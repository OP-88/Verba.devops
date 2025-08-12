"""
Fixed Compatible VAD Service with NumPy 2.x Compatibility
Resolves dtype argument errors and Whisper integration issues
"""
import numpy as np
import webrtcvad
import logging
from typing import List, Dict, Any, Tuple
import time
import librosa

class AudioSegment:
    """Represents a detected voice segment with timing information"""
    def __init__(self, start_time: float, end_time: float, audio_data: np.ndarray = None):
        self.start_time = start_time
        self.end_time = end_time
        self.duration = end_time - start_time
        self.audio_data = audio_data
    
    def __repr__(self):
        return f"AudioSegment({self.start_time:.2f}-{self.end_time:.2f}s)"

class CompatibleVADService:
    """
    WebRTC VAD service with NumPy 2.x compatibility
    Fixed dtype parameter handling and array creation
    """
    
    def __init__(self, aggressiveness: int = 2, sample_rate: int = 16000):
        self.aggressiveness = aggressiveness
        self.sample_rate = sample_rate
        self.frame_duration_ms = 30  # WebRTC VAD supports 10, 20, 30ms
        self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)
        
        # Initialize WebRTC VAD
        self.vad = webrtcvad.Vad()
        self.vad.set_mode(aggressiveness)
        
        # Statistics tracking
        self.stats = {
            'total_frames_processed': 0,
            'voice_frames_detected': 0,
            'processing_time': 0.0
        }
        
        logging.info(f"Compatible VAD Service initialized with aggressiveness {aggressiveness}")
    
    def preprocess_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Load and preprocess audio with proper NumPy 2.x compatibility
        """
        try:
            # Load audio using librosa with explicit parameters
            audio_data, sr = librosa.load(
                audio_path, 
                sr=self.sample_rate,
                mono=True,
                dtype=np.float32  # Explicit dtype as keyword
            )
            
            # Ensure audio is in correct format for WebRTC VAD
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize to [-1, 1] range
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            return audio_data, sr
            
        except Exception as e:
            logging.error(f"Audio preprocessing failed: {e}")
            raise
    
    def audio_to_pcm16(self, audio_data: np.ndarray) -> bytes:
        """
        Convert float32 audio to PCM16 format required by WebRTC VAD
        Fixed NumPy array creation
        """
        try:
            # Ensure audio is float32
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Scale to int16 range and convert
            # Use explicit dtype as keyword argument to avoid position error
            pcm16_data = (audio_data * 32767).astype(dtype=np.int16)
            
            return pcm16_data.tobytes()
            
        except Exception as e:
            logging.error(f"PCM16 conversion failed: {e}")
            raise
    
    def detect_voice_segments(self, audio_data: np.ndarray) -> List[AudioSegment]:
        """
        Detect voice segments in audio data with improved error handling
        """
        start_time = time.time()
        segments = []
        
        try:
            # Convert to PCM16 format
            pcm_data = self.audio_to_pcm16(audio_data)
            
            # Process audio in frames
            frame_offset = 0
            voice_frames = []
            current_segment_start = None
            
            while frame_offset + self.frame_size <= len(audio_data):
                # Extract frame
                frame_data = audio_data[frame_offset:frame_offset + self.frame_size]
                
                # Convert frame to PCM16
                frame_pcm = self.audio_to_pcm16(frame_data)
                
                # Check if frame contains voice
                is_voice = self.vad.is_speech(frame_pcm, self.sample_rate)
                
                # Calculate timestamp
                timestamp = frame_offset / self.sample_rate
                
                # Track voice activity
                self.stats['total_frames_processed'] += 1
                if is_voice:
                    self.stats['voice_frames_detected'] += 1
                    voice_frames.append(timestamp)
                    
                    if current_segment_start is None:
                        current_segment_start = timestamp
                else:
                    # End of voice segment
                    if current_segment_start is not None:
                        segment_end = timestamp
                        if segment_end - current_segment_start > 0.1:  # Minimum 100ms
                            # Extract audio for this segment
                            start_idx = int(current_segment_start * self.sample_rate)
                            end_idx = int(segment_end * self.sample_rate)
                            segment_audio = audio_data[start_idx:end_idx]
                            
                            segments.append(AudioSegment(
                                current_segment_start, 
                                segment_end,
                                segment_audio
                            ))
                        current_segment_start = None
                
                frame_offset += self.frame_size
            
            # Handle final segment if it ends with voice
            if current_segment_start is not None:
                final_timestamp = len(audio_data) / self.sample_rate
                if final_timestamp - current_segment_start > 0.1:
                    start_idx = int(current_segment_start * self.sample_rate)
                    segment_audio = audio_data[start_idx:]
                    
                    segments.append(AudioSegment(
                        current_segment_start, 
                        final_timestamp,
                        segment_audio
                    ))
            
            # Update processing time
            self.stats['processing_time'] = time.time() - start_time
            
            return segments
            
        except Exception as e:
            logging.error(f"Voice detection failed: {e}")
            return []
    
    def process_audio_file(self, audio_path: str) -> Dict[str, Any]:
        """
        Main processing method that returns VAD results
        """
        try:
            # Preprocess audio
            audio_data, sample_rate = self.preprocess_audio(audio_path)
            
            # Detect voice segments
            segments = self.detect_voice_segments(audio_data)
            
            # Calculate statistics
            total_duration = len(audio_data) / sample_rate
            voice_duration = sum(seg.duration for seg in segments)
            speech_ratio = (voice_duration / total_duration) * 100 if total_duration > 0 else 0
            
            result = {
                'success': True,
                'segments': segments,
                'total_duration': total_duration,
                'voice_duration': voice_duration,
                'speech_ratio': speech_ratio,
                'num_segments': len(segments),
                'processing_time': self.stats['processing_time']
            }
            
            return result
            
        except Exception as e:
            logging.error(f"Audio processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'segments': []
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Return processing statistics"""
        return self.stats.copy()

def create_test_audio(filename: str = "test_audio.wav", duration: float = 5.0, sample_rate: int = 16000):
    """
    Create test audio file with voice-like patterns
    Fixed NumPy array creation for compatibility
    """
    try:
        # Create time array - use explicit dtype keyword
        t = np.linspace(0, duration, int(duration * sample_rate), dtype=np.float32)
        
        # Create audio with voice-like segments
        audio = np.zeros_like(t, dtype=np.float32)
        
        # Add voice segments (sine waves at speech frequencies)
        # Segment 1: 1-2 seconds
        voice_mask1 = (t >= 1.0) & (t <= 2.0)
        audio[voice_mask1] = 0.3 * np.sin(2 * np.pi * 150 * t[voice_mask1])
        
        # Segment 2: 3-4 seconds  
        voice_mask2 = (t >= 3.0) & (t <= 4.0)
        audio[voice_mask2] = 0.3 * np.sin(2 * np.pi * 200 * t[voice_mask2])
        
        # Add some noise
        noise = 0.05 * np.random.randn(len(audio)).astype(np.float32)
        audio += noise
        
        # Save as WAV file
        import soundfile as sf
        sf.write(filename, audio, sample_rate)
        
        return filename, len(audio) / sample_rate
        
    except Exception as e:
        logging.error(f"Test audio creation failed: {e}")
        raise

def test_compatible_vad():
    """Test the compatible VAD service"""
    print("🧪 Testing Compatible VAD Service")
    print("=" * 40)
    
    try:
        # Initialize VAD service
        vad = CompatibleVADService(aggressiveness=2)
        print("✅ VAD service initialized")
        
        # Create test audio
        test_file, duration = create_test_audio("vad_test_audio.wav", 5.0)
        print(f"📊 Test audio: {duration}s")
        
        # Process audio
        result = vad.process_audio_file(test_file)
        
        if result['success']:
            print("✅ VAD processing successful")
            print(f"📊 Voice segments: {result['num_segments']}")
            print(f"🗣️ Speech ratio: {result['speech_ratio']:.1f}%")
            print(f"⏱️ Processing time: {result['processing_time']:.3f}s")
            
            # Show segment details
            for i, segment in enumerate(result['segments'], 1):
                print(f"   Segment {i}: {segment.start_time:.2f}-{segment.end_time:.2f}s ({segment.duration:.2f}s)")
            
            # Show stats
            stats = vad.get_stats()
            print(f"📈 Stats: {stats['total_frames_processed']} frames, {stats['voice_frames_detected']} voice")
            
            # Cleanup
            import os
            if os.path.exists(test_file):
                os.remove(test_file)
                
        else:
            print(f"❌ VAD processing failed: {result.get('error', 'Unknown error')}")
        
        print("🎉 Compatible VAD test completed")
        return result['success']
        
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the VAD service
    success = test_compatible_vad()
    if success:
        print("\n✅ VAD service is working correctly!")
    else:
        print("\n❌ VAD service needs further debugging")
