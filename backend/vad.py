#!/usr/bin/env python3
"""
Voice Activity Detection (VAD) Service for Verba
Proprietary VAD filter implementation with fallback to WebRTC VAD
"""

import numpy as np
import librosa
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def vad_filter(audio_data: np.ndarray, sr: int = 16000) -> np.ndarray:
    """
    Proprietary VAD filter implementation placeholder.
    
    This function should implement advanced voice activity detection
    to filter out silence and noise from audio data.
    
    Args:
        audio_data: Audio samples as numpy array
        sr: Sample rate in Hz
        
    Returns:
        Filtered audio data with silence removed
        
    TODO: Replace with actual proprietary VAD implementation
    """
    # Placeholder implementation - replace with proprietary algorithm
    logger.info(f"🎙️ Applying VAD filter to {len(audio_data)} samples at {sr}Hz")
    
    # Basic energy-based VAD as placeholder
    frame_length = int(0.025 * sr)  # 25ms frames
    hop_length = int(0.010 * sr)    # 10ms hop
    
    # Compute RMS energy
    rms = librosa.feature.rms(
        y=audio_data, 
        frame_length=frame_length, 
        hop_length=hop_length
    )[0]
    
    # Simple threshold-based VAD
    threshold = np.percentile(rms, 30)  # Bottom 30% as silence
    
    # Create voice activity mask
    voice_frames = rms > threshold
    
    # Apply some smoothing to avoid choppy results
    kernel_size = 5
    voice_frames = np.convolve(voice_frames, np.ones(kernel_size)/kernel_size, mode='same') > 0.5
    
    # Convert frame-based mask to sample-based
    voice_mask = np.repeat(voice_frames, hop_length)
    voice_mask = voice_mask[:len(audio_data)]
    
    # Apply mask to audio
    filtered_audio = audio_data * voice_mask
    
    # Remove leading/trailing silence
    non_zero_indices = np.nonzero(filtered_audio)[0]
    if len(non_zero_indices) > 0:
        start_idx = non_zero_indices[0]
        end_idx = non_zero_indices[-1]
        filtered_audio = filtered_audio[start_idx:end_idx+1]
    
    logger.info(f"✅ VAD filter applied: {len(audio_data)} -> {len(filtered_audio)} samples ({(len(filtered_audio)/len(audio_data)*100):.1f}%)")
    
    return filtered_audio


class EnhancedVADService:
    """Enhanced VAD service with multiple detection methods"""
    
    def __init__(self):
        self.fallback_available = False
        try:
            import webrtcvad
            self.webrtc_vad = webrtcvad.Vad(2)  # Moderate aggressiveness
            self.fallback_available = True
            logger.info("✅ WebRTC VAD fallback available")
        except ImportError:
            logger.warning("⚠️ WebRTC VAD not available")
    
    def detect_voice_activity(
        self, 
        audio_data: np.ndarray, 
        sr: int = 16000,
        return_segments: bool = True
    ) -> List[Tuple[float, float]]:
        """
        Detect voice activity segments in audio.
        
        Args:
            audio_data: Audio samples
            sr: Sample rate
            return_segments: Return time segments vs binary mask
            
        Returns:
            List of (start_time, end_time) tuples for voice segments
        """
        try:
            # Use proprietary VAD filter first
            filtered_audio = vad_filter(audio_data, sr)
            
            if not return_segments:
                return filtered_audio
            
            # Detect segments in filtered audio
            segments = self._detect_segments(filtered_audio, sr)
            logger.info(f"🎯 Detected {len(segments)} voice segments")
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ VAD detection failed: {e}")
            if self.fallback_available:
                return self._webrtc_fallback(audio_data, sr, return_segments)
            else:
                # Return entire audio as one segment
                return [(0.0, len(audio_data) / sr)]
    
    def _detect_segments(
        self, 
        audio_data: np.ndarray, 
        sr: int
    ) -> List[Tuple[float, float]]:
        """Detect continuous voice segments"""
        if len(audio_data) == 0:
            return []
        
        # Simple threshold-based segmentation
        frame_length = int(0.025 * sr)
        hop_length = int(0.010 * sr)
        
        rms = librosa.feature.rms(
            y=audio_data,
            frame_length=frame_length,
            hop_length=hop_length
        )[0]
        
        threshold = np.percentile(rms, 20)
        voice_frames = rms > threshold
        
        # Find segment boundaries
        segments = []
        start_frame = None
        
        for i, is_voice in enumerate(voice_frames):
            if is_voice and start_frame is None:
                start_frame = i
            elif not is_voice and start_frame is not None:
                start_time = start_frame * hop_length / sr
                end_time = i * hop_length / sr
                if end_time - start_time > 0.5:  # Minimum 0.5s segments
                    segments.append((start_time, end_time))
                start_frame = None
        
        # Handle case where audio ends with voice
        if start_frame is not None:
            start_time = start_frame * hop_length / sr
            end_time = len(audio_data) / sr
            segments.append((start_time, end_time))
        
        # Merge close segments
        merged_segments = []
        for start, end in segments:
            if merged_segments and start - merged_segments[-1][1] < 1.0:
                merged_segments[-1] = (merged_segments[-1][0], end)
            else:
                merged_segments.append((start, end))
        
        return merged_segments
    
    def _webrtc_fallback(
        self, 
        audio_data: np.ndarray, 
        sr: int,
        return_segments: bool = True
    ) -> List[Tuple[float, float]]:
        """Fallback to WebRTC VAD"""
        logger.info("🔄 Using WebRTC VAD fallback")
        
        try:
            # Convert to 16-bit PCM
            audio_int16 = (audio_data * 32768).astype(np.int16)
            
            frame_duration = 30  # ms
            frame_size = int(sr * frame_duration / 1000)
            
            segments = []
            current_start = None
            
            for i in range(0, len(audio_int16) - frame_size, frame_size):
                frame = audio_int16[i:i + frame_size].tobytes()
                
                try:
                    is_speech = self.webrtc_vad.is_speech(frame, sr)
                    timestamp = i / sr
                    
                    if is_speech and current_start is None:
                        current_start = timestamp
                    elif not is_speech and current_start is not None:
                        segments.append((current_start, timestamp))
                        current_start = None
                except:
                    continue
            
            # Handle case where audio ends with speech
            if current_start is not None:
                segments.append((current_start, len(audio_int16) / sr))
            
            # Filter short segments and merge close ones
            filtered_segments = []
            for start, end in segments:
                if end - start >= 0.5:  # Minimum 0.5s
                    if filtered_segments and start - filtered_segments[-1][1] < 1.0:
                        filtered_segments[-1] = (filtered_segments[-1][0], end)
                    else:
                        filtered_segments.append((start, end))
            
            return filtered_segments
            
        except Exception as e:
            logger.error(f"❌ WebRTC VAD fallback failed: {e}")
            return [(0.0, len(audio_data) / sr)]


# Convenience functions for backward compatibility
def enhance_audio_with_vad(audio_path: str, sr: int = 16000) -> np.ndarray:
    """Load and enhance audio file with VAD filtering"""
    try:
        audio_data, _ = librosa.load(audio_path, sr=sr)
        return vad_filter(audio_data, sr)
    except Exception as e:
        logger.error(f"❌ Audio enhancement failed: {e}")
        audio_data, _ = librosa.load(audio_path, sr=sr)
        return audio_data


def detect_speech_segments(audio_path: str, sr: int = 16000) -> List[Tuple[float, float]]:
    """Detect speech segments in audio file"""
    try:
        audio_data, _ = librosa.load(audio_path, sr=sr)
        vad_service = EnhancedVADService()
        return vad_service.detect_voice_activity(audio_data, sr)
    except Exception as e:
        logger.error(f"❌ Speech segment detection failed: {e}")
        return [(0.0, librosa.get_duration(filename=audio_path))]