"""
Real-Time Audio Capture System for Verba Enhanced Transcription
Supports microphone input and system audio routing
"""
import os
import sys
import time
import queue
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
import logging
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass
from collections import deque
import tempfile

# Import your enhanced transcription service
try:
    from enhanced_transcription_service import EnhancedTranscriptionService, TranscriptionResult
    from vad_service import CompatibleVADService
except ImportError:
    print("⚠️ Enhanced services not found. Install them first.")

@dataclass
class AudioStreamConfig:
    """Configuration for audio streaming"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    buffer_seconds: float = 30.0  # Maximum buffer duration
    vad_chunk_seconds: float = 2.0  # VAD processing chunk size
    transcription_chunk_seconds: float = 10.0  # Transcription chunk size
    device: Optional[int] = None  # None = default device
    device_type: str = "microphone"  # "microphone" or "system"

class AudioBuffer:
    """Circular buffer for audio data with thread-safe operations"""
    
    def __init__(self, max_seconds: float, sample_rate: int):
        self.max_samples = int(max_seconds * sample_rate)
        self.sample_rate = sample_rate
        self.buffer = deque(maxlen=self.max_samples)
        self.timestamps = deque(maxlen=self.max_samples)
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def add_audio(self, audio_data: np.ndarray):
        """Add audio data to buffer"""
        current_time = time.time()
        
        with self.lock:
            # Add samples with timestamps
            for sample in audio_data.flatten():
                self.buffer.append(sample)
                self.timestamps.append(current_time)
                current_time += 1.0 / self.sample_rate
    
    def get_recent_audio(self, duration_seconds: float) -> np.ndarray:
        """Get most recent audio data"""
        num_samples = int(duration_seconds * self.sample_rate)
        
        with self.lock:
            if len(self.buffer) < num_samples:
                # Return all available data
                return np.array(list(self.buffer), dtype=np.float32)
            else:
                # Return most recent samples
                recent_samples = list(self.buffer)[-num_samples:]
                return np.array(recent_samples, dtype=np.float32)
    
    def get_buffer_duration(self) -> float:
        """Get current buffer duration in seconds"""
        with self.lock:
            return len(self.buffer) / self.sample_rate
    
    def clear_old_data(self, keep_seconds: float):
        """Remove old data, keeping only recent samples"""
        keep_samples = int(keep_seconds * self.sample_rate)
        
        with self.lock:
            if len(self.buffer) > keep_samples:
                # Remove old samples
                samples_to_remove = len(self.buffer) - keep_samples
                for _ in range(samples_to_remove):
                    if self.buffer:
                        self.buffer.popleft()
                        self.timestamps.popleft()

class RealTimeAudioCapture:
    """
    Real-time audio capture with transcription integration
    Supports both microphone and system audio
    """
    
    def __init__(self, 
                 config: AudioStreamConfig,
                 transcription_service: Optional[EnhancedTranscriptionService] = None,
                 transcription_callback: Optional[Callable] = None):
        
        self.config = config
        self.transcription_service = transcription_service
        self.transcription_callback = transcription_callback
        
        # Audio components
        self.audio_buffer = AudioBuffer(config.buffer_seconds, config.sample_rate)
        self.audio_queue = queue.Queue()
        self.stream = None
        self.is_recording = False
        
        # Processing threads
        self.processing_thread = None
        self.transcription_thread = None
        
        # Statistics
        self.stats = {
            'total_audio_processed': 0.0,
            'transcription_chunks': 0,
            'average_processing_time': 0.0,
            'last_transcription_time': 0.0
        }
        
        # Setup logging
        self.logger = logging.getLogger('real_time_audio_capture')
        
        # Validate audio devices
        self._validate_audio_setup()
    
    def _validate_audio_setup(self):
        """Validate audio device configuration"""
        try:
            # List available devices
            devices = sd.query_devices()
            self.logger.info(f"Found {len(devices)} audio devices")
            
            # Log available devices
            for i, device in enumerate(devices):
                device_type = "Input" if device['max_input_channels'] > 0 else "Output"
                self.logger.info(f"Device {i}: {device['name']} ({device_type})")
            
            # Validate selected device
            if self.config.device is not None:
                if self.config.device >= len(devices):
                    raise ValueError(f"Device {self.config.device} not found")
                    
                selected_device = devices[self.config.device]
                if selected_device['max_input_channels'] == 0:
                    raise ValueError(f"Device {self.config.device} has no input channels")
                    
                self.logger.info(f"Using device {self.config.device}: {selected_device['name']}")
            else:
                # Use default input device
                default_device = sd.query_devices(kind='input')
                self.logger.info(f"Using default input device: {default_device['name']}")
                
        except Exception as e:
            self.logger.error(f"Audio device validation failed: {e}")
            raise
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback for audio stream - called by sounddevice"""
        if status:
            self.logger.warning(f"Audio stream status: {status}")
        
        try:
            # Convert to float32 and ensure mono
            audio_data = indata.copy().astype(np.float32)
            if audio_data.ndim > 1:
                audio_data = np.mean(audio_data, axis=1)  # Convert to mono
            
            # Add to buffer
            self.audio_buffer.add_audio(audio_data)
            
            # Queue for processing
            self.audio_queue.put(audio_data.copy())
            
            # Update stats
            self.stats['total_audio_processed'] += len(audio_data) / self.config.sample_rate
            
        except Exception as e:
            self.logger.error(f"Audio callback error: {e}")
    
    def _processing_worker(self):
        """Worker thread for audio processing"""
        self.logger.info("Audio processing worker started")
        
        while self.is_recording:
            try:
                # Process queued audio chunks
                audio_chunks = []
                
                # Collect chunks for VAD processing
                try:
                    # Wait for first chunk
                    chunk = self.audio_queue.get(timeout=1.0)
                    audio_chunks.append(chunk)
                    
                    # Collect additional chunks without blocking
                    while True:
                        try:
                            chunk = self.audio_queue.get_nowait()
                            audio_chunks.append(chunk)
                        except queue.Empty:
                            break
                            
                except queue.Empty:
                    continue  # No audio data available
                
                # Combine chunks
                if audio_chunks:
                    combined_audio = np.concatenate(audio_chunks)
                    
                    # Process with VAD if available
                    if self.transcription_service and self.transcription_service.vad_service:
                        self._process_audio_chunk(combined_audio)
                
            except Exception as e:
                self.logger.error(f"Processing worker error: {e}")
        
        self.logger.info("Audio processing worker stopped")
    
    def _process_audio_chunk(self, audio_data: np.ndarray):
        """Process audio chunk with VAD"""
        try:
            # Save chunk temporarily for VAD processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, self.config.sample_rate)
                
                # Process with VAD
                vad_result = self.transcription_service.vad_service.process_audio_file(tmp_file.name)
                
                # Clean up temp file
                os.unlink(tmp_file.name)
                
                # Check if speech detected
                if vad_result['success'] and vad_result['num_segments'] > 0:
                    self.logger.info(f"Speech detected: {vad_result['num_segments']} segments")
                    
                    # Trigger transcription if enough audio accumulated
                    buffer_duration = self.audio_buffer.get_buffer_duration()
                    if buffer_duration >= self.config.transcription_chunk_seconds:
                        self._trigger_transcription()
                        
        except Exception as e:
            self.logger.error(f"Audio chunk processing failed: {e}")
    
    def _trigger_transcription(self):
        """Trigger transcription of accumulated audio"""
        if not self.transcription_service:
            return
            
        try:
            # Get recent audio for transcription
            audio_data = self.audio_buffer.get_recent_audio(self.config.transcription_chunk_seconds)
            
            if len(audio_data) == 0:
                return
            
            # Save for transcription
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                sf.write(tmp_file.name, audio_data, self.config.sample_rate)
                
                # Transcribe in separate thread to avoid blocking
                if self.transcription_thread is None or not self.transcription_thread.is_alive():
                    self.transcription_thread = threading.Thread(
                        target=self._transcription_worker,
                        args=(tmp_file.name,),
                        daemon=True
                    )
                    self.transcription_thread.start()
                    
        except Exception as e:
            self.logger.error(f"Transcription trigger failed: {e}")
    
    def _transcription_worker(self, audio_file: str):
        """Worker thread for transcription"""
        try:
            start_time = time.time()
            self.logger.info(f"Starting transcription of {audio_file}")
            
            # Run transcription
            result = self.transcription_service.transcribe_audio(audio_file)
            
            # Update stats
            processing_time = time.time() - start_time
            self.stats['transcription_chunks'] += 1
            self.stats['last_transcription_time'] = processing_time
            
            # Calculate average processing time
            total_chunks = self.stats['transcription_chunks']
            current_avg = self.stats['average_processing_time']
            self.stats['average_processing_time'] = (current_avg * (total_chunks - 1) + processing_time) / total_chunks
            
            # Call callback if provided
            if self.transcription_callback and result.success:
                self.transcription_callback(result)
            
            self.logger.info(f"Transcription completed in {processing_time:.2f}s: '{result.text[:100]}...'")
            
            # Clean up temp file
            if os.path.exists(audio_file):
                os.unlink(audio_file)
                
            # Clear old audio data to prevent memory growth
            self.audio_buffer.clear_old_data(self.config.buffer_seconds * 0.5)
            
        except Exception as e:
            self.logger.error(f"Transcription worker failed: {e}")
            if os.path.exists(audio_file):
                os.unlink(audio_file)
    
    def start_recording(self):
        """Start real-time audio capture"""
        if self.is_recording:
            self.logger.warning("Recording already in progress")
            return
        
        try:
            self.logger.info("Starting real-time audio capture...")
            self.is_recording = True
            
            # Start audio stream
            self.stream = sd.InputStream(
                callback=self._audio_callback,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                blocksize=self.config.chunk_size,
                device=self.config.device,
                dtype=np.float32
            )
            
            self.stream.start()
            self.logger.info(f"Audio stream started: {self.config.sample_rate}Hz, {self.config.channels} channel(s)")
            
            # Start processing worker
            self.processing_thread = threading.Thread(target=self._processing_worker, daemon=True)
            self.processing_thread.start()
            
            self.logger.info("Real-time audio capture active")
            
        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            raise
    
    def stop_recording(self):
        """Stop real-time audio capture"""
        if not self.is_recording:
            return
        
        self.logger.info("Stopping real-time audio capture...")
        self.is_recording = False
        
        # Stop audio stream
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=5.0)
        
        # Wait for transcription thread to finish
        if self.transcription_thread and self.transcription_thread.is_alive():
            self.transcription_thread.join(timeout=10.0)
        
        self.logger.info("Real-time audio capture stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get capture and processing statistics"""
        stats = self.stats.copy()
        stats['buffer_duration'] = self.audio_buffer.get_buffer_duration()
        stats['is_recording'] = self.is_recording
        stats['queue_size'] = self.audio_queue.qsize()
        return stats
    
    def list_audio_devices(self) -> List[Dict[str, Any]]:
        """List available audio devices"""
        devices = []
        for i, device in enumerate(sd.query_devices()):
            devices.append({
                'id': i,
                'name': device['name'],
                'input_channels': device['max_input_channels'],
                'output_channels': device['max_output_channels'],
                'sample_rate': device['default_samplerate']
            })
        return devices

def create_microphone_capture(transcription_service: Optional[EnhancedTranscriptionService] = None,
                             transcription_callback: Optional[Callable] = None,
                             device_id: Optional[int] = None) -> RealTimeAudioCapture:
    """Create microphone capture configuration"""
    config = AudioStreamConfig(
        device=device_id,
        device_type="microphone",
        sample_rate=16000,
        channels=1,
        chunk_size=1024,
        buffer_seconds=30.0,
        transcription_chunk_seconds=5.0
    )
    
    return RealTimeAudioCapture(config, transcription_service, transcription_callback)

def create_system_audio_capture(transcription_service: Optional[EnhancedTranscriptionService] = None,
                               transcription_callback: Optional[Callable] = None) -> RealTimeAudioCapture:
    """Create system audio capture configuration (requires virtual audio cable)"""
    # Note: System audio capture typically requires a virtual audio cable
    # or specific system configuration
    
    config = AudioStreamConfig(
        device=None,  # Use default or specify virtual cable device
        device_type="system",
        sample_rate=16000,
        channels=1,  # Convert stereo to mono
        chunk_size=1024,
        buffer_seconds=60.0,  # Longer buffer for system audio
        transcription_chunk_seconds=8.0
    )
    
    return RealTimeAudioCapture(config, transcription_service, transcription_callback)

# Example usage and testing
def demo_transcription_callback(result: TranscriptionResult):
    """Example callback for transcription results"""
    if result.success and result.text.strip():
        print(f"\n🎯 TRANSCRIPTION: {result.text}")
        print(f"⏱️ Processing: {result.processing_time:.2f}s")
        print(f"🚀 Efficiency: {result.efficiency_gain:.1f}x")
        print(f"📊 Segments: {len(result.segments)}")
        if result.statistics:
            print(f"🗣️ Speech ratio: {result.statistics['speech_ratio']:.1f}%")
        print("-" * 50)

def test_real_time_capture():
    """Test real-time audio capture system"""
    print("🎤 REAL-TIME AUDIO CAPTURE TEST")
    print("=" * 50)
    
    try:
        # Initialize transcription service
        print("🔧 Initializing transcription service...")
        transcription_service = EnhancedTranscriptionService(
            model_name="openai/whisper-tiny",
            device="cpu",
            vad_aggressiveness=2
        )
        print("✅ Transcription service ready")
        
        # Create audio capture
        capture = create_microphone_capture(
            transcription_service=transcription_service,
            transcription_callback=demo_transcription_callback
        )
        
        # List available devices
        devices = capture.list_audio_devices()
        print(f"\n📱 Available audio devices:")
        for device in devices:
            if device['input_channels'] > 0:
                print(f"  {device['id']}: {device['name']} ({device['input_channels']} inputs)")
        
        # Start capture
        print(f"\n🎤 Starting microphone capture...")
        print("🗣️ Speak into your microphone...")
        print("⏹️ Press Ctrl+C to stop")
        
        capture.start_recording()
        
        # Run for demo period
        try:
            while True:
                time.sleep(1)
                stats = capture.get_stats()
                print(f"\r📊 Buffer: {stats['buffer_duration']:.1f}s | "
                      f"Processed: {stats['total_audio_processed']:.1f}s | "
                      f"Queue: {stats['queue_size']}", end="")
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopping capture...")
            
        capture.stop_recording()
        
        # Show final stats
        final_stats = capture.get_stats()
        print(f"\n📈 FINAL STATS:")
        print(f"   Total audio processed: {final_stats['total_audio_processed']:.1f}s")
        print(f"   Transcription chunks: {final_stats['transcription_chunks']}")
        print(f"   Average processing time: {final_stats['average_processing_time']:.2f}s")
        
        print("✅ Real-time capture test completed!")
        
    except Exception as e:
        print(f"❌ Real-time capture test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Test the real-time capture system
    success = test_real_time_capture()
    if success:
        print("\n🎉 Real-time audio capture is working!")
    else:
        print("\n🔧 Check the errors above and fix issues")
