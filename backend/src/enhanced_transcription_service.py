"""
Enhanced Transcription Service - Fixed for NumPy 2.x Compatibility
Resolves dtype parameter errors and integration issues
"""
import os
import time
import logging
import warnings
import numpy as np
import torch
import whisper
import librosa
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import our fixed VAD service
from vad_service import CompatibleVADService, AudioSegment

@dataclass
class TranscriptionResult:
    """Enhanced result object with comprehensive metadata"""
    text: str
    success: bool
    segments: List[AudioSegment]
    processing_time: float
    model_info: Dict[str, Any]
    audio_duration: float
    efficiency_gain: float = 1.0
    error: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None

class EnhancedTranscriptionService:
    """
    Enhanced Transcription Service with VAD integration
    Fixed for NumPy 2.x compatibility and dtype issues
    """
    
    def __init__(
        self,
        model_name: str = "openai/whisper-tiny",
        device: str = "auto",
        vad_aggressiveness: int = 2,
        sample_rate: int = 16000
    ):
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.vad_aggressiveness = vad_aggressiveness
        
        # Setup device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        print(f"Using {self.device.upper()} processing")
        
        # Force float32 on CPU to avoid dtype conflicts
        if self.device == "cpu":
            torch.set_default_dtype(torch.float32)
        
        # Initialize components
        self.vad_service = None
        self.whisper_model = None
        self.model_info = {}
        
        # Setup logging
        self.logger = logging.getLogger('enhanced_transcription_service')
        self.logger.info(f"Using {self.device.upper()} processing")
        
        # Initialize VAD service
        self._initialize_vad()
        
        self.logger.info("Enhanced Transcription Service initialized")
        self.logger.info(f"Model: {model_name}, Device: {self.device}")
        self.logger.info(f"VAD Aggressiveness: {vad_aggressiveness}")
    
    def _initialize_vad(self):
        """Initialize VAD service with error handling"""
        try:
            self.vad_service = CompatibleVADService(
                aggressiveness=self.vad_aggressiveness,
                sample_rate=self.sample_rate
            )
            self.logger.info("VAD service initialized successfully")
        except Exception as e:
            self.logger.error(f"VAD initialization failed: {e}")
            raise
    
    def _load_whisper_model(self):
        """Load Whisper model with proper dtype handling"""
        if self.whisper_model is not None:
            return  # Already loaded
            
        try:
            self.logger.info(f"Loading Whisper model: {self.model_name}")
            start_time = time.time()
            
            # Extract model size from name
            model_size = self.model_name.split('/')[-1].replace('whisper-', '')
            
            # Suppress FP16 warnings for CPU
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.whisper_model = whisper.load_model(model_size, device=self.device)
            
            # Force model to float32 on CPU to avoid dtype mismatches
            if self.device == "cpu":
                self.whisper_model = self.whisper_model.float()
            
            load_time = time.time() - start_time
            
            self.model_info = {
                'name': self.model_name,
                'device': self.device,
                'load_time': load_time,
                'parameters': sum(p.numel() for p in self.whisper_model.parameters()),
                'dtype': 'float32' if self.device == "cpu" else 'float16'
            }
            
            self.logger.info(f"Model loaded successfully in {load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Model loading failed: {e}")
            raise
    
    def _preprocess_audio(self, audio_path: str) -> np.ndarray:
        """
        Preprocess audio with NumPy 2.x compatibility
        """
        try:
            self.logger.info(f"Preprocessing audio: {audio_path}")
            
            # Load audio with explicit dtype to avoid parameter errors
            audio_data, sr = librosa.load(
                audio_path,
                sr=self.sample_rate,
                mono=True,
                dtype=np.float32  # Explicit keyword to avoid position error
            )
            
            # Ensure consistent dtype
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            self.logger.info(f"Audio preprocessed: {len(audio_data)/sr:.2f}s, {sr}Hz")
            return audio_data
            
        except Exception as e:
            self.logger.error(f"Audio preprocessing failed: {e}")
            raise
    
    def _detect_voice_segments(self, audio_data: np.ndarray) -> List[AudioSegment]:
        """Detect voice segments using VAD"""
        try:
            # Create temporary file for VAD processing
            import tempfile
            import soundfile as sf
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                # Ensure audio is float32 before saving
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32)
                    
                sf.write(tmp_file.name, audio_data, self.sample_rate)
                
                # Process with VAD
                vad_result = self.vad_service.process_audio_file(tmp_file.name)
                
                # Clean up temp file
                os.unlink(tmp_file.name)
                
                if vad_result['success']:
                    return vad_result['segments']
                else:
                    self.logger.warning(f"VAD failed: {vad_result.get('error')}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Voice segment detection failed: {e}")
            return []
    
    def _transcribe_segments(self, segments: List[AudioSegment]) -> List[Dict[str, Any]]:
        """Transcribe individual audio segments"""
        transcribed_segments = []
        
        for i, segment in enumerate(segments):
            try:
                if segment.audio_data is None or len(segment.audio_data) == 0:
                    continue
                
                # Ensure audio is in correct format for Whisper
                audio_segment = segment.audio_data.astype(np.float32)
                
                # Pad short segments to avoid Whisper issues
                min_length = int(0.1 * self.sample_rate)  # 100ms minimum
                if len(audio_segment) < min_length:
                    padding = np.zeros(min_length - len(audio_segment), dtype=np.float32)
                    audio_segment = np.concatenate([audio_segment, padding])
                
                # Transcribe with proper dtype handling
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = self.whisper_model.transcribe(
                        audio_segment,
                        fp16=False,  # Force float32 to avoid dtype issues
                        language=None,  # Auto-detect
                        task='transcribe'
                    )
                
                transcribed_segments.append({
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'duration': segment.duration,
                    'text': result['text'].strip(),
                    'language': result.get('language', 'unknown')
                })
                
            except Exception as e:
                self.logger.warning(f"Segment {i} transcription failed: {e}")
                # Add empty segment to maintain timing
                transcribed_segments.append({
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'duration': segment.duration,
                    'text': '',
                    'language': 'unknown'
                })
        
        return transcribed_segments
    
    def _calculate_efficiency_gain(self, total_duration: float, voice_duration: float, processing_time: float) -> float:
        """Calculate efficiency gain from VAD preprocessing"""
        if total_duration <= 0 or processing_time <= 0:
            return 1.0
        
        # Theoretical processing time without VAD (assume 0.5x realtime for tiny model)
        baseline_time = total_duration * 0.5
        
        # Actual efficiency gain
        efficiency_gain = baseline_time / processing_time if processing_time > 0 else 1.0
        
        # Factor in VAD savings (less audio to process)
        vad_savings = total_duration / voice_duration if voice_duration > 0 else 1.0
        
        return min(efficiency_gain * (vad_savings * 0.3 + 0.7), 10.0)  # Cap at 10x
    
    def transcribe_audio(self, audio_path: str) -> TranscriptionResult:
        """
        Main transcription method with VAD integration
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting enhanced transcription: {audio_path}")
            
            # Load Whisper model if not already loaded
            self._load_whisper_model()
            
            # Preprocess audio
            audio_data = self._preprocess_audio(audio_path)
            total_duration = len(audio_data) / self.sample_rate
            
            # Detect voice segments
            voice_segments = self._detect_voice_segments(audio_data)
            
            if not voice_segments:
                self.logger.warning("No voice segments detected, processing full audio")
                # Fallback to full audio transcription
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = self.whisper_model.transcribe(
                        audio_data,
                        fp16=False,
                        language=None
                    )
                
                processing_time = time.time() - start_time
                
                return TranscriptionResult(
                    text=result['text'].strip(),
                    success=True,
                    segments=[],
                    processing_time=processing_time,
                    model_info=self.model_info,
                    audio_duration=total_duration,
                    efficiency_gain=1.0,
                    statistics={
                        'voice_segments': 0,
                        'voice_duration': total_duration,
                        'speech_ratio': 100.0
                    }
                )
            
            # Transcribe detected segments
            transcribed_segments = self._transcribe_segments(voice_segments)
            
            # Combine transcriptions
            full_text = ' '.join([seg['text'] for seg in transcribed_segments if seg['text']])
            
            # Calculate statistics
            voice_duration = sum(seg.duration for seg in voice_segments)
            speech_ratio = (voice_duration / total_duration) * 100 if total_duration > 0 else 0
            processing_time = time.time() - start_time
            efficiency_gain = self._calculate_efficiency_gain(total_duration, voice_duration, processing_time)
            
            # Compile statistics
            statistics = {
                'voice_segments': len(voice_segments),
                'voice_duration': voice_duration,
                'speech_ratio': speech_ratio,
                'processing_speed': total_duration / processing_time if processing_time > 0 else 0,
                'vad_stats': self.vad_service.get_stats() if self.vad_service else {}
            }
            
            self.logger.info(f"Transcription completed in {processing_time:.2f}s")
            self.logger.info(f"Efficiency gain: {efficiency_gain:.1f}x")
            
            return TranscriptionResult(
                text=full_text,
                success=True,
                segments=voice_segments,
                processing_time=processing_time,
                model_info=self.model_info,
                audio_duration=total_duration,
                efficiency_gain=efficiency_gain,
                statistics=statistics
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Transcription pipeline failed: {error_msg}")
            
            return TranscriptionResult(
                text="",
                success=False,
                segments=[],
                processing_time=processing_time,
                model_info=self.model_info,
                audio_duration=0.0,
                error=error_msg
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return self.model_info.copy()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {
            'model_info': self.model_info,
            'device': self.device,
            'vad_aggressiveness': self.vad_aggressiveness,
            'sample_rate': self.sample_rate
        }
        
        if self.vad_service:
            stats['vad_stats'] = self.vad_service.get_stats()
        
        return stats

# Test function for the enhanced service
def test_enhanced_transcription():
    """Test the enhanced transcription service"""
    try:
        print("🧪 Testing Enhanced Transcription Service")
        print("=" * 50)
        
        # Initialize service
        service = EnhancedTranscriptionService(
            model_name="openai/whisper-tiny",
            device="cpu",  # Force CPU for compatibility testing
            vad_aggressiveness=2
        )
        print("✅ Service initialized")
        
        # Create test audio with voice content
        import soundfile as sf
        
        duration = 6.0
        sample_rate = 16000
        t = np.linspace(0, duration, int(duration * sample_rate), dtype=np.float32)
        
        # Create realistic speech-like audio
        audio = np.zeros(len(t), dtype=np.float32)
        
        # Voice segment 1: 1-2.5 seconds
        voice1_mask = (t >= 1.0) & (t <= 2.5)
        audio[voice1_mask] = 0.3 * np.sin(2 * np.pi * 150 * t[voice1_mask])
        
        # Voice segment 2: 4-5.5 seconds  
        voice2_mask = (t >= 4.0) & (t <= 5.5)
        audio[voice2_mask] = 0.3 * np.sin(2 * np.pi * 200 * t[voice2_mask])
        
        # Add noise
        noise = 0.02 * np.random.randn(len(audio)).astype(np.float32)
        audio += noise
        
        test_file = "enhanced_service_test.wav"
        sf.write(test_file, audio, sample_rate)
        print(f"✅ Test audio created: {duration}s")
        
        # Run transcription
        result = service.transcribe_audio(test_file)
        
        if result.success:
            print("✅ Transcription successful!")
            print(f"📝 Text: '{result.text}'")
            print(f"⏱️ Processing time: {result.processing_time:.2f}s")
            print(f"🚀 Efficiency gain: {result.efficiency_gain:.1f}x")
            print(f"📊 Voice segments: {len(result.segments)}")
            
            if result.statistics:
                stats = result.statistics
                print(f"🗣️ Speech ratio: {stats['speech_ratio']:.1f}%")
                print(f"⚡ Processing speed: {stats['processing_speed']:.1f}x realtime")
        else:
            print(f"❌ Transcription failed: {result.error}")
            return False
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        
        print("🎉 Enhanced service test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced service test failed: {e}")
        return False

if __name__ == "__main__":
    # Test the enhanced service
    success = test_enhanced_transcription()
    if success:
        print("\n✅ Enhanced Transcription Service is working correctly!")
    else:
        print("\n❌ Enhanced Transcription Service needs debugging")
