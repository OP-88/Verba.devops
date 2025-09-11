"""
AI Summarization Service using Transformers
Provides offline text summarization and key points extraction
"""

import logging
import re
from typing import Dict, List, Any, Optional
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for text summarization and analysis"""
    
    def __init__(self, model_name: str = "t5-small"):
        self.model_name = model_name
        self.summarizer = None
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.max_length = 512
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the summarization model"""
        try:
            logger.info(f"📝 Loading summarization model: {self.model_name}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            
            # Move to device
            if torch.cuda.is_available():
                self.model.to(torch.device("cuda"))
            
            # Create pipeline
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            self.is_initialized = True
            logger.info(f"✅ Summarization model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize summarization model: {e}")
            self.is_initialized = False
    
    def summarize_transcript(self, text: str, max_length: int = 150, min_length: int = 50) -> Dict[str, Any]:
        """
        Generate summary of transcript text
        
        Args:
            text: Input transcript text
            max_length: Maximum summary length
            min_length: Minimum summary length
            
        Returns:
            Dictionary with summary and metadata
        """
        if not self.is_initialized:
            return self._fallback_summary(text)
        
        try:
            logger.info("📝 Generating transcript summary...")
            
            # Clean and prepare text
            cleaned_text = self._preprocess_text(text)
            
            if len(cleaned_text.split()) < 10:
                return {
                    'summary': cleaned_text,
                    'key_points': [cleaned_text],
                    'action_items': [],
                    'sentiment': 'neutral',
                    'word_count': len(cleaned_text.split()),
                    'compression_ratio': 1.0
                }
            
            # Split long text into chunks if needed
            chunks = self._split_text_into_chunks(cleaned_text)
            summaries = []
            
            for chunk in chunks:
                try:
                    # Generate summary for chunk
                    chunk_summary = self.summarizer(
                        chunk,
                        max_length=min(max_length, len(chunk.split()) // 2),
                        min_length=min(min_length, len(chunk.split()) // 4),
                        do_sample=False,
                        temperature=0.7,
                        num_beams=4
                    )[0]['summary_text']
                    
                    summaries.append(chunk_summary)
                    
                except Exception as e:
                    logger.warning(f"Failed to summarize chunk: {e}")
                    # Use first few sentences as fallback
                    sentences = chunk.split('.')[:3]
                    summaries.append('. '.join(sentences) + '.')
            
            # Combine summaries
            final_summary = ' '.join(summaries)
            
            # Extract additional insights
            key_points = self._extract_key_points(cleaned_text)
            action_items = self._extract_action_items(cleaned_text)
            sentiment = self._analyze_sentiment(cleaned_text)
            
            result = {
                'summary': final_summary,
                'key_points': key_points,
                'action_items': action_items,
                'sentiment': sentiment,
                'word_count': len(cleaned_text.split()),
                'compression_ratio': len(final_summary.split()) / len(cleaned_text.split())
            }
            
            logger.info(f"✅ Summary generated: {len(final_summary)} chars, {len(key_points)} key points")
            return result
            
        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            return self._fallback_summary(text)
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for summarization"""
        # Remove speaker labels for summarization
        text = re.sub(r'Speaker \d+:\s*', '', text)
        
        # Clean up multiple spaces and newlines
        text = re.sub(r'\s+', ' ', text)
        
        # Remove filler words and vocal sounds
        fillers = ['um', 'uh', 'er', 'ah', 'like', 'you know', 'I mean']
        for filler in fillers:
            text = re.sub(rf'\b{filler}\b', '', text, flags=re.IGNORECASE)
        
        # Clean up punctuation
        text = re.sub(r'\s+([,.!?])', r'\1', text)
        
        return text.strip()
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 400) -> List[str]:
        """Split text into chunks for processing"""
        words = text.split()
        
        if len(words) <= max_chunk_size:
            return [text]
        
        chunks = []
        current_chunk = []
        
        for word in words:
            current_chunk.append(word)
            
            if len(current_chunk) >= max_chunk_size:
                # Try to end at sentence boundary
                chunk_text = ' '.join(current_chunk)
                last_period = chunk_text.rfind('.')
                
                if last_period > len(chunk_text) * 0.7:  # If period is in last 30%
                    chunks.append(chunk_text[:last_period + 1])
                    remaining = chunk_text[last_period + 1:].strip()
                    current_chunk = remaining.split() if remaining else []
                else:
                    chunks.append(chunk_text)
                    current_chunk = []
        
        # Add remaining words
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text"""
        try:
            # Simple extraction based on sentence importance
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            # Score sentences by length and keyword presence
            important_keywords = [
                'decided', 'agreed', 'important', 'action', 'todo', 'deadline',
                'meeting', 'project', 'budget', 'timeline', 'responsible',
                'next steps', 'follow up', 'deliverable'
            ]
            
            scored_sentences = []
            for sentence in sentences:
                score = len(sentence.split())  # Base score on length
                
                # Boost score for important keywords
                for keyword in important_keywords:
                    if keyword.lower() in sentence.lower():
                        score += 10
                
                scored_sentences.append((sentence, score))
            
            # Sort by score and take top sentences
            scored_sentences.sort(key=lambda x: x[1], reverse=True)
            key_points = [s[0] + '.' for s in scored_sentences[:5] if s[1] > 5]
            
            return key_points[:3] if len(key_points) > 3 else key_points
            
        except Exception as e:
            logger.warning(f"Key point extraction failed: {e}")
            return []
    
    def _extract_action_items(self, text: str) -> List[str]:
        """Extract action items from text"""
        try:
            action_patterns = [
                r'(?:will|should|need to|must|have to|going to)\s+([^.]+)',
                r'(?:action item|todo|task|assignment):\s*([^.]+)',
                r'(?:by|before|until)\s+\w+day\s+([^.]+)',
                r'(?:responsible for|assigned to|owner)\s*:\s*([^.]+)'
            ]
            
            action_items = []
            for pattern in action_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    action = match.group(1).strip()
                    if len(action) > 5 and action not in action_items:
                        action_items.append(action)
            
            return action_items[:5]  # Limit to top 5 action items
            
        except Exception as e:
            logger.warning(f"Action item extraction failed: {e}")
            return []
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis"""
        try:
            positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'achieve', 'agree']
            negative_words = ['bad', 'terrible', 'problem', 'issue', 'concern', 'difficult', 'challenge']
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return 'positive'
            elif negative_count > positive_count:
                return 'negative'
            else:
                return 'neutral'
                
        except Exception:
            return 'neutral'
    
    def _fallback_summary(self, text: str) -> Dict[str, Any]:
        """Fallback summary when model is not available"""
        try:
            # Simple extractive summary - take first and key sentences
            sentences = text.split('.')
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
            
            if len(sentences) <= 3:
                summary = text
            else:
                # Take first sentence and a few important ones
                summary_sentences = [sentences[0]]
                
                # Add sentences with important keywords
                for sentence in sentences[1:]:
                    if any(keyword in sentence.lower() for keyword in ['important', 'decided', 'action', 'next']):
                        summary_sentences.append(sentence)
                        if len(summary_sentences) >= 3:
                            break
                
                summary = '. '.join(summary_sentences) + '.'
            
            return {
                'summary': summary,
                'key_points': self._extract_key_points(text),
                'action_items': self._extract_action_items(text),
                'sentiment': self._analyze_sentiment(text),
                'word_count': len(text.split()),
                'compression_ratio': len(summary.split()) / len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Fallback summary failed: {e}")
            return {
                'summary': text[:200] + '...' if len(text) > 200 else text,
                'key_points': [],
                'action_items': [],
                'sentiment': 'neutral',
                'word_count': len(text.split()),
                'compression_ratio': 1.0
            }
    
    def cleanup(self):
        """Clean up resources"""
        if self.model and torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("🧹 Summarization service cleaned up")