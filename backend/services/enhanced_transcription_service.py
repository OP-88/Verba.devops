#!/usr/bin/env python3
"""
Enhanced Transcription Service
Combines Whisper, VAD, Speaker Diarization, and Summarization
"""

import os
import logging
import asyncio
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import whisper
import torch

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionSegment:
    """Represents a segment of transcribed audio"""
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'text': self.text,
            'confidence': self.confidence,
            'speaker': self.speaker
        }

@dataclass
class TranscriptionResult:
    """Complete transcription result with metadata"""
    text: str
    segments: List[TranscriptionSegment]
    duration: float
    language: Optional[str] = None
    processing_time: float = 0.0
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'segments': [seg.to_dict() for seg in self.segments],
            'duration': self.duration,
            'language': self.language,
            'processing_time': self.processing_time,
            'summary': self.summary
        }


class EnhancedVADService:
    """Enhanced Voice Activity Detection using Silero VAD with WebRTC fallback"""
    
    def __init__(self):
        self.model = None
        self.utils = None
        self.fallback_vad = None
        self._initialize_vad()
    
    def _initialize_vad(self):
        """Initialize VAD with Silero, fallback to WebRTC"""
        try:
            # Try to load Silero VAD
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.model = model
            self.utils = utils
            logger.info("✅ Silero VAD initialized successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load Silero VAD: {e}")
            try:
                import webrtcvad
                self.fallback_vad = webrtcvad.Vad(2)
                logger.info("✅ WebRTC VAD initialized as fallback")
            except ImportError:
                logger.error("❌ No VAD available - install webrtcvad")
    
    def detect_speech_segments(self, audio: np.ndarray, sample_rate: int = 16000) -> List[Tuple[float, float]]:
        """Detect speech segments in audio"""
        if self.model is not None:
            return self._silero_vad(audio, sample_rate)
        elif self.fallback_vad is not None:
            return self._webrtc_vad(audio, sample_rate)
        else:
            # Return entire audio as one segment if no VAD
            duration = len(audio) / sample_rate
            return [(0.0, duration)]
    
    def _silero_vad(self, audio: np.ndarray, sample_rate: int) -> List[Tuple[float, float]]:
        """Use Silero VAD for speech detection"""
        try:
            get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks = self.utils
            
            # Ensure audio is float32 and correct sample rate
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            # Get speech timestamps
            speech_timestamps = get_speech_timestamps(audio, self.model, sampling_rate=sample_rate)
            
            # Convert to time segments
            segments = []
            for speech in speech_timestamps:
                start_time = speech['start'] / sample_rate
                end_time = speech['end'] / sample_rate
                segments.append((start_time, end_time))
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ Silero VAD failed: {e}")
            return [(0.0, len(audio) / sample_rate)]
    
    def _webrtc_vad(self, audio: np.ndarray, sample_rate: int) -> List[Tuple[float, float]]:
        """Use WebRTC VAD for speech detection"""
        try:
            # Convert to int16 for WebRTC
            audio_int16 = (audio * 32768).astype(np.int16)
            
            frame_duration = 30  # ms
            frame_size = int(sample_rate * frame_duration / 1000)
            
            segments = []
            current_start = None
            
            for i in range(0, len(audio_int16) - frame_size, frame_size):
                frame = audio_int16[i:i + frame_size].tobytes()
                
                try:
                    is_speech = self.fallback_vad.is_speech(frame, sample_rate)
                    timestamp = i / sample_rate
                    
                    if is_speech and current_start is None:
                        current_start = timestamp
                    elif not is_speech and current_start is not None:
                        segments.append((current_start, timestamp))
                        current_start = None
                except:
                    continue
            
            # Handle case where audio ends with speech
            if current_start is not None:
                segments.append((current_start, len(audio_int16) / sample_rate))
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ WebRTC VAD failed: {e}")
            return [(0.0, len(audio) / sample_rate)]


class SpeakerDiarizationService:
    """Speaker diarization using pyannote.audio"""
    
    def __init__(self):
        self.pipeline = None
        self._initialize_diarization()
    
    def _initialize_diarization(self):
        """Initialize speaker diarization pipeline"""
        try:
            from pyannote.audio import Pipeline
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=os.getenv("HUGGINGFACE_ACCESS_TOKEN")
            )
            logger.info("✅ Speaker diarization initialized")
        except Exception as e:
            logger.warning(f"⚠️ Speaker diarization not available: {e}")
    
    def diarize_audio(self, audio_path: str) -> List[Tuple[float, float, str]]:
        """Perform speaker diarization on audio file"""
        if self.pipeline is None:
            return []
        
        try:
            diarization = self.pipeline(audio_path)
            
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append((turn.start, turn.end, f"Speaker {speaker}"))
            
            return segments
            
        except Exception as e:
            logger.error(f"❌ Diarization failed: {e}")
            return []


class SummarizationService:
    """Text summarization using Hugging Face transformers"""
    
    def __init__(self):
        self.summarizer = None
        self._initialize_summarizer()
    
    def _initialize_summarizer(self):
        """Initialize summarization pipeline"""
        try:
            from transformers import pipeline
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("✅ Summarization service initialized")
        except Exception as e:
            logger.warning(f"⚠️ Summarization not available: {e}")
    
    def summarize_text(self, text: str, max_length: int = 150) -> Optional[str]:
        """Summarize the given text"""
        if self.summarizer is None or len(text.split()) < 50:
            return None
        
        try:
            # Truncate text if too long for model
            max_input_length = 1024
            words = text.split()
            if len(words) > max_input_length:
                text = ' '.join(words[:max_input_length])
            
            summary = self.summarizer(
                text,
                max_length=max_length,
                min_length=30,
                do_sample=False
            )
            
            return summary[0]['summary_text']
            
        except Exception as e:
            logger.error(f"❌ Summarization failed: {e}")
            return None


class EnhancedTranscriptionService:
    """Enhanced transcription service with VAD, diarization, and summarization"""
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.sample_rate = 16000
        self.whisper_model = None
        self.vad_service = EnhancedVADService()
        self.diarization_service = SpeakerDiarizationService()
        self.summarization_service = SummarizationService()
        
        self._initialize_whisper()
    
    def _initialize_whisper(self):
        """Initialize Whisper model"""
        try:
            self.whisper_model = whisper.load_model(self.model_size)
            logger.info(f"✅ Whisper {self.model_size} model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def _preprocess_audio(self, audio_path: str) -> Tuple[np.ndarray, float]:
        """Load and preprocess audio file"""
        try:
            audio, sr = sf.read(audio_path)
            
            # Convert to mono if stereo
            if len(audio.shape) > 1:
                audio = np.mean(audio, axis=1)
            
            # Resample if needed (Whisper expects 16kHz)
            if sr != self.sample_rate:
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=self.sample_rate)
            
            # Ensure float32
            if audio.dtype != np.float32:
                audio = audio.astype(np.float32)
            
            duration = len(audio) / self.sample_rate
            return audio, duration
            
        except Exception as e:
            logger.error(f"❌ Audio preprocessing failed: {e}")
            raise
    
    def _merge_segments_with_speakers(
        self, 
        transcription_segments: List[TranscriptionSegment], 
        speaker_segments: List[Tuple[float, float, str]]
    ) -> List[TranscriptionSegment]:
        """Merge transcription segments with speaker information"""
        if not speaker_segments:
            return transcription_segments
        
        merged_segments = []
        
        for trans_seg in transcription_segments:
            # Find overlapping speaker segments
            best_speaker = None
            best_overlap = 0
            
            for spk_start, spk_end, speaker in speaker_segments:
                # Calculate overlap
                overlap_start = max(trans_seg.start_time, spk_start)
                overlap_end = min(trans_seg.end_time, spk_end)
                overlap = max(0, overlap_end - overlap_start)
                
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = speaker
            
            # Create new segment with speaker info
            new_segment = TranscriptionSegment(
                start_time=trans_seg.start_time,
                end_time=trans_seg.end_time,
                text=trans_seg.text,
                confidence=trans_seg.confidence,
                speaker=best_speaker
            )
            merged_segments.append(new_segment)
        
        return merged_segments
    
    async def transcribe_audio(
        self, 
        audio_path: str, 
        enable_vad: bool = True,
        enable_diarization: bool = False,
        enable_summarization: bool = False
    ) -> TranscriptionResult:
        """Perform enhanced transcription with optional VAD, diarization, and summarization"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Preprocess audio
            audio, duration = self._preprocess_audio(audio_path)
            logger.info(f"🎵 Audio loaded: {duration:.2f}s")
            
            # Apply VAD if enabled
            speech_segments = None
            if enable_vad:
                speech_segments = self.vad_service.detect_speech_segments(audio, self.sample_rate)
                logger.info(f"🎯 VAD found {len(speech_segments)} speech segments")
            
            # Perform Whisper transcription
            result = self.whisper_model.transcribe(audio_path, language=None)
            
            # Convert Whisper segments to our format
            transcription_segments = []
            for segment in result.get('segments', []):
                trans_seg = TranscriptionSegment(
                    start_time=segment['start'],
                    end_time=segment['end'],
                    text=segment['text'].strip(),
                    confidence=1.0 + segment.get('avg_logprob', -1.0)  # Convert logprob to confidence
                )
                transcription_segments.append(trans_seg)
            
            # Perform speaker diarization if enabled
            speaker_segments = []
            if enable_diarization:
                speaker_segments = self.diarization_service.diarize_audio(audio_path)
                logger.info(f"👥 Diarization found {len(speaker_segments)} speaker segments")
            
            # Merge transcription with speaker info
            if speaker_segments:
                transcription_segments = self._merge_segments_with_speakers(
                    transcription_segments, speaker_segments
                )
            
            # Generate summary if enabled
            summary = None
            if enable_summarization:
                summary = self.summarization_service.summarize_text(result['text'])
                if summary:
                    logger.info("📝 Summary generated")
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return TranscriptionResult(
                text=result['text'],
                segments=transcription_segments,
                duration=duration,
                language=result.get('language'),
                processing_time=processing_time,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise
    
    def transcribe_audio_sync(self, *args, **kwargs) -> TranscriptionResult:
        """Synchronous wrapper for transcribe_audio"""
        return asyncio.run(self.transcribe_audio(*args, **kwargs))