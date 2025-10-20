from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

# SQLAlchemy Base for database models
Base = declarative_base()

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


# Database Models
class TranscriptionRecord(Base):
    """Database model for storing transcription records"""
    __tablename__ = 'transcriptions'
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255))
    text = Column(Text)
    confidence = Column(Float, default=0.0)
    language = Column(String(10))
    model_used = Column(String(50), default='whisper-base')
    processing_time = Column(Float)
    file_size = Column(Integer)
    duration = Column(Float)
    segments = Column(JSON)  # Store segments as JSON
    metadata = Column(JSON)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'text': self.text,
            'confidence': self.confidence,
            'language': self.language,
            'model_used': self.model_used,
            'processing_time': self.processing_time,
            'file_size': self.file_size,
            'duration': self.duration,
            'segments': self.segments or [],
            'metadata': self.metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AudioFileRecord(Base):
    """Database model for audio file metadata"""
    __tablename__ = 'audio_files'
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False)
    original_filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    duration = Column(Float)
    sample_rate = Column(Integer)
    channels = Column(Integer, default=1)
    format = Column(String(10))  # wav, mp3, etc.
    checksum = Column(String(64))  # For duplicate detection
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed = Column(Boolean, default=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
            'channels': self.channels,
            'format': self.format,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed': self.processed
        }
