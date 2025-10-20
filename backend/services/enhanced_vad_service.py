#!/usr/bin/env python3
"""
Enhanced Voice Activity Detection (VAD) Service for Verba
Integrates Silero VAD for superior noise reduction and speech detection
"""

import os
import logging
import numpy as np
import torch
import librosa
from typing import List, Tuple, Optional, Dict, Any
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

class EnhancedVADService:
    """
    Enhanced Voice Activity Detection using Silero VAD
    Provides superior noise reduction and speech detection compared to basic VAD
    """
    
    def __init__(self, 
                 model_name: str = 'silero_vad',
                 repo_or_dir: str = 'snakers4/silero-vad',
                 sample_rate: int = 16000,
                 chunk_size: int = 512):
        """
        Initialize Enhanced VAD Service with Silero VAD
        
        Args:
            model_name: Silero VAD model name
            repo_or_dir: GitHub repo or local directory
            sample_rate: Audio sample rate (16kHz recommended)
            chunk_size: Audio chunk size for processing
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.model = None
        self.fallback_available = False
        
        # Initialize Silero VAD
        self._load_silero_vad(model_name, repo_or_dir)
        
        # Initialize fallback VAD if needed
        self._initialize_fallback_vad()
        
        logger.info(f"✅ Enhanced VAD Service initialized (Silero: {'✅' if self.model else '❌'}, Fallback: {'✅' if self.fallback_available else '❌'})")
    
    def _load_silero_vad(self, model_name: str, repo_or_dir: str):
        """Load Silero VAD model"""
        try:
            # Load Silero VAD model
            self.model, self.utils = torch.hub.load(
                repo_or_dir=repo_or_dir,
                model=model_name,
                force_reload=False,
                onnx=False,
                verbose=False
            )
            
            # Extract utility functions
            (self.get_speech_timestamps, 
             self.save_audio, 
             self.read_audio, 
             self.VADIterator, 
             self.collect_chunks) = self.utils
            
            logger.info("✅ Silero VAD model loaded successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load Silero VAD: {e}")
            self.model = None
    
    def _initialize_fallback_vad(self):
        """Initialize fallback WebRTC VAD"""
        try:
            import webrtcvad
            self.webrtc_vad = webrtcvad.Vad(2)  # Moderate aggressiveness
            self.fallback_available = True
            logger.info("✅ Fallback WebRTC VAD initialized")
        except ImportError:
            logger.warning("⚠️ WebRTC VAD not available as fallback")
            self.fallback_available = False
    
    def detect_speech_segments(self, 
                             audio: np.ndarray, 
                             return_seconds: bool = True,
                             min_speech_duration_ms: int = 250,
                             max_speech_duration_s: int = float('inf'),
                             min_silence_duration_ms: int = 100,
                             window_size_samples: int = 1024,
                             speech_pad_ms: int = 30) -> List[Tuple[float, float]]:
        """
        Detect speech segments in audio using Silero VAD
        
        Args:
            audio: Audio array (16kHz mono)
            return_seconds: Return timestamps in seconds (vs samples)
            min_speech_duration_ms: Minimum speech duration to keep
            max_speech_duration_s: Maximum speech duration before splitting
            min_silence_duration_ms: Minimum silence between segments
            window_size_samples: Window size for VAD processing
            speech_pad_ms: Padding around speech segments
            
        Returns:
            List of (start_time, end_time) tuples for speech segments
        """
        if self.model is None:
            return self._fallback_speech_detection(audio, return_seconds)
        
        try:
            # Ensure audio is float32 and normalized
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Normalize audio to [-1, 1] range
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / np.max(np.abs(audio))
            
            # Convert to PyTorch tensor
            wav_tensor = torch.from_numpy(audio)
            
            # Get speech timestamps using Silero VAD
            speech_timestamps = self.get_speech_timestamps(
                wav_tensor,
                self.model,
                sampling_rate=self.sample_rate,
                return_seconds=return_seconds,
                min_speech_duration_ms=min_speech_duration_ms,
                max_speech_duration_s=max_speech_duration_s,
                min_silence_duration_ms=min_silence_duration_ms,
                window_size_samples=window_size_samples,
                speech_pad_ms=speech_pad_ms
            )
            
            # Convert to list of tuples
            segments = [(ts['start'], ts['end']) for ts in speech_timestamps]
            
            logger.info(f"🎙️ Silero VAD detected {len(segments)} speech segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Silero VAD failed: {e}")
            return self._fallback_speech_detection(audio, return_seconds)
    
    def _fallback_speech_detection(self, 
                                 audio: np.ndarray, 
                                 return_seconds: bool = True) -> List[Tuple[float, float]]:
        """Fallback speech detection using WebRTC VAD"""
        if not self.fallback_available:
            logger.warning("⚠️ No VAD available, returning full audio as speech")
            duration = len(audio) / self.sample_rate if return_seconds else len(audio)
            return [(0.0, duration)]
        
        try:
            # Convert to int16 for WebRTC VAD
            audio_int16 = (audio * 32768).astype(np.int16)
            
            frame_duration = 30  # ms
            frame_size = int(self.sample_rate * frame_duration / 1000)
            
            voiced_segments = []
            current_segment_start = None
            
            for i in range(0, len(audio_int16) - frame_size, frame_size):
                frame = audio_int16[i:i + frame_size].tobytes()
                
                try:
                    is_speech = self.webrtc_vad.is_speech(frame, self.sample_rate)
                    timestamp = i / self.sample_rate if return_seconds else i
                    
                    if is_speech and current_segment_start is None:
                        current_segment_start = timestamp
                    elif not is_speech and current_segment_start is not None:
                        voiced_segments.append((current_segment_start, timestamp))
                        current_segment_start = None
                except Exception:
                    continue
            
            # Handle case where audio ends with speech
            if current_segment_start is not None:
                end_time = len(audio_int16) / self.sample_rate if return_seconds else len(audio_int16)
                voiced_segments.append((current_segment_start, end_time))
            
            # Merge close segments and filter short ones
            merged_segments = []
            min_duration = 0.5  # Minimum 0.5 seconds
            merge_gap = 1.0     # Merge if gap < 1 second
            
            for start, end in voiced_segments:
                if end - start >= min_duration:
                    if merged_segments and start - merged_segments[-1][1] < merge_gap:
                        merged_segments[-1] = (merged_segments[-1][0], end)
                    else:
                        merged_segments.append((start, end))
            
            logger.info(f"🎙️ WebRTC VAD detected {len(merged_segments)} speech segments")
            return merged_segments
            
        except Exception as e:
            logger.error(f"❌ Fallback VAD failed: {e}")
            duration = len(audio) / self.sample_rate if return_seconds else len(audio)
            return [(0.0, duration)]
    
    def preprocess_audio_for_vad(self, 
                               audio_data: np.ndarray, 
                               original_sr: int = None) -> np.ndarray:
        """
        Preprocess audio for optimal VAD performance
        
        Args:
            audio_data: Raw audio data
            original_sr: Original sample rate
            
        Returns:
            Preprocessed audio at 16kHz mono
        """
        try:
            # Convert to float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Resample to 16kHz if needed
            if original_sr and original_sr != self.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=self.sample_rate)
            
            # Convert to mono if stereo
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=0)
            
            # Normalize audio
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Apply basic noise reduction (simple high-pass filter)
            audio_data = self._apply_noise_reduction(audio_data)
            
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ Audio preprocessing failed: {e}")
            return audio_data
    
    def _apply_noise_reduction(self, audio: np.ndarray, cutoff_freq: int = 80) -> np.ndarray:
        """Apply basic noise reduction with high-pass filter"""
        try:
            from scipy import signal
            
            # High-pass filter to remove low-frequency noise
            nyquist = self.sample_rate / 2
            normal_cutoff = cutoff_freq / nyquist
            b, a = signal.butter(4, normal_cutoff, btype='high', analog=False)
            filtered_audio = signal.filtfilt(b, a, audio)
            
            return filtered_audio
            
        except Exception:
            # Return original audio if filtering fails
            return audio
    
    def get_vad_confidence(self, audio_chunk: np.ndarray) -> float:
        """
        Get VAD confidence score for an audio chunk
        
        Args:
            audio_chunk: Audio chunk to analyze
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if self.model is None:
            return 0.5  # Neutral confidence for fallback
        
        try:
            # Ensure proper format
            if audio_chunk.dtype != np.float32:
                audio_chunk = audio_chunk.astype(np.float32)
            
            # Normalize
            if np.max(np.abs(audio_chunk)) > 0:
                audio_chunk = audio_chunk / np.max(np.abs(audio_chunk))
            
            wav_tensor = torch.from_numpy(audio_chunk)
            
            # Get speech probability using Silero model
            with torch.no_grad():
                speech_prob = self.model(wav_tensor, self.sample_rate).item()
            
            return max(0.0, min(1.0, speech_prob))
            
        except Exception as e:
            logger.error(f"❌ VAD confidence calculation failed: {e}")
            return 0.5
    
    def filter_audio_by_speech(self, 
                             audio: np.ndarray, 
                             speech_segments: List[Tuple[float, float]],
                             padding_ms: int = 100) -> np.ndarray:
        """
        Filter audio to keep only speech segments with padding
        
        Args:
            audio: Original audio array
            speech_segments: List of (start, end) speech segments in seconds
            padding_ms: Padding around speech segments in milliseconds
            
        Returns:
            Filtered audio containing only speech segments
        """
        if not speech_segments:
            return np.array([], dtype=np.float32)
        
        try:
            padding_samples = int(padding_ms * self.sample_rate / 1000)
            filtered_chunks = []
            
            for start_time, end_time in speech_segments:
                start_sample = max(0, int(start_time * self.sample_rate) - padding_samples)
                end_sample = min(len(audio), int(end_time * self.sample_rate) + padding_samples)
                
                chunk = audio[start_sample:end_sample]
                if len(chunk) > 0:
                    filtered_chunks.append(chunk)
            
            # Concatenate all speech chunks
            if filtered_chunks:
                return np.concatenate(filtered_chunks)
            else:
                return np.array([], dtype=np.float32)
                
        except Exception as e:
            logger.error(f"❌ Audio filtering failed: {e}")
            return audio
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the VAD service"""
        return {
            "silero_vad_available": self.model is not None,
            "fallback_vad_available": self.fallback_available,
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size,
            "status": "✅ Enhanced VAD Ready" if self.model else "⚠️ Using Fallback VAD"
        }


def create_enhanced_vad_service() -> EnhancedVADService:
    """Factory function to create enhanced VAD service"""
    try:
        return EnhancedVADService()
    except Exception as e:
        logger.error(f"❌ Failed to create Enhanced VAD Service: {e}")
        raise