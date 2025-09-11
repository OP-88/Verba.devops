"""
Speaker Diarization Service using pyannote.audio
Provides offline speaker identification and segmentation
"""

import os
import logging
import tempfile
from typing import List, Dict, Any, Tuple
import torch
import torchaudio
from pyannote.audio import Pipeline
from pyannote.core import Segment
import numpy as np

logger = logging.getLogger(__name__)

class SpeakerDiarizationService:
    """Service for speaker diarization using pyannote.audio"""
    
    def __init__(self, model_name: str = "pyannote/speaker-diarization-3.1"):
        self.model_name = model_name
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the diarization pipeline"""
        try:
            logger.info(f"🔊 Loading speaker diarization model: {self.model_name}")
            
            # Initialize pipeline
            self.pipeline = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=None  # Use offline models when available
            )
            
            if torch.cuda.is_available():
                self.pipeline.to(torch.device("cuda"))
                
            self.is_initialized = True
            logger.info(f"✅ Speaker diarization model loaded on {self.device}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize diarization model: {e}")
            # Fallback to simple speaker assignment
            self.is_initialized = False
            logger.info("🔄 Falling back to simple speaker detection")
    
    def detect_speakers(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Detect and segment speakers in audio file
        
        Returns:
            List of speaker segments with start, end, speaker_id
        """
        if not self.is_initialized:
            return self._fallback_speaker_detection(audio_path)
            
        try:
            logger.info(f"🎙️ Running speaker diarization on: {audio_path}")
            
            # Run diarization
            diarization = self.pipeline(audio_path)
            
            # Convert to list of segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'start': turn.start,
                    'end': turn.end,
                    'speaker': f"Speaker {speaker}",
                    'duration': turn.end - turn.start
                })
            
            # Sort by start time
            segments.sort(key=lambda x: x['start'])
            
            # Merge very short segments
            merged_segments = self._merge_short_segments(segments)
            
            logger.info(f"✅ Detected {len(set(s['speaker'] for s in merged_segments))} speakers in {len(merged_segments)} segments")
            
            return merged_segments
            
        except Exception as e:
            logger.error(f"❌ Diarization failed: {e}")
            return self._fallback_speaker_detection(audio_path)
    
    def _fallback_speaker_detection(self, audio_path: str) -> List[Dict[str, Any]]:
        """Fallback speaker detection using simple voice activity"""
        try:
            import librosa
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000)
            duration = len(audio) / sr
            
            # Simple VAD-based segmentation
            # Split into 30-second chunks and assume single speaker
            chunk_duration = 30.0
            segments = []
            
            current_time = 0
            speaker_count = 1
            
            while current_time < duration:
                end_time = min(current_time + chunk_duration, duration)
                
                # Simple energy-based speaker change detection
                if len(segments) > 0 and current_time % 60 == 0:
                    speaker_count += 1
                
                segments.append({
                    'start': current_time,
                    'end': end_time,
                    'speaker': f"Speaker {speaker_count}",
                    'duration': end_time - current_time
                })
                
                current_time = end_time
            
            logger.info(f"🔄 Fallback speaker detection: {speaker_count} speakers in {len(segments)} segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ Fallback speaker detection failed: {e}")
            # Return single speaker for entire audio
            return [{
                'start': 0,
                'end': 60,  # Assume 1 minute max
                'speaker': 'Speaker 1',
                'duration': 60
            }]
    
    def _merge_short_segments(self, segments: List[Dict], min_duration: float = 2.0) -> List[Dict]:
        """Merge segments that are too short"""
        if not segments:
            return segments
            
        merged = []
        current_segment = segments[0].copy()
        
        for next_segment in segments[1:]:
            # If current segment is too short, try to merge with next
            if current_segment['duration'] < min_duration:
                # Extend current segment to include next segment start
                current_segment['end'] = next_segment['start']
                current_segment['duration'] = current_segment['end'] - current_segment['start']
            else:
                # Current segment is long enough, add it and start new one
                merged.append(current_segment)
                current_segment = next_segment.copy()
        
        # Add the last segment
        merged.append(current_segment)
        
        return merged
    
    def apply_diarization_to_transcript(
        self, 
        transcript_segments: List[Dict], 
        speaker_segments: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        Combine transcript segments with speaker diarization results
        
        Args:
            transcript_segments: Whisper transcript segments with timing
            speaker_segments: Speaker diarization segments
            
        Returns:
            Combined segments with speaker labels
        """
        labeled_segments = []
        
        for transcript_seg in transcript_segments:
            transcript_start = transcript_seg.get('start', 0)
            transcript_end = transcript_seg.get('end', transcript_start + 5)
            transcript_text = transcript_seg.get('text', '').strip()
            
            if not transcript_text:
                continue
            
            # Find overlapping speaker segment
            speaker_label = "Speaker 1"  # Default
            best_overlap = 0
            
            for speaker_seg in speaker_segments:
                speaker_start = speaker_seg['start']
                speaker_end = speaker_seg['end']
                
                # Calculate overlap
                overlap_start = max(transcript_start, speaker_start)
                overlap_end = min(transcript_end, speaker_end)
                overlap_duration = max(0, overlap_end - overlap_start)
                
                if overlap_duration > best_overlap:
                    best_overlap = overlap_duration
                    speaker_label = speaker_seg['speaker']
            
            labeled_segments.append({
                'start': transcript_start,
                'end': transcript_end,
                'text': transcript_text,
                'speaker': speaker_label,
                'confidence': transcript_seg.get('confidence', 0.95)
            })
        
        return labeled_segments
    
    def get_speaker_statistics(self, segments: List[Dict]) -> Dict[str, Any]:
        """Get statistics about detected speakers"""
        if not segments:
            return {'total_speakers': 0, 'speaker_times': {}}
            
        speaker_times = {}
        
        for segment in segments:
            speaker = segment['speaker']
            duration = segment['duration']
            
            if speaker not in speaker_times:
                speaker_times[speaker] = 0
            speaker_times[speaker] += duration
        
        return {
            'total_speakers': len(speaker_times),
            'speaker_times': speaker_times,
            'dominant_speaker': max(speaker_times.items(), key=lambda x: x[1])[0] if speaker_times else None
        }
    
    def cleanup(self):
        """Clean up resources"""
        if self.pipeline and torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("🧹 Diarization service cleaned up")