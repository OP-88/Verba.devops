"""
Verba Whisper AI Service
OpenAI Whisper integration for speech-to-text transcription.
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import tempfile
import os

import whisper
import torch
import numpy as np
from pydantic import BaseModel

from config.settings import settings

logger = logging.getLogger(__name__)

class WhisperService:
    """Service for handling Whisper AI transcription operations."""
    
    def __init__(self):
        self.model = None
        self.model_info = {}
        self.start_time = time.time()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize Whisper model with error handling."""
        try:
            model_size = settings.whisper_model_size
            logger.info(f"Loading Whisper model '{model_size}' on device '{self.device}'...")
            
            start_time = time.time()
            
            # Load model in thread to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, 
                self._load_model, 
                model_size
            )
            
            load_time = time.time() - start_time
            
            # Store model information
            self.model_info = {
                "size": model_size,
                "device": self.device,
                "load_time": load_time,
                "languages": self._get_supported_languages(),
                "parameters": self._estimate_parameters(model_size)
            }
            
            self.is_initialized = True
            logger.info(f"✅ Whisper model loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise RuntimeError(f"Whisper initialization failed: {e}")
    
    def _load_model(self, model_size: str):
        """Load Whisper model synchronously."""
        return whisper.load_model(model_size, device=self.device)
    
    def _get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        if hasattr(whisper.tokenizer, 'LANGUAGES'):
            return list(whisper.tokenizer.LANGUAGES.keys())
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", 
            "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", 
            "el", "ms", "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr", 
            "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn", 
            "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne", 
            "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn", 
            "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", 
            "lo", "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", 
            "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]
    
    def _estimate_parameters(self, model_size: str) -> int:
        """Estimate model parameters based on size."""
        parameter_map = {
            "tiny": 39_000_000,
            "base": 74_000_000,
            "small": 244_000_000,
            "medium": 769_000_000,
            "large": 1_550_000_000
        }
        return parameter_map.get(model_size, 74_000_000)
    
    async def transcribe(self, audio_data: bytes, options: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Transcribe audio data using Whisper model.
        
        Args:
            audio_data: Raw audio bytes
            options: Additional transcription options
            
        Returns:
            Transcription result with text, confidence, language, segments
        """
        if not self.is_initialized or not self.model:
            raise RuntimeError("Whisper service not initialized")
        
        try:
            # Default options
            transcribe_options = {
                "language": None,  # Auto-detect
                "task": "transcribe",
                "verbose": False,
                "condition_on_previous_text": False,
                "temperature": 0.0,
                "compression_ratio_threshold": 2.4,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6
            }
            
            if options:
                transcribe_options.update(options)
            
            # Create temporary file for audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Run transcription in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self._transcribe_file,
                    temp_file_path,
                    transcribe_options
                )
                
                # Process and format result
                formatted_result = self._format_transcription_result(result)
                
                logger.info(f"Transcription completed: {len(formatted_result['text'])} characters")
                return formatted_result
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise RuntimeError(f"Transcription error: {e}")
    
    def _transcribe_file(self, file_path: str, options: Dict) -> Dict:
        """Transcribe file synchronously."""
        return self.model.transcribe(file_path, **options)
    
    def _format_transcription_result(self, result: Dict) -> Dict[str, Any]:
        """Format Whisper result into standardized response."""
        
        # Extract main text
        text = result.get("text", "").strip()
        
        # Calculate overall confidence from segments
        segments = result.get("segments", [])
        confidence = self._calculate_overall_confidence(segments)
        
        # Get detected language
        language = result.get("language", "unknown")
        
        # Calculate duration
        duration = 0.0
        if segments:
            duration = max(segment.get("end", 0) for segment in segments)
        
        # Format segments for API response
        formatted_segments = []
        for i, segment in enumerate(segments):
            formatted_segment = {
                "id": i,
                "start": segment.get("start", 0.0),
                "end": segment.get("end", 0.0),
                "text": segment.get("text", "").strip(),
                "confidence": segment.get("avg_logprob", 0.0),
                "tokens": segment.get("tokens", []),
                "temperature": segment.get("temperature", 0.0),
                "avg_logprob": segment.get("avg_logprob", 0.0),
                "compression_ratio": segment.get("compression_ratio", 0.0),
                "no_speech_prob": segment.get("no_speech_prob", 0.0)
            }
            formatted_segments.append(formatted_segment)
        
        return {
            "text": text,
            "confidence": confidence,
            "language": language,
            "duration": duration,
            "segments": formatted_segments,
            "word_count": len(text.split()) if text else 0,
            "character_count": len(text)
        }
    
    def _calculate_overall_confidence(self, segments: List[Dict]) -> float:
        """Calculate overall confidence score from segments."""
        if not segments:
            return 0.0
        
        # Use average log probability as confidence proxy
        total_logprob = 0.0
        total_duration = 0.0
        
        for segment in segments:
            duration = segment.get("end", 0) - segment.get("start", 0)
            logprob = segment.get("avg_logprob", -1.0)
            
            total_logprob += logprob * duration
            total_duration += duration
        
        if total_duration == 0:
            return 0.0
        
        avg_logprob = total_logprob / total_duration
        
        # Convert log probability to confidence score (0-1)
        # This is a heuristic conversion
        confidence = max(0.0, min(1.0, (avg_logprob + 1.0) / 1.0))
        return round(confidence, 3)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        return self.model_info.copy()
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self.start_time
    
    def is_ready(self) -> bool:
        """Check if service is ready for transcription."""
        return self.is_initialized and self.model is not None
    
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up Whisper service...")
        if self.model:
            del self.model
            self.model = None
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.is_initialized = False
        logger.info("✅ Whisper service cleanup complete")

# Test the service
async def test_whisper_service():
    """Test function for the Whisper service"""
    service = WhisperService(model_size="tiny")
    
    # Test model loading
    success = await service.load_model()
    if success:
        print("✅ Whisper service test passed")
        
        # Get model info
        info = service.get_model_info()
        print(f"Model info: {info}")
        
        # Clean up
        await service.unload_model()
    else:
        print("❌ Whisper service test failed")

if __name__ == "__main__":
    # Run test
    asyncio.run(test_whisper_service())
