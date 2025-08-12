#!/usr/bin/env python3
"""Whisper transcription service for Verba"""

import whisper
import torch
import numpy as np
import asyncio
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class WhisperService:
    def __init__(self, model_size: str = "tiny", device: str = "auto"):
        """
        Initialize Whisper service
        
        Args:
            model_size: "tiny", "base", "small", "medium", "large"
            device: "auto", "cpu", "cuda"
        """
        self.model_size = model_size
        self.device = self._get_device(device)
        self.model = None
        self.is_loaded = False
        
        # Model directory for caching
        self.model_dir = Path("./models")
        self.model_dir.mkdir(exist_ok=True)
        
        logger.info(f"WhisperService initialized - Model: {model_size}, Device: {self.device}")
    
    def _get_device(self, device: str) -> str:
        """Determine the best device to use"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    async def load_model(self) -> bool:
        """Load the Whisper model asynchronously"""
        if self.is_loaded:
            return True
            
        try:
            logger.info(f"Loading Whisper {self.model_size} model...")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                lambda: whisper.load_model(
                    self.model_size,
                    device=self.device,
                    download_root=str(self.model_dir)
                )
            )
            
            self.is_loaded = True
            logger.info(f"✅ Whisper model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            return False
    
    async def transcribe_audio(
        self, 
        audio_data: Union[np.ndarray, str, Path], 
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> Dict[str, Any]:
        """
        Transcribe audio data
        
        Args:
            audio_data: Audio array, file path, or file-like object
            language: Language code (None for auto-detection)
            task: "transcribe" or "translate"
            
        Returns:
            Dict with transcription results
        """
        if not self.is_loaded:
            await self.load_model()
        
        try:
            logger.info("Starting transcription...")
            
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.model.transcribe(
                    audio_data,
                    language=language,
                    task=task,
                    fp16=False,  # Better compatibility
                    verbose=False
                )
            )
            
            # Process results
            transcription_result = {
                "text": result["text"].strip(),
                "language": result["language"],
                "segments": [
                    {
                        "start": seg["start"],
                        "end": seg["end"], 
                        "text": seg["text"].strip()
                    }
                    for seg in result["segments"]
                ],
                "duration": max([seg["end"] for seg in result["segments"]]) if result["segments"] else 0
            }
            
            logger.info(f"✅ Transcription completed - {len(result['segments'])} segments")
            return transcription_result
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise Exception(f"Whisper transcription error: {str(e)}")
    
    async def transcribe_file(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Transcribe audio file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        logger.info(f"Transcribing file: {file_path.name}")
        return await self.transcribe_audio(str(file_path))
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "model_size": self.model_size,
            "device": self.device,
            "is_loaded": self.is_loaded,
            "model_path": str(self.model_dir)
        }
    
    async def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            del self.model
            self.model = None
            self.is_loaded = False
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            logger.info("Model unloaded and memory cleared")

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
