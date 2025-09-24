"""
Compatible VAD Service Wrapper
Wraps your existing VAD service to provide the expected interface
"""
import numpy as np
import webrtcvad
import logging
from typing import List, Dict, Any, Tuple
import time

logger = logging.getLogger(__name__)

class CompatibleVADService:
    """
    Compatible VAD Service that provides the interface expected by Enhanced Transcription Service
    """
    
    def __init__(self, aggressiveness: int = 2):
        """
        Initialize VAD service
        Args:
            aggressiveness: VAD aggressiveness level (0-3)
        """
        self.aggressiveness = aggressiveness
        self.vad = webrtcvad.Vad(aggressiveness)
        self.frame_duration_ms = 30  # 30ms frames
        self.sample_rate = 16000
        
        # Statistics tracking
        self.stats = {
            'total_frames_processed': 0,
            'voice_frames_detected': 0,
            'total_audio_duration': 0.0,
            'total_processing_time': 0.0,
            'segments_created': 0
        }
        
        logger.info(f"Compatible VAD Service initialized with aggressiveness {aggressiveness}")
    
    def _frame_generator(self, audio: np.ndarray, sample_rate: int):
        """Generate audio frames for VAD processing"""
        frame_length = int(sample_rate * self.frame_duration_ms / 1000.0)
        offset = 0
        
        while offset + frame_length <= len(audio):
            frame = audio[offset:offset + frame_length]
            # Convert to int16 for WebRTC VAD - FIXED numpy syntax
            frame_int16 = np.clip(frame * 32767, -32768, 32767).astype(np.int16)
            yield frame_int16.tobytes(), offset / sample_rate
            offset += frame_length
    
    def _merge_adjacent_segments(self, segments: List[Tuple[float, float]], 
                               max_gap: float = 0.3) -> List[Tuple[float, float]]:
        """Merge segments that are close together"""
        if not segments:
            return []
        
        merged = [segments[0]]
        
        for start, end in segments[1:]:
            last_start, last_end = merged[-1]
            # If segments are close, merge them
            if start - last_end <= max_gap:
                merged[-1] = (last_start, end)
            else:
                merged.append((start, end))
        
        return merged
    
    def process_audio(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        """
        Process audio and detect voice segments
        Args:
            audio: Audio data as numpy array
            sample_rate: Sample rate of audio
        Returns:
            Dictionary with voice segments and metadata
        """
        start_time = time.time()
        
        try:
            # Ensure audio is the right sample rate
            if sample_rate != self.sample_rate:
                import librosa
                audio = librosa.resample(audio, orig_sr=sample_rate, target_sr=self.sample_rate)
                sample_rate = self.sample_rate
            
            # Ensure audio is float32
            audio = audio.astype(np.float32)
            
            # Process frames through VAD
            voice_frames = []
            total_frames = 0

            for frame_bytes, frame_time in self._frame_generator(audio, sample_rate):
                total_frames += 1

                # Check if frame contains speech
                is_speech = self.vad.is_speech(frame_bytes, sample_rate)

                if is_speech:
                    voice_frames.append(frame_time)
                    self.stats['voice_frames_detected'] += 1

            self.stats['total_frames_processed'] += total_frames

            # Convert voice frames to segments
            voice_segments = []
            if voice_frames:
                # Group consecutive voice frames into segments
                segments = []
                current_start = voice_frames[0]
                current_end = voice_frames[0] + self.frame_duration_ms / 1000.0

                for frame_time in voice_frames[1:]:
                    # If frame is adjacent to current segment, extend it
                    if frame_time - current_end <= self.frame_duration_ms / 1000.0 * 1.5:
                        current_end = frame_time + self.frame_duration_ms / 1000.0
                    else:
                        # Start new segment
                        segments.append((current_start, current_end))
                        current_start = frame_time
                        current_end = frame_time + self.frame_duration_ms / 1000.0

                # Add the last segment
                segments.append((current_start, current_end))

                # Merge adjacent segments
                segments = self._merge_adjacent_segments(segments)

                # Convert to the expected format
                for start, end in segments:
                    duration = end - start
                    if duration >= 0.5:  # Minimum segment duration
                        voice_segments.append({
                            'start': start,
                            'end': end,
                            'duration': duration,
                            'confidence': 0.8  # WebRTC VAD doesn't provide confidence, use fixed value
                        })
                        self.stats['segments_created'] += 1

            # Update statistics
            processing_time = time.time() - start_time
            audio_duration = len(audio) / sample_rate

            self.stats['total_audio_duration'] += audio_duration
            self.stats['total_processing_time'] += processing_time

            # Calculate speech ratio
            total_speech_duration = sum(seg['duration'] for seg in voice_segments)
            speech_ratio = total_speech_duration / audio_duration if audio_duration > 0 else 0

            logger.info(f"VAD processed {audio_duration:.2f}s audio in {processing_time:.3f}s")
            logger.info(f"Found {len(voice_segments)} voice segments ({speech_ratio:.1%} speech)")

            return {
                'success': True,
                'voice_segments': voice_segments,
                'total_duration': audio_duration,
                'speech_duration': total_speech_duration,
                'speech_ratio': speech_ratio,
                'processing_time': processing_time,
                'frames_processed': total_frames,
                'voice_frames': len(voice_frames)
            }

        except Exception as e:
            logger.error(f"VAD processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'voice_segments': [],
                'total_duration': len(audio) / sample_rate if len(audio) > 0 else 0,
                'speech_duration': 0,
                'speech_ratio': 0,
                'processing_time': time.time() - start_time
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get VAD processing statistics"""
        voice_ratio = (
            self.stats['voice_frames_detected'] / self.stats['total_frames_processed']
            if self.stats['total_frames_processed'] > 0 else 0
        )

        avg_processing_speed = (
            self.stats['total_audio_duration'] / self.stats['total_processing_time']
            if self.stats['total_processing_time'] > 0 else 0
        )
        
        return {
            **self.stats,
            'voice_frame_ratio': voice_ratio,
            'average_processing_speed': avg_processing_speed,
            'aggressiveness': self.aggressiveness
        }
    
    def reset_stats(self):
        """Reset all statistics"""
        self.stats = {
            'total_frames_processed': 0,
            'voice_frames_detected': 0,
            'total_audio_duration': 0.0,
            'total_processing_time': 0.0,
            'segments_created': 0
        }
        logger.info("VAD statistics reset")

# Compatibility alias
VADService = CompatibleVADService

# Test the service
if __name__ == "__main__":
    def test_compatible_vad():
        """Test the compatible VAD service"""
        print("🧪 Testing Compatible VAD Service")
        print("=" * 40)
        
        # Initialize service
        vad = CompatibleVADService(aggressiveness=2)
        print("✅ VAD service initialized")
        
        # Create test audio
        sample_rate = 16000
        duration = 5.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create speech-like audio
        audio = np.zeros_like(t)
        
        # Add speech segments
        for start in [1, 3]:
            segment_start = int(start * sample_rate)
            segment_end = int((start + 1) * sample_rate)
            if segment_end <= len(audio):
                segment_t = t[segment_start:segment_end]
                speech = 0.3 * np.sin(2 * np.pi * 400 * segment_t)
                audio[segment_start:segment_end] = speech
        
        # Add noise
        audio += 0.02 * np.random.randn(len(audio))
        audio = audio.astype(np.float32)
        
        print(f"📊 Test audio: {duration}s")
        
        # Process with VAD
        result = vad.process_audio(audio, sample_rate)
        
        if result['success']:
            print(f"✅ VAD processing successful")
            print(f"📊 Voice segments: {len(result['voice_segments'])}")
            print(f"🗣️ Speech ratio: {result['speech_ratio']:.1%}")
            print(f"⏱️ Processing time: {result['processing_time']:.3f}s")
            
            # Show segments
            for i, seg in enumerate(result['voice_segments']):
                print(f"   Segment {i+1}: {seg['start']:.2f}-{seg['end']:.2f}s ({seg['duration']:.2f}s)")
            
            # Show stats
            stats = vad.get_stats()
            print(f"📈 Stats: {stats['total_frames_processed']} frames, {stats['voice_frames_detected']} voice")
        else:
            print(f"❌ VAD processing failed: {result.get('error', 'Unknown error')}")
        
        print("🎉 Compatible VAD test completed")
    
    test_compatible_vad()
