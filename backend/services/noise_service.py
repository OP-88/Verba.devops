"""
RNNoise-based audio denoising service for Verba AI
Provides noise reduction capabilities for cleaner transcription input
"""

import numpy as np
import torch
import torchaudio
import librosa
from typing import Optional, Tuple
from loguru import logger

class RNNoiseService:
    """
    RNNoise-based audio denoising service
    
    Note: This is a simplified implementation. For production,
    consider using actual RNNoise bindings or similar libraries.
    """
    
    def __init__(self):
        self.sample_rate = 16000
        self.frame_size = 480  # 30ms at 16kHz
        self.initialized = False
        
        try:
            # Initialize basic spectral subtraction for noise reduction
            self.hop_length = 512
            self.n_fft = 2048
            self.initialized = True
            logger.info("✅ Noise reduction service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Noise reduction service failed to initialize: {e}")
            self.initialized = False
    
    def filter(self, audio_data: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Apply noise reduction to audio data
        
        Args:
            audio_data: Input audio signal
            sample_rate: Sample rate of the audio
            
        Returns:
            Denoised audio signal
        """
        if not self.initialized:
            logger.warning("Noise reduction not available, returning original audio")
            return audio_data
        
        try:
            # Resample to 16kHz if needed
            if sample_rate != self.sample_rate:
                audio_data = librosa.resample(
                    audio_data, 
                    orig_sr=sample_rate, 
                    target_sr=self.sample_rate
                )
            
            # Apply spectral subtraction for noise reduction
            denoised = self._spectral_subtraction(audio_data)
            
            logger.debug(f"Applied noise reduction to {len(audio_data)/self.sample_rate:.2f}s audio")
            return denoised
            
        except Exception as e:
            logger.error(f"❌ Noise reduction failed: {e}")
            return audio_data
    
    def _spectral_subtraction(self, audio: np.ndarray, alpha: float = 2.0, beta: float = 0.001) -> np.ndarray:
        """
        Apply spectral subtraction for noise reduction
        
        Args:
            audio: Input audio signal
            alpha: Over-subtraction factor
            beta: Spectral floor factor
            
        Returns:
            Denoised audio signal
        """
        # Compute STFT
        stft = librosa.stft(
            audio, 
            n_fft=self.n_fft, 
            hop_length=self.hop_length, 
            window='hann'
        )
        
        magnitude = np.abs(stft)
        phase = np.angle(stft)
        
        # Estimate noise from first few frames (assuming initial silence/noise)
        noise_frames = min(10, magnitude.shape[1] // 4)
        noise_magnitude = np.mean(magnitude[:, :noise_frames], axis=1, keepdims=True)
        
        # Apply spectral subtraction
        enhanced_magnitude = magnitude - alpha * noise_magnitude
        
        # Apply spectral floor
        enhanced_magnitude = np.maximum(
            enhanced_magnitude, 
            beta * magnitude
        )
        
        # Reconstruct STFT
        enhanced_stft = enhanced_magnitude * np.exp(1j * phase)
        
        # Convert back to time domain
        enhanced_audio = librosa.istft(
            enhanced_stft, 
            hop_length=self.hop_length, 
            window='hann'
        )
        
        return enhanced_audio
    
    def preprocess_for_transcription(
        self, 
        audio_data: np.ndarray, 
        sample_rate: int = 16000
    ) -> Tuple[np.ndarray, int]:
        """
        Preprocess audio for optimal transcription quality
        
        Args:
            audio_data: Input audio signal
            sample_rate: Sample rate of the audio
            
        Returns:
            Tuple of (processed_audio, target_sample_rate)
        """
        try:
            # Apply noise reduction
            denoised = self.filter(audio_data, sample_rate)
            
            # Normalize audio
            if np.max(np.abs(denoised)) > 0:
                denoised = denoised / np.max(np.abs(denoised)) * 0.95
            
            # Apply gentle high-pass filter to remove low-frequency noise
            denoised = self._high_pass_filter(denoised, cutoff=80)
            
            return denoised, self.sample_rate
            
        except Exception as e:
            logger.error(f"❌ Audio preprocessing failed: {e}")
            return audio_data, sample_rate
    
    def _high_pass_filter(self, audio: np.ndarray, cutoff: float = 80) -> np.ndarray:
        """Apply high-pass filter to remove low-frequency noise"""
        try:
            from scipy import signal
            
            # Design high-pass filter
            nyquist = self.sample_rate / 2
            normal_cutoff = cutoff / nyquist
            b, a = signal.butter(4, normal_cutoff, btype='high', analog=False)
            
            # Apply filter
            filtered = signal.filtfilt(b, a, audio)
            return filtered
            
        except ImportError:
            logger.warning("scipy not available for high-pass filtering")
            return audio
        except Exception as e:
            logger.error(f"High-pass filtering failed: {e}")
            return audio

# Global instance
rnnoise_service = RNNoiseService()