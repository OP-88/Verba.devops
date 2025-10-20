#!/usr/bin/env python3
"""
Basic backend functionality tests
Quick tests to verify core functionality without heavy model downloads
"""

import pytest
import sys
import os
import tempfile
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_backend_imports():
    """Test that all backend modules can be imported"""
    try:
        import backend.vad
        import backend.services.database_service
        import backend.services.diarization_service
        import backend.services.summary_service
        import backend.services.enhanced_transcription_service
        assert True
    except ImportError as e:
        pytest.fail(f"Backend import failed: {e}")

def test_vad_module():
    """Test VAD module basic functionality"""
    from backend.vad import vad_filter, EnhancedVADService
    
    # Test basic VAD filter with dummy data
    sample_rate = 16000
    duration = 2.0
    audio_data = np.random.randn(int(sample_rate * duration)).astype(np.float32)
    
    # Test VAD filter
    filtered_audio = vad_filter(audio_data, sample_rate)
    assert isinstance(filtered_audio, np.ndarray)
    assert len(filtered_audio) <= len(audio_data)  # Should be same or smaller

def test_database_models():
    """Test database model creation"""
    from backend.models.transcription_models import TranscriptionRecord, AudioFileRecord, Base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Test in-memory database
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Create test records
    audio_record = AudioFileRecord(
        filename='test.wav',
        original_filename='test.wav',
        file_size=1024,
        duration=10.0,
        sample_rate=16000
    )
    
    transcription_record = TranscriptionRecord(
        filename='test.wav',
        text='Hello world',
        confidence=0.9,
        language='en',
        processing_time=2.5
    )
    
    session.add(audio_record)
    session.add(transcription_record)
    session.commit()
    
    # Verify records
    assert session.query(AudioFileRecord).count() == 1
    assert session.query(TranscriptionRecord).count() == 1
    
    session.close()

def test_configuration():
    """Test configuration settings"""
    from backend.config.settings import settings
    
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'api_host')
    assert hasattr(settings, 'api_port')
    assert hasattr(settings, 'whisper_model')
    assert hasattr(settings, 'cors_origins')
    
    # Test default values
    assert settings.api_port == 8000
    assert settings.whisper_model == 'base'
    assert isinstance(settings.cors_origins, list)

def test_transcription_models():
    """Test transcription data models"""
    from backend.models.transcription_models import TranscriptionResult
    
    result = TranscriptionResult(
        success=True,
        text="Hello world",
        confidence=0.9,
        language="en",
        segments=[{"start": 0.0, "end": 2.0, "text": "Hello world"}],
        processing_stats={"duration": 2.0, "model": "base"}
    )
    
    assert result.success == True
    assert result.text == "Hello world"
    assert result.confidence == 0.9
    assert len(result.segments) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])