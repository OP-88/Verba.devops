from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class AudioSegment:
    """Represents a segment of audio with speech content"""
    audio_data: np.ndarray
    start_time: float  # Start time in seconds
    end_time: float    # End time in seconds
    sample_rate: int   # Sample rate of audio data
    segment_id: int    # Unique identifier for this segment
    
    @property
    def duration(self) -> float:
        """Duration of the segment in seconds"""
        return self.end_time - self.start_time
    
    @property
    def sample_count(self) -> int:
        """Number of audio samples in this segment"""
        return len(self.audio_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding audio data)"""
        return {
            'segment_id': self.segment_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'sample_count': self.sample_count
        }

@dataclass
class TranscriptionResult:
    """Complete transcription result with metadata"""
    success: bool
    text: Optional[str] = None
    confidence: float = 0.0
    language: Optional[str] = None
    segments: List[Dict[str, Any]] = None
    processing_stats: Dict[str, Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.segments is None:
            self.segments = []
        if self.processing_stats is None:
            self.processing_stats = {}
