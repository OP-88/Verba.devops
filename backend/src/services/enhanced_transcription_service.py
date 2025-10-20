#!/usr/bin/env python3
"""
Enhanced Transcription Service for Verba.devops
Integrates Whisper, Silero VAD, pyannote.audio diarization, and T5 summarization
"""

import os
import sys
import time
import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import torch
import whisper
import librosa
from transformers import pipeline

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed audio with metadata"""
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    confidence: float = 0.0
    vad_confidence: float = 0.0

@dataclass
class TranscriptionResult:
    """Complete transcription result with all metadata"""
    text: str
    summary: str
    segments: List[TranscriptionSegment]
    speakers: List[str]
    processing_time: float
    audio_duration: float
    model_info: Dict[str, Any]
    quality_metrics: Dict[str, float]

class EnhancedVADService:
    """Enhanced Voice Activity Detection using Silero VAD with fallback"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.model = None
        self.utils = None
        self.fallback_vad = None
        
        # Try to load Silero VAD
        self._load_silero_vad()
        
        # Initialize fallback VAD if Silero fails
        if not self.model:
            self._init_fallback_vad()
    
    def _load_silero_vad(self):
        """Load Silero VAD model"""
        try:
            # Load from torch.hub
            self.model, self.utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                verbose=False
            )
            
            (self.get_speech_timestamps, 
             self.save_audio, 
             self.read_audio, 
             self.VADIterator, 
             self.collect_chunks) = self.utils
            
            logger.info("✅ Silero VAD loaded successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load Silero VAD: {e}")
            self.model = None
    
    def _init_fallback_vad(self):
        """Initialize fallback WebRTC VAD"""
        try:
            import webrtcvad
            self.fallback_vad = webrtcvad.Vad(2)
            logger.info("✅ Fallback WebRTC VAD initialized")
        except ImportError:
            logger.error("❌ No VAD available - will process entire audio")
    
    def detect_speech_segments(self, audio: np.ndarray) -> List[Tuple[float, float]]:
        """Detect speech segments in audio"""
        if self.model:
            return self._silero_vad_detection(audio)
        elif self.fallback_vad:
            return self._webrtc_vad_detection(audio)
        else:
            # No VAD available - return entire audio
            duration = len(audio) / self.sample_rate
            return [(0.0, duration)]
    
    def _silero_vad_detection(self, audio: np.ndarray) -> List[Tuple[float, float]]:
        """Use Silero VAD for speech detection"""
        try:
            # Ensure audio is float32 and normalized
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            if np.max(np.abs(audio)) > 1.0:
                audio = audio / np.max(np.abs(audio))
            
            # Convert to tensor
            wav_tensor = torch.from_numpy(audio)
            
            # Get speech timestamps
            speech_timestamps = self.get_speech_timestamps(
                wav_tensor,
                self.model,
                sampling_rate=self.sample_rate,
                min_speech_duration_ms=250,
                min_silence_duration_ms=100,
                speech_pad_ms=30
            )
            
            # Convert to list of tuples
            segments = [(ts['start'], ts['end']) for ts in speech_timestamps]
            logger.info(f"🎙️ Silero VAD detected {len(segments)} speech segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Silero VAD failed: {e}")
            if self.fallback_vad:
                return self._webrtc_vad_detection(audio)
            return [(0.0, len(audio) / self.sample_rate)]
    
    def _webrtc_vad_detection(self, audio: np.ndarray) -> List[Tuple[float, float]]:
        """Fallback WebRTC VAD detection"""
        try:
            # Convert to int16
            audio_int16 = (audio * 32768).astype(np.int16)
            frame_duration = 30  # ms
            frame_size = int(self.sample_rate * frame_duration / 1000)
            
            voiced_segments = []
            current_start = None
            
            for i in range(0, len(audio_int16) - frame_size, frame_size):
                frame = audio_int16[i:i + frame_size].tobytes()
                timestamp = i / self.sample_rate
                
                try:
                    is_speech = self.fallback_vad.is_speech(frame, self.sample_rate)
                    
                    if is_speech and current_start is None:
                        current_start = timestamp
                    elif not is_speech and current_start is not None:
                        voiced_segments.append((current_start, timestamp))
                        current_start = None
                except:
                    continue
            
            # Handle audio ending with speech
            if current_start is not None:
                voiced_segments.append((current_start, len(audio_int16) / self.sample_rate))
            
            # Merge close segments
            merged = []
            for start, end in voiced_segments:
                if end - start >= 0.5:  # Minimum 0.5s
                    if merged and start - merged[-1][1] < 1.0:  # Merge if gap < 1s
                        merged[-1] = (merged[-1][0], end)
                    else:
                        merged.append((start, end))
            
            logger.info(f"🎙️ WebRTC VAD detected {len(merged)} speech segments")
            return merged
            
        except Exception as e:
            logger.error(f"❌ WebRTC VAD failed: {e}")
            return [(0.0, len(audio) / self.sample_rate)]

class SpeakerDiarizationService:
    """Speaker diarization using pyannote.audio"""
    
    def __init__(self):
        self.pipeline = None
        self._load_diarization_model()
    
    def _load_diarization_model(self):
        """Load pyannote.audio diarization pipeline"""
        try:
            from pyannote.audio import Pipeline
            self.pipeline = Pipeline.from_pretrained(
                'pyannote/speaker-diarization-3.1',
                use_auth_token=None  # You may need to set this for private models
            )
            logger.info("✅ Speaker diarization pipeline loaded")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load diarization pipeline: {e}")
            self.pipeline = None
    
    def diarize_audio(self, audio_path: str) -> List[Tuple[float, float, str]]:
        """
        Perform speaker diarization on audio file
        Returns: List of (start_time, end_time, speaker_label) tuples
        """
        if not self.pipeline:
            logger.warning("⚠️ No diarization pipeline available")
            return []
        
        try:
            # Apply diarization
            diarization = self.pipeline(audio_path)
            
            # Convert to segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append((turn.start, turn.end, f"Speaker {speaker}"))
            
            logger.info(f"🎭 Detected {len(set([s[2] for s in segments]))} speakers in {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Speaker diarization failed: {e}")
            return []

class SummarizationService:
    """Text summarization using T5-small"""
    
    def __init__(self):
        self.summarizer = None
        self._load_summarization_model()
    
    def _load_summarization_model(self):
        """Load T5-small summarization model"""
        try:
            self.summarizer = pipeline(
                "summarization",
                model="t5-small",
                tokenizer="t5-small",
                framework="pt",
                device=-1  # CPU
            )
            logger.info("✅ Summarization model loaded")
        except Exception as e:
            logger.warning(f"⚠️ Failed to load summarization model: {e}")
            self.summarizer = None
    
    def summarize_text(self, text: str, max_length: int = 50, min_length: int = 10) -> str:
        """Generate abstractive summary of text"""
        if not self.summarizer or not text.strip():
            return ""
        
        try:
            # Limit input length to avoid memory issues
            max_input_length = 512
            if len(text.split()) > max_input_length:
                text = ' '.join(text.split()[:max_input_length])
            
            result = self.summarizer(
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False,
                early_stopping=True
            )
            
            summary = result[0]['summary_text'].strip()
            logger.info(f"📝 Generated summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            return ""

class EnhancedTranscriptionService:
    """
    Main transcription service integrating all components
    Designed for <1GB RAM usage with efficient processing
    """
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.whisper_model = None
        self.sample_rate = 16000
        
        # Initialize services
        self.vad_service = EnhancedVADService(self.sample_rate)
        self.diarization_service = SpeakerDiarizationService()
        self.summarization_service = SummarizationService()
        
        # Load Whisper model
        self._load_whisper_model()
        
        # Performance tracking
        self.stats = {
            "transcriptions": 0,
            "total_duration": 0.0,
            "total_processing_time": 0.0
        }
    
    def _load_whisper_model(self):
        """Load Whisper model with memory optimization"""
        try:
            logger.info(f"🤖 Loading Whisper {self.model_size} model...")
            start_time = time.time()
            
            self.whisper_model = whisper.load_model(self.model_size)
            
            load_time = time.time() - start_time
            logger.info(f"✅ Whisper model loaded in {load_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def _preprocess_audio(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """Load and preprocess audio with noise reduction"""
        try:
            # Load audio
            audio, sr = librosa.load(
                audio_path,
                sr=self.sample_rate,
                mono=True,
                dtype=np.float32
            )
            
            # Basic noise reduction (high-pass filter)
            from scipy import signal
            nyquist = sr / 2
            cutoff = 80 / nyquist
            b, a = signal.butter(4, cutoff, btype='high')
            audio = signal.filtfilt(b, a, audio)
            
            # Normalize
            if np.max(np.abs(audio)) > 0:
                audio = audio / np.max(np.abs(audio))
            
            duration = len(audio) / sr
            logger.info(f"📁 Loaded audio: {duration:.2f}s @ {sr}Hz")
            
            return audio, duration
            
        except Exception as e:
            logger.error(f"❌ Audio preprocessing failed: {e}")
            raise
    
    def _merge_segments_with_speakers(self, 
                                    transcription_segments: List[TranscriptionSegment],
                                    speaker_segments: List[Tuple[float, float, str]]) -> List[TranscriptionSegment]:
        """Merge transcription segments with speaker labels"""
        if not speaker_segments:
            return transcription_segments
        
        # Simple overlap-based assignment
        for trans_seg in transcription_segments:
            best_overlap = 0
            best_speaker = "Speaker 1"
            
            for start, end, speaker in speaker_segments:
                # Calculate overlap
                overlap_start = max(trans_seg.start_time, start)
                overlap_end = min(trans_seg.end_time, end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = speaker
            
            trans_seg.speaker = best_speaker
        
        return transcription_segments
    
    def transcribe_audio(self, audio_path: str, include_diarization: bool = True, 
                        include_summary: bool = True) -> TranscriptionResult:
        """
        Complete audio transcription with all enhancements
        
        Args:
            audio_path: Path to audio file
            include_diarization: Whether to perform speaker diarization
            include_summary: Whether to generate summary
        
        Returns:
            TranscriptionResult with all metadata
        """
        start_time = time.time()
        
        try:
            # Preprocess audio
            audio, audio_duration = self._preprocess_audio(audio_path)
            
            # Voice Activity Detection
            logger.info("🔍 Performing voice activity detection...")
            speech_segments = self.vad_service.detect_speech_segments(audio)
            
            if not speech_segments:
                return TranscriptionResult(
                    text="No speech detected in audio",
                    summary="",
                    segments=[],
                    speakers=[],
                    processing_time=time.time() - start_time,
                    audio_duration=audio_duration,
                    model_info={"whisper_model": self.model_size, "vad": "none"},
                    quality_metrics={"speech_ratio": 0.0}
                )
            
            # Speaker Diarization (parallel with transcription prep)
            speaker_segments = []
            if include_diarization:
                logger.info("🎭 Performing speaker diarization...")
                speaker_segments = self.diarization_service.diarize_audio(audio_path)
            
            # Transcribe speech segments
            logger.info(f"🎙️ Transcribing {len(speech_segments)} speech segments...")
            transcription_segments = []
            full_text_parts = []
            
            for i, (start, end) in enumerate(speech_segments):
                logger.info(f"  Processing segment {i+1}/{len(speech_segments)} ({start:.1f}-{end:.1f}s)")
                
                # Extract audio segment
                start_sample = int(start * self.sample_rate)
                end_sample = int(end * self.sample_rate)
                segment_audio = audio[start_sample:end_sample]
                
                # Transcribe with optimized settings
                result = self.whisper_model.transcribe(
                    segment_audio,
                    language='en',  # Auto-detect if needed
                    task='transcribe',
                    temperature=0.0,  # Deterministic output
                    best_of=1,  # Memory optimization
                    beam_size=1,  # Memory optimization
                    word_timestamps=False,  # Memory optimization
                    fp16=False,  # CPU compatibility
                    verbose=False
                )
                
                segment_text = result["text"].strip()
                if segment_text:
                    # Calculate confidence (simplified)
                    avg_logprob = result.get("segments", [{}])[0].get("avg_logprob", -1.0) if result.get("segments") else -1.0
                    confidence = max(0.0, min(1.0, np.exp(avg_logprob) if avg_logprob > -5 else 0.1))
                    
                    segment_obj = TranscriptionSegment(
                        start_time=start,
                        end_time=end,
                        text=segment_text,
                        confidence=confidence,
                        vad_confidence=1.0  # Simplified
                    )
                    
                    transcription_segments.append(segment_obj)
                    full_text_parts.append(segment_text)
            
            # Merge with speaker information
            if speaker_segments:
                transcription_segments = self._merge_segments_with_speakers(
                    transcription_segments, speaker_segments
                )
            
            # Generate full text
            full_text = " ".join(full_text_parts)
            
            # Generate summary
            summary = ""
            if include_summary and full_text:
                logger.info("📝 Generating summary...")
                summary = self.summarization_service.summarize_text(full_text)
            
            # Calculate metrics
            speech_duration = sum(end - start for start, end in speech_segments)
            speech_ratio = speech_duration / audio_duration if audio_duration > 0 else 0.0
            
            processing_time = time.time() - start_time
            
            # Update stats
            self.stats["transcriptions"] += 1
            self.stats["total_duration"] += audio_duration
            self.stats["total_processing_time"] += processing_time
            
            # Get unique speakers
            speakers = list(set(seg.speaker for seg in transcription_segments if seg.speaker))
            
            logger.info(f"✅ Transcription completed in {processing_time:.2f}s "
                       f"({audio_duration/processing_time:.1f}x real-time)")
            
            return TranscriptionResult(
                text=full_text,
                summary=summary,
                segments=transcription_segments,
                speakers=speakers,
                processing_time=processing_time,
                audio_duration=audio_duration,
                model_info={
                    "whisper_model": self.model_size,
                    "vad": "silero" if self.vad_service.model else "webrtc",
                    "diarization": "pyannote" if self.diarization_service.pipeline else "none",
                    "summarization": "t5-small" if self.summarization_service.summarizer else "none"
                },
                quality_metrics={
                    "speech_ratio": speech_ratio,
                    "avg_confidence": np.mean([seg.confidence for seg in transcription_segments]) if transcription_segments else 0.0,
                    "processing_speed": audio_duration / processing_time if processing_time > 0 else 0.0
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise
    
    async def transcribe_audio_stream(self, audio_path: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream transcription results as they become available
        Useful for real-time applications
        """
        try:
            # This is a simplified streaming implementation
            # In a full implementation, you'd process chunks in real-time
            result = self.transcribe_audio(audio_path)
            
            # Yield intermediate results
            for i, segment in enumerate(result.segments):
                yield {
                    "type": "segment",
                    "segment_id": i,
                    "start_time": segment.start_time,
                    "end_time": segment.end_time,
                    "text": segment.text,
                    "speaker": segment.speaker,
                    "confidence": segment.confidence
                }
                
                # Small delay to simulate real-time processing
                await asyncio.sleep(0.1)
            
            # Final result
            yield {
                "type": "final",
                "text": result.text,
                "summary": result.summary,
                "speakers": result.speakers,
                "processing_time": result.processing_time,
                "quality_metrics": result.quality_metrics
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        avg_processing_speed = (
            self.stats["total_duration"] / self.stats["total_processing_time"] 
            if self.stats["total_processing_time"] > 0 else 0.0
        )
        
        return {
            "transcriptions_completed": self.stats["transcriptions"],
            "total_audio_duration": self.stats["total_duration"],
            "total_processing_time": self.stats["total_processing_time"],
            "average_processing_speed": f"{avg_processing_speed:.1f}x real-time",
            "services_available": {
                "whisper": self.whisper_model is not None,
                "vad": self.vad_service.model is not None or self.vad_service.fallback_vad is not None,
                "diarization": self.diarization_service.pipeline is not None,
                "summarization": self.summarization_service.summarizer is not None
            },
            "model_info": {
                "whisper_model": self.model_size,
                "sample_rate": self.sample_rate
            }
        }

# Factory function for easy instantiation
def create_enhanced_transcription_service(model_size: str = "base") -> EnhancedTranscriptionService:
    """Create and initialize the enhanced transcription service"""
    return EnhancedTranscriptionService(model_size=model_size)

# Example usage
if __name__ == "__main__":
    service = create_enhanced_transcription_service()
    print("Enhanced Transcription Service initialized successfully!")
    print("Service stats:", service.get_service_stats())