#!/usr/bin/env python3
"""
Audio Preprocessing Utilities for Enhanced VAD
Optimized for Silero VAD and improved noise reduction
"""

import os
import logging
import numpy as np
import librosa
from typing import Tuple, Optional, Dict, Any
from scipy import signal
import warnings

warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

class AudioPreprocessor:
    """
    Audio preprocessing utilities optimized for VAD and transcription
    Includes noise reduction, normalization, and format conversion
    """
    
    def __init__(self, target_sr: int = 16000, normalize_audio: bool = True):
        """
        Initialize Audio Preprocessor
        
        Args:
            target_sr: Target sample rate for processing
            normalize_audio: Whether to normalize audio levels
        """
        self.target_sr = target_sr
        self.normalize_audio = normalize_audio
        logger.info(f"✅ Audio Preprocessor initialized (SR: {target_sr}Hz, Normalize: {normalize_audio})")
    
    def load_and_preprocess_audio(self, 
                                audio_path: str, 
                                apply_noise_reduction: bool = True) -> Tuple[np.ndarray, int]:
        """
        Load and preprocess audio file for optimal VAD and transcription
        
        Args:
            audio_path: Path to audio file
            apply_noise_reduction: Whether to apply noise reduction
            
        Returns:
            Tuple of (preprocessed_audio_array, sample_rate)
        """
        try:
            # Load audio with librosa (handles multiple formats)
            audio, sr = librosa.load(
                audio_path, 
                sr=self.target_sr,  # Resample to target rate
                mono=True,          # Convert to mono
                dtype=np.float32    # Use float32 for better precision
            )
            
            logger.info(f"📁 Loaded audio: {os.path.basename(audio_path)} "
                       f"({len(audio)/sr:.2f}s, {sr}Hz)")
            
            # Apply preprocessing
            audio = self.preprocess_audio_array(audio, sr, apply_noise_reduction)
            
            return audio, sr
            
        except Exception as e:
            logger.error(f"❌ Failed to load audio {audio_path}: {e}")
            raise
    
    def preprocess_audio_array(self, 
                             audio: np.ndarray, 
                             sr: int,
                             apply_noise_reduction: bool = True) -> np.ndarray:
        """
        Preprocess audio array for optimal VAD performance
        
        Args:
            audio: Audio array
            sr: Sample rate
            apply_noise_reduction: Whether to apply noise reduction
            
        Returns:
            Preprocessed audio array
        """
        try:
            # Ensure float32 format
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Handle stereo to mono conversion
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=0)
            
            # Remove DC offset
            audio = self._remove_dc_offset(audio)
            
            # Apply noise reduction if requested
            if apply_noise_reduction:
                audio = self._apply_noise_reduction(audio, sr)
            
            # Normalize audio levels
            if self.normalize_audio:
                audio = self._normalize_audio(audio)
            
            # Apply soft limiting to prevent clipping
            audio = self._soft_limit(audio)
            
            logger.info(f"🔧 Audio preprocessed: "
                       f"Duration={len(audio)/sr:.2f}s, "
                       f"Level={np.abs(audio).mean():.3f}, "
                       f"Peak={np.abs(audio).max():.3f}")
            
            return audio
            
        except Exception as e:
            logger.error(f"❌ Audio preprocessing failed: {e}")
            return audio
    
    def _remove_dc_offset(self, audio: np.ndarray) -> np.ndarray:
        """Remove DC offset from audio"""
        return audio - np.mean(audio)
    
    def _apply_noise_reduction(self, audio: np.ndarray, sr: int) -> np.ndarray:
        """
        Apply comprehensive noise reduction
        
        Args:
            audio: Audio array
            sr: Sample rate
            
        Returns:
            Noise-reduced audio
        """
        try:
            # 1. High-pass filter to remove low-frequency noise (rumble, hum)
            audio = self._high_pass_filter(audio, sr, cutoff=80)
            
            # 2. Spectral subtraction for broadband noise reduction
            audio = self._spectral_subtraction(audio, sr)
            
            # 3. Median filter for impulse noise removal
            audio = self._median_filter(audio)
            
            return audio
            
        except Exception as e:
            logger.warning(f"⚠️ Noise reduction failed: {e}")
            return audio
    
    def _high_pass_filter(self, audio: np.ndarray, sr: int, cutoff: int = 80) -> np.ndarray:
        """Apply high-pass filter to remove low-frequency noise"""
        try:
            nyquist = sr / 2
            normal_cutoff = cutoff / nyquist
            b, a = signal.butter(4, normal_cutoff, btype='high', analog=False)
            return signal.filtfilt(b, a, audio)
        except Exception:
            return audio
    
    def _spectral_subtraction(self, audio: np.ndarray, sr: int, alpha: float = 2.0) -> np.ndarray:
        """
        Simple spectral subtraction for noise reduction
        
        Args:
            audio: Audio signal
            sr: Sample rate
            alpha: Over-subtraction factor
            
        Returns:
            Noise-reduced audio
        """
        try:
            # Estimate noise from first 0.5 seconds
            noise_duration = min(int(0.5 * sr), len(audio) // 4)
            noise_sample = audio[:noise_duration]
            
            # Compute noise spectrum
            noise_fft = np.fft.rfft(noise_sample)
            noise_magnitude = np.abs(noise_fft)
            noise_power = noise_magnitude ** 2
            
            # Process audio in overlapping frames
            frame_size = 1024
            hop_size = frame_size // 2
            enhanced_audio = np.zeros_like(audio)
            
            for i in range(0, len(audio) - frame_size, hop_size):
                frame = audio[i:i + frame_size]
                
                # Apply window
                windowed_frame = frame * np.hanning(len(frame))
                
                # FFT
                frame_fft = np.fft.rfft(windowed_frame, n=len(noise_sample))
                frame_magnitude = np.abs(frame_fft)
                frame_phase = np.angle(frame_fft)
                frame_power = frame_magnitude ** 2
                
                # Spectral subtraction
                enhanced_power = frame_power - alpha * noise_power[:len(frame_power)]
                enhanced_power = np.maximum(enhanced_power, 0.1 * frame_power)
                
                # Reconstruct signal
                enhanced_magnitude = np.sqrt(enhanced_power)
                enhanced_fft = enhanced_magnitude * np.exp(1j * frame_phase)
                enhanced_frame = np.fft.irfft(enhanced_fft, n=frame_size)
                
                # Overlap-add
                enhanced_audio[i:i + frame_size] += enhanced_frame * np.hanning(frame_size)
            
            return enhanced_audio
            
        except Exception as e:
            logger.warning(f"⚠️ Spectral subtraction failed: {e}")
            return audio
    
    def _median_filter(self, audio: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """Apply median filter to remove impulse noise"""
        try:
            from scipy.ndimage import median_filter
            return median_filter(audio, size=kernel_size)
        except Exception:
            return audio
    
    def _normalize_audio(self, audio: np.ndarray, target_level: float = 0.7) -> np.ndarray:
        """
        Normalize audio to target level
        
        Args:
            audio: Audio array
            target_level: Target RMS level (0-1)
            
        Returns:
            Normalized audio
        """
        try:
            # Calculate RMS level
            rms = np.sqrt(np.mean(audio ** 2))
            
            if rms > 0:
                # Normalize to target level
                normalization_factor = target_level / rms
                audio = audio * normalization_factor
            
            return audio
            
        except Exception as e:
            logger.warning(f"⚠️ Audio normalization failed: {e}")
            return audio
    
    def _soft_limit(self, audio: np.ndarray, threshold: float = 0.95) -> np.ndarray:
        """
        Apply soft limiting to prevent clipping
        
        Args:
            audio: Audio array
            threshold: Soft limiting threshold
            
        Returns:
            Soft-limited audio
        """
        try:
            # Tanh soft limiting
            return np.tanh(audio / threshold) * threshold
        except Exception:
            return audio
    
    def detect_audio_properties(self, audio: np.ndarray, sr: int) -> Dict[str, Any]:
        """
        Analyze audio properties for processing optimization
        
        Args:
            audio: Audio array
            sr: Sample rate
            
        Returns:
            Dictionary of audio properties
        """
        try:
            duration = len(audio) / sr
            rms_level = np.sqrt(np.mean(audio ** 2))
            peak_level = np.max(np.abs(audio))
            zero_crossing_rate = np.mean(librosa.feature.zero_crossing_rate(audio))
            
            # Estimate noise level from quietest segments
            audio_db = librosa.amplitude_to_db(np.abs(audio) + 1e-8)
            noise_floor = np.percentile(audio_db, 10)
            
            # Spectral properties
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
            spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=audio, sr=sr))
            
            return {
                "duration_seconds": duration,
                "rms_level": float(rms_level),
                "peak_level": float(peak_level),
                "zero_crossing_rate": float(zero_crossing_rate),
                "noise_floor_db": float(noise_floor),
                "spectral_centroid": float(spectral_centroid),
                "spectral_bandwidth": float(spectral_bandwidth),
                "is_low_quality": rms_level < 0.01 or noise_floor > -20,
                "has_clipping": peak_level > 0.99
            }
            
        except Exception as e:
            logger.error(f"❌ Audio analysis failed: {e}")
            return {"error": str(e)}
    
    def chunk_audio_for_processing(self, 
                                 audio: np.ndarray, 
                                 sr: int,
                                 chunk_duration: float = 30.0,
                                 overlap_duration: float = 1.0) -> list:
        """
        Split audio into overlapping chunks for processing
        
        Args:
            audio: Audio array
            sr: Sample rate
            chunk_duration: Duration of each chunk in seconds
            overlap_duration: Overlap between chunks in seconds
            
        Returns:
            List of (chunk_audio, start_time, end_time) tuples
        """
        try:
            chunk_size = int(chunk_duration * sr)
            overlap_size = int(overlap_duration * sr)
            hop_size = chunk_size - overlap_size
            
            chunks = []
            
            for i in range(0, len(audio), hop_size):
                chunk_end = min(i + chunk_size, len(audio))
                chunk = audio[i:chunk_end]
                
                start_time = i / sr
                end_time = chunk_end / sr
                
                # Only include chunks with minimum duration
                if len(chunk) >= sr:  # At least 1 second
                    chunks.append((chunk, start_time, end_time))
                
                if chunk_end >= len(audio):
                    break
            
            logger.info(f"📊 Created {len(chunks)} audio chunks "
                       f"({chunk_duration}s chunks, {overlap_duration}s overlap)")
            
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Audio chunking failed: {e}")
            return [(audio, 0.0, len(audio) / sr)]


def create_audio_preprocessor(target_sr: int = 16000) -> AudioPreprocessor:
    """Factory function to create audio preprocessor"""
    return AudioPreprocessor(target_sr=target_sr)


# Utility functions for common audio operations
def load_audio_for_vad(audio_path: str, target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """Convenience function to load audio optimized for VAD"""
    preprocessor = create_audio_preprocessor(target_sr)
    return preprocessor.load_and_preprocess_audio(audio_path)


def preprocess_uploaded_audio(audio_data: bytes, 
                            original_filename: str = "audio",
                            target_sr: int = 16000) -> Tuple[np.ndarray, int]:
    """
    Preprocess uploaded audio data
    
    Args:
        audio_data: Raw audio bytes
        original_filename: Original filename for format detection
        target_sr: Target sample rate
        
    Returns:
        Tuple of (preprocessed_audio, sample_rate)
    """
    import tempfile
    
    try:
        # Save bytes to temporary file
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(original_filename)[1], 
                                       delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_path = temp_file.name
        
        try:
            # Load and preprocess
            preprocessor = create_audio_preprocessor(target_sr)
            audio, sr = preprocessor.load_and_preprocess_audio(temp_path)
            return audio, sr
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"❌ Failed to preprocess uploaded audio: {e}")
        raise