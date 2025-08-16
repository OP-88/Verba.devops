#!/usr/bin/env python3
"""
OpenRouter AI Assistant Integration for Verba
Connects to free OpenRouter models for AI chatbot functionality
"""

import os
import requests
import json
from typing import Dict, List, Optional, Any, Generator
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterAIAssistant:
    """AI Assistant powered by OpenRouter free models"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter AI Assistant
        
        Args:
            api_key: OpenRouter API key (or set OPENROUTER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key required. Set OPENROUTER_API_KEY or pass api_key parameter")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.current_model = "mistralai/mistral-7b-instruct:free"  # Default free model
        self.conversation_history = []
        self.session_context = {}
        
        # Available free models
        self.free_models = {
            "mistral-7b": "mistralai/mistral-7b-instruct:free",
            "mixtral-8x7b": "mistralai/mixtral-8x7b-instruct:free", 
            "llama-3-8b": "meta-llama/llama-3-8b-instruct:free",
            "gemma-7b": "google/gemma-7b-it:free"
        }
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test OpenRouter API connection"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://verba.local",
                "X-Title": "Verba AI Assistant"
            }
            
            # Simple test call
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ OpenRouter API connection successful")
                return True
            else:
                logger.error(f"❌ OpenRouter API connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ OpenRouter connection test failed: {e}")
            return False
    
    def set_model(self, model_name: str) -> bool:
        """
        Set the AI model to use
        
        Args:
            model_name: Model name from free_models dict or full model path
        """
        if model_name in self.free_models:
            self.current_model = self.free_models[model_name]
            logger.info(f"Model set to: {model_name} ({self.current_model})")
            return True
        elif model_name.startswith("mistralai/") or model_name.startswith("meta-llama/") or model_name.startswith("google/"):
            self.current_model = model_name
            logger.info(f"Model set to: {model_name}")
            return True
        else:
            logger.error(f"Unknown model: {model_name}. Available: {list(self.free_models.keys())}")
            return False
    
    def add_transcription_context(self, transcription_text: str, meeting_title: str = "Meeting"):
        """Add transcription context for AI assistant"""
        self.session_context = {
            "transcription": transcription_text,
            "meeting_title": meeting_title,
            "timestamp": time.time()
        }
        logger.info(f"Added transcription context: {meeting_title} ({len(transcription_text)} chars)")
    
    def chat(self, message: str, use_context: bool = True) -> str:
        """
        Send a chat message to the AI assistant
        
        Args:
            message: User message
            use_context: Whether to include transcription context
        
        Returns:
            AI response text
        """
        try:
            # Build conversation messages
            messages = []
            
            # Add system message with context
            if use_context and self.session_context.get('transcription'):
                system_message = f"""You are an AI assistant helping with meeting analysis and transcription insights.

Current meeting context:
Title: {self.session_context.get('meeting_title', 'Meeting')}
Transcription: {self.session_context['transcription'][:2000]}...

Please provide helpful, concise responses about the meeting content, action items, key points, or any questions the user might have."""
                
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append({
                    "role": "system", 
                    "content": "You are a helpful AI assistant for the Verba transcription application. Provide clear, concise, and helpful responses."
                })
            
            # Add conversation history (last 4 messages to stay within token limits)
            messages.extend(self.conversation_history[-4:])
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Prepare request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://verba.local",
                "X-Title": "Verba AI Assistant"
            }
            
            payload = {
                "model": self.current_model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
            
            # Make request
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content'].strip()
                
                # Add to conversation history
                self.conversation_history.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": ai_response}
                ])
                
                # Keep history manageable
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
                
                return ai_response
            else:
                error_msg = f"API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return f"Sorry, I'm having trouble connecting right now. {error_msg}"
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
    
    def chat_stream(self, message: str, use_context: bool = True) -> Generator[str, None, None]:
        """
        Stream chat response for real-time UI updates
        
        Args:
            message: User message
            use_context: Whether to include transcription context
        
        Yields:
            Chunks of AI response text
        """
        try:
            # Build messages (same as chat method)
            messages = []
            
            # Add system message with context
            if use_context and self.session_context.get('transcription'):
                system_message = f"""You are an AI assistant helping with meeting analysis and transcription insights.

Current meeting context:
Title: {self.session_context.get('meeting_title', 'Meeting')}
Transcription: {self.session_context['transcription'][:2000]}...

Please provide helpful, concise responses about the meeting content, action items, key points, or any questions the user might have."""
                
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append({
                    "role": "system", 
                    "content": "You are a helpful AI assistant for the Verba transcription application. Provide clear, concise, and helpful responses."
                })
            
            # Add conversation history
            messages.extend(self.conversation_history[-4:])
            messages.append({"role": "user", "content": message})
            
            # Prepare streaming request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://verba.local",
                "X-Title": "Verba AI Assistant"
            }
            
            payload = {
                "model": self.current_model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.7,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
                stream=True
            )
            
            if response.status_code == 200:
                full_response = ""
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            line = line[6:]  # Remove 'data: '
                            
                            if line == '[DONE]':
                                break
                            
                            try:
                                chunk_data = json.loads(line)
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        full_response += content
                                        yield content
                            except json.JSONDecodeError:
                                continue
                
                # Add to conversation history
                self.conversation_history.extend([
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": full_response}
                ])
                
                if len(self.conversation_history) > 10:
                    self.conversation_history = self.conversation_history[-10:]
            
            else:
                yield f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            yield f"Stream error: {str(e)}"
    
    def analyze_transcription(self, transcription_text: str, analysis_type: str = "summary") -> str:
        """
        Analyze transcription with specific prompts
        
        Args:
            transcription_text: Full transcription text
            analysis_type: Type of analysis (summary, action_items, key_points, questions)
        
        Returns:
            Analysis result
        """
        analysis_prompts = {
            "summary": "Please provide a concise summary of this meeting/transcription:",
            "action_items": "Extract all action items, tasks, and next steps mentioned in this transcription:",
            "key_points": "Identify the main topics, decisions, and key points discussed:",
            "questions": "What questions were raised or need follow-up based on this content:",
            "participants": "Who are the participants or speakers mentioned in this transcription:",
            "decisions": "What decisions were made during this meeting/discussion:"
        }
        
        if analysis_type not in analysis_prompts:
            return f"Unknown analysis type. Available: {list(analysis_prompts.keys())}"
        
        prompt = f"{analysis_prompts[analysis_type]}\n\nTranscription:\n{transcription_text[:3000]}..."
        
        return self.chat(prompt, use_context=False)
    
    def get_suggested_questions(self, transcription_text: str) -> List[str]:
        """Generate suggested questions based on transcription"""
        prompt = f"""Based on this meeting transcription, suggest 5 helpful follow-up questions someone might want to ask:

Transcription: {transcription_text[:2000]}...

Format your response as a numbered list of questions."""
        
        response = self.chat(prompt, use_context=False)
        
        # Extract questions from response
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Clean up the question
                question = line.split('.', 1)[-1].strip()
                if question and question.endswith('?'):
                    questions.append(question)
        
        return questions[:5]  # Return max 5 questions
    
    def clear_conversation(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def clear_context(self):
        """Clear transcription context"""
        self.session_context = {}
        logger.info("Session context cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current assistant status"""
        return {
            "model": self.current_model,
            "conversation_length": len(self.conversation_history),
            "has_context": bool(self.session_context.get('transcription')),
            "context_title": self.session_context.get('meeting_title'),
            "available_models": list(self.free_models.keys())
        }

# FastAPI Integration
def setup_ai_assistant_routes(app, assistant: OpenRouterAIAssistant):
    """Setup FastAPI routes for AI assistant"""
    
    @app.post("/api/ai/chat")
    async def ai_chat(request: dict):
        """AI chat endpoint"""
        message = request.get("message")
        use_context = request.get("use_context", True)
        
        if not message:
            return {"success": False, "error": "Message required"}
        
        try:
            response = assistant.chat(message, use_context)
            return {
                "success": True,
                "response": response,
                "model": assistant.current_model
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/ai/analyze")
    async def ai_analyze(request: dict):
        """AI transcription analysis endpoint"""
        transcription_text = request.get("transcription_text")
        analysis_type = request.get("analysis_type", "summary")
        
        if not transcription_text:
            return {"success": False, "error": "Transcription text required"}
        
        try:
            analysis = assistant.analyze_transcription(transcription_text, analysis_type)
            suggestions = assistant.get_suggested_questions(transcription_text)
            
            return {
                "success": True,
                "analysis": analysis,
                "suggested_questions": suggestions,
                "analysis_type": analysis_type
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.post("/api/ai/context")
    async def set_ai_context(request: dict):
        """Set transcription context for AI"""
        transcription_text = request.get("transcription_text")
        meeting_title = request.get("meeting_title", "Meeting")
        
        if not transcription_text:
            return {"success": False, "error": "Transcription text required"}
        
        try:
            assistant.add_transcription_context(transcription_text, meeting_title)
            return {
                "success": True,
                "message": f"Context set for: {meeting_title}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/ai/status")
    async def ai_status():
        """Get AI assistant status"""
        try:
            status = assistant.get_status()
            return {"success": True, "status": status}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Testing Functions
def test_openrouter_assistant():
    """Test OpenRouter AI Assistant functionality"""
    print("🤖 Testing OpenRouter AI Assistant...")
    
    # Initialize
    try:
        assistant = OpenRouterAIAssistant()
        print("✅ AI Assistant initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Test basic chat
    try:
        response = assistant.chat("Hello! Can you help me analyze meeting notes?")
        print(f"✅ Chat test successful: {response[:100]}...")
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
    
    # Test with context
    try:
        sample_transcription = """
        Meeting started at 2:00 PM.
        John: We need to review the quarterly budget.
        Sarah: I'll prepare the expense report by Friday.
        Mike: The marketing campaign needs approval by next week.
        John: Let's schedule a follow-up meeting for Monday.
        """
        
        assistant.add_transcription_context(sample_transcription, "Budget Review Meeting")
        
        response = assistant.chat("What are the main action items from this meeting?")
        print(f"✅ Context chat successful: {response[:100]}...")
    except Exception as e:
        print(f"❌ Context chat failed: {e}")
    
    # Test analysis
    try:
        analysis = assistant.analyze_transcription(sample_transcription, "action_items")
        print(f"✅ Analysis successful: {analysis[:100]}...")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
    
    # Test suggested questions
    try:
        questions = assistant.get_suggested_questions(sample_transcription)
        print(f"✅ Suggested questions: {len(questions)} generated")
        for i, q in enumerate(questions, 1):
            print(f"   {i}. {q}")
    except Exception as e:
        print(f"❌ Suggested questions failed: {e}")
    
    print("🎉 AI Assistant testing complete!")

if __name__ == "__main__":
    test_openrouter_assistant()
