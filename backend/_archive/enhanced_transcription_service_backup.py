#!/usr/bin/env python3
"""
Enhanced Transcription Service with VAD Integration
Verba Project - Phase 2 Implementation
"""

import numpy as np
import torch
import librosa
import logging
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path
import time
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# Try importing from current directory first, then from services
try:
    from vad_service import VADService
except ImportError:
    try:
        from services.vad_service import VADService
    except ImportError:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))
        from vad_service import VADService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class AudioSegment:
    """Represents a voice activity segment"""
    start_time: float
    end_time: float
    audio_data: np.ndarray
    confidence: float
    duration: float
    
    @property
    def is_valid(self) -> bool:
        """Check if segment is valid for transcription"""
        return (
            self.duration >= 0.5 and  # Minimum 500ms
            self.confidence >= 0.6 and  # Minimum confidence
            len(self.audio_data) > 0
        )

@dataclass
class TranscriptionResult:
    """Enhanced transcription result with VAD metadata"""
    text: str
    segments: List[Dict[str, Any]]
    processing_stats: Dict[str, Any]
    vad_stats: Dict[str, Any]
    total_duration: float
    speech_duration: float
    speech_ratio: float

class EnhancedTranscriptionService:
    """
    Advanced transcription service with VAD integration
    Provides efficient, accurate speech-to-text with voice activity detection
    """
    
    def __init__(self, 
                 model_name: str = "openai/whisper-base",
                 vad_aggressiveness: int = 2,
                 device: str = "auto"):
        """
        Initialize the Enhanced Transcription Service
        
        Args:
            model_name: Whisper model to use
            vad_aggressiveness: VAD sensitivity (0-3, higher = more aggressive)
            device: Processing device ('cpu', 'cuda', or 'auto')
        """
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.vad_service = VADService(aggressiveness=vad_aggressiveness)
        
        # Processing parameters
        self.sample_rate = 16000
        self.chunk_duration = 30.0  # seconds
        self.overlap_duration = 2.0  # seconds
        self.min_segment_duration = 0.5  # seconds
        self.max_segment_duration = 30.0  # seconds
        
        # Performance tracking
        self.stats = {
            'total_files_processed': 0,
            'total_audio_duration': 0.0,
            'total_processing_time': 0.0,
            'total_speech_detected': 0.0,
            'efficiency_ratio': 0.0
        }
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"Enhanced Transcription Service initialized")
        logger.info(f"Model: {model_name}, Device: {self.device}")
        logger.info(f"VAD Aggressiveness: {vad_aggressiveness}")

    def _setup_device(self, device: str) -> str:
        """Setup and validate processing device"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                logger.info("CUDA available - using GPU acceleration")
            else:
                device = "cpu"
                logger.info("Using CPU processing")
        return device

    def load_whisper_model(self):
        """Load Whisper model for transcription"""
        try:
            import whisper
            
            start_time = time.time()
            logger.info(f"Loading Whisper model: {self.model_name}")
            
            # Extract model size from full model name
            model_size = self.model_name.split('/')[-1].replace('whisper-', '')
            self.model = whisper.load_model(model_size, device=self.device)
            
            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.2f}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            return False

    def preprocess_audio(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """
        Preprocess audio file for transcription
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, duration)
        """
        try:
            logger.info(f"Preprocessing audio: {audio_path}")
            
            # Load audio with librosa
            audio, sr = librosa.load(
                audio_path, 
                sr=self.sample_rate,
                mono=True
            )
            
            duration = len(audio) / self.sample_rate
            logger.info(f"Audio loaded: {duration:.2f}s at {sr}Hz")
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            return audio, duration
            
        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            raise

    def detect_voice_segments(self, audio: np.ndarray) -> List[AudioSegment]:
        """
        Detect voice activity segments using VAD
        
        Args:
            audio: Audio data array
            
        Returns:
            List of voice activity segments
        """
        logger.info("Detecting voice activity segments...")
        
        try:
            # Process audio through VAD
            vad_result = self.vad_service.process_audio(audio, self.sample_rate)
            
            if not vad_result['success']:
                logger.warning("VAD processing failed, using full audio")
                return [AudioSegment(
                    start_time=0.0,
                    end_time=len(audio) / self.sample_rate,
                    audio_data=audio,
                    confidence=1.0,
                    duration=len(audio) / self.sample_rate
                )]
            
            segments = []
            voice_segments = vad_result['voice_segments']
            
            logger.info(f"Found {len(voice_segments)} voice segments")
            
            for segment in voice_segments:
                start_sample = int(segment['start'] * self.sample_rate)
                end_sample = int(segment['end'] * self.sample_rate)
                
                # Extract audio data for segment
                segment_audio = audio[start_sample:end_sample]
                
                if len(segment_audio) > 0:
                    audio_segment = AudioSegment(
                        start_time=segment['start'],
                        end_time=segment['end'],
                        audio_data=segment_audio,
                        confidence=segment['confidence'],
                        duration=segment['duration']
                    )
                    
                    if audio_segment.is_valid:
                        segments.append(audio_segment)
                        logger.debug(f"Added segment: {segment['start']:.2f}-{segment['end']:.2f}s")
            
            logger.info(f"Created {len(segments)} valid audio segments")
            return segments
            
        except Exception as e:
            logger.error(f"Voice activity detection failed: {e}")
            # Fallback to full audio
            return [AudioSegment(
                start_time=0.0,
                end_time=len(audio) / self.sample_rate,
                audio_data=audio,
                confidence=1.0,
                duration=len(audio) / self.sample_rate
            )]

    def transcribe_segment(self, segment: AudioSegment) -> Dict[str, Any]:
        """
        Transcribe a single audio segment
        
        Args:
            segment: Audio segment to transcribe
            
        Returns:
            Transcription result for segment
        """
        try:
            start_time = time.time()
            
            # Transcribe using Whisper
            result = self.model.transcribe(
                segment.audio_data,
                fp16=False,  # Use fp32 for better accuracy
                language=None,  # Auto-detect language
                task="transcribe"
            )
            
            processing_time = time.time() - start_time
            
            return {
                'text': result['text'].strip(),
                'language': result.get('language', 'unknown'),
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'duration': segment.duration,
                'confidence': segment.confidence,
                'processing_time': processing_time,
                'words': result.get('segments', [])
            }
            
        except Exception as e:
            logger.error(f"Segment transcription failed: {e}")
            return {
                'text': '',
                'language': 'unknown',
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'duration': segment.duration,
                'confidence': 0.0,
                'processing_time': 0.0,
                'error': str(e)
            }

    def transcribe_segments_parallel(self, segments: List[AudioSegment], 
                                   max_workers: int = 2) -> List[Dict[str, Any]]:
        """
        Transcribe multiple segments in parallel
        
        Args:
            segments: List of audio segments
            max_workers: Maximum number of worker threads
            
        Returns:
            List of transcription results
        """
        logger.info(f"Transcribing {len(segments)} segments with {max_workers} workers")
        
        results = []
        
        # For small numbers of segments, process sequentially
        if len(segments) <= 2:
            for i, segment in enumerate(segments):
                logger.info(f"Transcribing segment {i+1}/{len(segments)}")
                result = self.transcribe_segment(segment)
                results.append(result)
        else:
            # Use thread pool for parallel processing
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_segment = {
                    executor.submit(self.transcribe_segment, segment): segment 
                    for segment in segments
                }
                
                for i, future in enumerate(future_to_segment):
                    logger.info(f"Processing segment {i+1}/{len(segments)}")
                    result = future.result()
                    results.append(result)
        
        return results

    def merge_transcription_results(self, segment_results: List[Dict[str, Any]]) -> str:
        """
        Merge individual segment transcriptions into final text
        
        Args:
            segment_results: List of segment transcription results
            
        Returns:
            Merged transcription text
        """
        # Filter successful transcriptions
        valid_results = [
            result for result in segment_results 
            if result.get('text') and 'error' not in result
        ]
        
        if not valid_results:
            logger.warning("No valid transcription results found")
            return ""
        
        # Sort by start time
        valid_results.sort(key=lambda x: x['start_time'])
        
        # Merge text segments
        merged_text = []
        for result in valid_results:
            text = result['text'].strip()
            if text:
                merged_text.append(text)
        
        final_text = ' '.join(merged_text)
        logger.info(f"Merged {len(valid_results)} segments into final transcription")
        
        return final_text

    def transcribe_file(self, audio_path: str) -> TranscriptionResult:
        """
        Complete transcription pipeline with VAD enhancement
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Complete transcription result with metadata
        """
        start_time = time.time()
        logger.info(f"Starting enhanced transcription: {audio_path}")
        
        try:
            # Step 1: Preprocess audio
            audio, total_duration = self.preprocess_audio(audio_path)
            
            # Step 2: Detect voice segments
            voice_segments = self.detect_voice_segments(audio)
            
            if not voice_segments:
                logger.warning("No voice segments detected")
                return TranscriptionResult(
                    text="",
                    segments=[],
                    processing_stats={},
                    vad_stats={},
                    total_duration=total_duration,
                    speech_duration=0.0,
                    speech_ratio=0.0
                )
            
            # Step 3: Transcribe segments
def transcribe_segment(self, segment: AudioSegment) -> Dict[str, Any]:
    """
    Transcribe a single audio segment
    """
    try:
        start_time = time.time()
        
        # Ensure audio is float32 (fix the dtype issue)
        audio_data = segment.audio_data.astype(np.float32)
        
        # Transcribe using Whisper
        result = self.model.transcribe(
            audio_data,
            fp16=False,  # Use fp32 for better CPU compatibility
            language=None,  # Auto-detect language
            task="transcribe"
        )
        
        processing_time = time.time() - start_time
        
        return {
            'text': result['text'].strip(),
            'language': result.get('language', 'unknown'),
            'start_time': segment.start_time,
            'end_time': segment.end_time,
            'duration': segment.duration,
            'confidence': segment.confidence,
            'processing_time': processing_time,
            'words': result.get('segments', [])
        }
        
    except Exception as e:
        logger.error(f"Segment transcription failed: {e}")
        return {
            'text': '',
            'language': 'unknown',
            'start_time': segment.start_time,
            'end_time': segment.end_time,
            'duration': segment.duration,
            'confidence': 0.0,
            'processing_time': 0.0,
            'error': str(e)
        }
            
            # Step 4: Merge results
            final_text = self.merge_transcription_results(segment_results)
            
            # Calculate statistics
            total_processing_time = time.time() - start_time
            speech_duration = sum(seg.duration for seg in voice_segments)
            speech_ratio = speech_duration / total_duration if total_duration > 0 else 0
            
            # VAD statistics
            vad_stats = self.vad_service.get_stats()
            
            # Processing statistics
            processing_stats = {
                'total_processing_time': total_processing_time,
                'segments_processed': len(voice_segments),
                'average_segment_duration': speech_duration / len(voice_segments) if voice_segments else 0,
                'processing_speed_ratio': total_duration / total_processing_time if total_processing_time > 0 else 0,
                'efficiency_gain': (total_duration - speech_duration) / total_duration if total_duration > 0 else 0
            }
            
            # Update global stats
            with self._lock:
                self.stats['total_files_processed'] += 1
                self.stats['total_audio_duration'] += total_duration
                self.stats['total_processing_time'] += total_processing_time
                self.stats['total_speech_detected'] += speech_duration
                
                if self.stats['total_audio_duration'] > 0:
                    self.stats['efficiency_ratio'] = (
                        self.stats['total_speech_detected'] / 
                        self.stats['total_audio_duration']
                    )
            
            logger.info(f"Transcription completed in {total_processing_time:.2f}s")
            logger.info(f"Speech ratio: {speech_ratio:.2%}")
            logger.info(f"Efficiency gain: {processing_stats['efficiency_gain']:.2%}")
            
            return TranscriptionResult(
                text=final_text,
                segments=segment_results,
                processing_stats=processing_stats,
                vad_stats=vad_stats,
                total_duration=total_duration,
                speech_duration=speech_duration,
                speech_ratio=speech_ratio
            )
            
        except Exception as e:
            logger.error(f"Transcription pipeline failed: {e}")
            raise

    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive service statistics"""
        with self._lock:
            return {
                **self.stats.copy(),
                'vad_stats': self.vad_service.get_stats(),
                'average_processing_speed': (
                    self.stats['total_audio_duration'] / self.stats['total_processing_time']
                    if self.stats['total_processing_time'] > 0 else 0
                )
            }

    def reset_stats(self):
        """Reset all statistics"""
        with self._lock:
            self.stats = {
                'total_files_processed': 0,
                'total_audio_duration': 0.0,
                'total_processing_time': 0.0,
                'total_speech_detected': 0.0,
                'efficiency_ratio': 0.0
            }
        self.vad_service.reset_stats()
        logger.info("Service statistics reset")


# Example usage and testing
if __name__ == "__main__":
    def main():
        """Test the Enhanced Transcription Service"""
        print("🚀 Testing Enhanced Transcription Service with VAD")
        print("=" * 60)
        
        # Initialize service
        try:
            service = EnhancedTranscriptionService(
                model_name="openai/whisper-base",
                vad_aggressiveness=2,
                device="auto"
            )
            
            # Load Whisper model
            if not service.load_whisper_model():
                print("❌ Failed to load Whisper model")
                return
            
            print("✅ Enhanced Transcription Service initialized")
            print("✅ Whisper model loaded")
            print("✅ VAD service ready")
            print()
            
            # Test with sample audio file (if available)
            test_files = [
                "sample_audio.wav",
                "test_recording.mp3",
                "../test_audio/sample.wav"
            ]
            
            for test_file in test_files:
                if Path(test_file).exists():
                    print(f"🎯 Testing with: {test_file}")
                    
                    try:
                        result = service.transcribe_file(test_file)
                        
                        print(f"📝 Transcription: {result.text[:100]}...")
                        print(f"⏱️  Total Duration: {result.total_duration:.2f}s")
                        print(f"🗣️  Speech Duration: {result.speech_duration:.2f}s")
                        print(f"📊 Speech Ratio: {result.speech_ratio:.2%}")
                        print(f"⚡ Processing Speed: {result.processing_stats['processing_speed_ratio']:.2f}x")
                        print()
                        
                    except Exception as e:
                        print(f"❌ Test failed: {e}")
                    
                    break
            else:
                print("ℹ️  No test audio files found")
                print("   Place a test audio file in the current directory to test transcription")
            
            # Display service statistics
            stats = service.get_service_stats()
            print("📈 Service Statistics:")
            for key, value in stats.items():
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for sub_key, sub_value in value.items():
                        print(f"     {sub_key}: {sub_value}")
                else:
                    print(f"   {key}: {value}")
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return
        
        print("🎉 Enhanced Transcription Service test completed!")
    
    main()
