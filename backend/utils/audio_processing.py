import asyncio
import numpy as np
import librosa
import soundfile as sf
from typing import Tuple, Optional
import logging

class AudioProcessor:
    """Audio processing utilities for VAD service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file and return normalized float32 data
        
        Returns:
            Tuple of (audio_data, sample_rate)
        """
        try:
            # Use librosa for robust audio loading
            audio_data, sample_rate = librosa.load(
                audio_path, 
                sr=None,  # Keep original sample rate
                mono=True,  # Convert to mono
                dtype=np.float32
            )
            
            # Normalize audio to [-1, 1] range
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            self.logger.info(f"Loaded audio: {len(audio_data)/sample_rate:.2f}s at {sample_rate}Hz")
            return audio_data, sample_rate
            
        except Exception as e:
            self.logger.error(f"Failed to load audio {audio_path}: {e}")
            raise
    
    async def resample_audio(
        self, 
        audio_data: np.ndarray, 
        original_rate: int, 
        target_rate: int
    ) -> np.ndarray:
        """Resample audio to target sample rate"""
        if original_rate == target_rate:
            return audio_data
        
        try:
            resampled = librosa.resample(
                audio_data, 
                orig_sr=original_rate, 
                target_sr=target_rate,
                res_type='kaiser_fast'  # Good quality, fast
            )
            
            self.logger.info(f"Resampled audio: {original_rate}Hz -> {target_rate}Hz")
            return resampled
            
        except Exception as e:
            self.logger.error(f"Audio resampling failed: {e}")
            raise
    
    def apply_noise_reduction(self, audio_data: np.ndarray) -> np.ndarray:
        """Apply basic noise reduction (optional enhancement)"""
        try:
            # Simple noise reduction using spectral gating
            # This is a placeholder - could be enhanced with more sophisticated algorithms
            
            # Apply mild high-pass filter to remove low-frequency noise
            from scipy import signal
            sos = signal.butter(4, 80, 'hp', fs=16000, output='sos')
            filtered = signal.sosfilt(sos, audio_data)
            
            return filtered.astype(np.float32)
            
        except Exception as e:
            self.logger.warning(f"Noise reduction failed, using original: {e}")
            return audio_data
