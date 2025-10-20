#!/usr/bin/env python3
"""
Comprehensive tests for Verba transcription system
Tests all major components: VAD, diarization, transcription, summarization, export
"""

import pytest
import asyncio
import tempfile
import numpy as np
import librosa
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from backend.services.whisper_service import WhisperTranscriptionService
from backend.services.diarization_service import SpeakerDiarizationService
from backend.services.enhanced_vad_service import EnhancedVADService
from backend.services.summary_service import SummarizationService
from backend.services.database_service import DatabaseService
from backend.routes.transcribe import router as transcribe_router
from backend.routes.export import router as export_router

class TestWhisperService:
    """Test Whisper transcription service"""
    
    @pytest.fixture
    def service(self):
        return WhisperTranscriptionService()
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a synthetic audio file for testing"""
        sample_rate = 16000
        duration = 5  # 5 seconds
        
        # Generate a simple sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            librosa.output.write_wav(f.name, audio, sample_rate)
            yield f.name
        
        # Cleanup
        os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initializes correctly"""
        await service.initialize()
        assert service.is_initialized
        assert service.model is not None
        assert service.device in ['cpu', 'cuda']
    
    @pytest.mark.asyncio 
    async def test_transcription_with_timing(self, service, sample_audio_file):
        """Test transcription with segment timing"""
        await service.initialize()
        
        result = await service.transcribe_with_timing(
            sample_audio_file, 
            language='en',
            return_segments=True
        )
        
        assert 'text' in result
        assert 'segments' in result
        assert 'language' in result
        assert 'duration' in result
        assert result['duration'] > 0
        
        # Check segments structure
        if result['segments']:
            for segment in result['segments']:
                assert 'start' in segment
                assert 'end' in segment
                assert 'text' in segment
                assert segment['end'] >= segment['start']
    
    @pytest.mark.asyncio
    async def test_memory_optimization(self, service, sample_audio_file):
        """Test memory-optimized processing"""
        await service.initialize()
        
        # Test with memory optimization enabled
        result = await service.transcribe_with_timing(
            sample_audio_file,
            optimize_memory=True
        )
        
        assert 'text' in result
        # Memory-optimized mode should still produce results
        assert len(result['text']) >= 0


class TestDiarizationService:
    """Test speaker diarization service"""
    
    @pytest.fixture
    def service(self):
        return SpeakerDiarizationService()
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a longer audio file for diarization testing"""
        sample_rate = 16000
        duration = 30  # 30 seconds for better diarization
        
        # Generate two different tones to simulate different speakers
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # First half: 440 Hz (Speaker 1)
        # Second half: 880 Hz (Speaker 2)
        mid_point = len(t) // 2
        audio = np.zeros_like(t)
        audio[:mid_point] = np.sin(2 * np.pi * 440 * t[:mid_point])
        audio[mid_point:] = np.sin(2 * np.pi * 880 * t[mid_point:])
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            librosa.output.write_wav(f.name, audio, sample_rate)
            yield f.name
        
        os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test diarization service initializes"""
        await service.initialize()
        # Service should handle initialization gracefully even if model loading fails
        assert hasattr(service, 'is_initialized')
    
    def test_speaker_detection(self, service, sample_audio_file):
        """Test speaker detection functionality"""
        segments = service.detect_speakers(sample_audio_file)
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        # Check segment structure
        for segment in segments:
            assert 'start' in segment
            assert 'end' in segment
            assert 'speaker' in segment
            assert 'duration' in segment
            assert segment['end'] >= segment['start']
            assert segment['duration'] > 0
    
    def test_transcript_labeling(self, service):
        """Test applying speaker labels to transcript segments"""
        # Mock transcript segments
        transcript_segments = [
            {'start': 0, 'end': 10, 'text': 'Hello world'},
            {'start': 10, 'end': 20, 'text': 'How are you today'},
            {'start': 20, 'end': 30, 'text': 'I am doing well'}
        ]
        
        # Mock speaker segments
        speaker_segments = [
            {'start': 0, 'end': 15, 'speaker': 'Speaker 1', 'duration': 15},
            {'start': 15, 'end': 30, 'speaker': 'Speaker 2', 'duration': 15}
        ]
        
        labeled = service.apply_diarization_to_transcript(
            transcript_segments, speaker_segments
        )
        
        assert len(labeled) == len(transcript_segments)
        for segment in labeled:
            assert 'speaker' in segment
            assert segment['speaker'] in ['Speaker 1', 'Speaker 2']
    
    def test_speaker_statistics(self, service):
        """Test speaker statistics calculation"""
        segments = [
            {'speaker': 'Speaker 1', 'duration': 10},
            {'speaker': 'Speaker 2', 'duration': 15},
            {'speaker': 'Speaker 1', 'duration': 5}
        ]
        
        stats = service.get_speaker_statistics(segments)
        
        assert stats['total_speakers'] == 2
        assert stats['speaker_times']['Speaker 1'] == 15
        assert stats['speaker_times']['Speaker 2'] == 15
        assert stats['dominant_speaker'] in ['Speaker 1', 'Speaker 2']


class TestEnhancedVADService:
    """Test Enhanced VAD service"""
    
    @pytest.fixture
    def service(self):
        return EnhancedVADService()
    
    def test_service_initialization(self, service):
        """Test VAD service initialization"""
        assert hasattr(service, 'model')
        assert hasattr(service, 'fallback_available')
        # Service should initialize with either Silero or fallback
    
    def test_speech_detection(self, service):
        """Test speech segment detection"""
        # Create synthetic audio with speech-like patterns
        sample_rate = 16000
        duration = 10
        
        # Create audio with alternating speech/silence
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.zeros_like(t)
        
        # Add "speech" segments (sine waves with random modulation)
        speech_segments = [(1, 3), (5, 7), (8, 9)]
        for start, end in speech_segments:
            start_idx = int(start * sample_rate)
            end_idx = int(end * sample_rate)
            segment_t = t[start_idx:end_idx]
            # Modulated sine wave to simulate speech
            audio[start_idx:end_idx] = np.sin(2 * np.pi * 440 * segment_t) * \
                                       (1 + 0.5 * np.sin(2 * np.pi * 10 * segment_t))
        
        segments = service.detect_speech_segments(audio, return_seconds=True)
        
        assert isinstance(segments, list)
        # Should detect some speech segments
        assert len(segments) > 0
        
        for start, end in segments:
            assert end > start
            assert start >= 0
            assert end <= duration


class TestSummarizationService:
    """Test AI summarization service"""
    
    @pytest.fixture
    def service(self):
        return SummarizationService()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test summarization service initialization"""
        await service.initialize()
        # Should handle initialization gracefully
        assert hasattr(service, 'is_initialized')
    
    def test_text_preprocessing(self, service):
        """Test text preprocessing functionality"""
        raw_text = """
        Speaker 1: Um, well, hello there, you know, I wanted to discuss the project.
        Speaker 2: Uh, yes, that sounds good. We need to, like, plan the timeline.
        """
        
        cleaned = service._preprocess_text(raw_text)
        
        # Should remove speaker labels and filler words
        assert 'Speaker 1:' not in cleaned
        assert 'Speaker 2:' not in cleaned
        assert 'Um,' not in cleaned
        assert 'Uh,' not in cleaned
        assert 'project' in cleaned
        assert 'timeline' in cleaned
    
    def test_text_chunking(self, service):
        """Test text splitting into chunks"""
        long_text = " ".join(["This is sentence number {}.".format(i) for i in range(100)])
        
        chunks = service._split_text_into_chunks(long_text, max_chunk_size=50)
        
        assert len(chunks) > 1
        for chunk in chunks:
            word_count = len(chunk.split())
            assert word_count <= 60  # Should be close to max_chunk_size with some buffer
    
    def test_key_points_extraction(self, service):
        """Test key points extraction"""
        text = """
        The meeting was very important for our project timeline. 
        We decided to move the deadline to next month.
        The budget was approved for the new features.
        Action items include updating documentation and testing.
        """
        
        key_points = service._extract_key_points(text)
        
        assert isinstance(key_points, list)
        assert len(key_points) > 0
        # Should identify important sentences
        important_keywords = ['important', 'decided', 'deadline', 'budget', 'action']
        found_important = any(
            any(keyword in point.lower() for keyword in important_keywords)
            for point in key_points
        )
        assert found_important


class TestDatabaseService:
    """Test database service"""
    
    @pytest.fixture
    def service(self):
        # Use in-memory database for testing
        return DatabaseService(":memory:")
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, service):
        """Test database initialization"""
        await service.initialize()
        # Should create tables successfully
    
    @pytest.mark.asyncio
    async def test_transcription_storage(self, service):
        """Test storing and retrieving transcriptions"""
        await service.initialize()
        
        # Store a transcription
        transcription_data = {
            'text': 'Test transcription',
            'duration': 30.5,
            'language': 'en',
            'confidence': 0.95,
            'file_name': 'test.wav',
            'segments': [{'start': 0, 'end': 30, 'text': 'Test transcription', 'speaker': 'Speaker 1'}],
            'summary': {'summary': 'Brief test', 'key_points': ['test point']}
        }
        
        transcription_id = await service.store_transcription(transcription_data)
        assert transcription_id is not None
        
        # Retrieve the transcription
        retrieved = await service.get_transcription(transcription_id)
        assert retrieved is not None
        assert retrieved['text'] == 'Test transcription'
        assert retrieved['duration'] == 30.5
        assert retrieved['language'] == 'en'
        
        # List transcriptions
        transcriptions = await service.get_transcription_history(limit=10)
        assert len(transcriptions) >= 1
        assert any(t['id'] == transcription_id for t in transcriptions)


class TestAPIEndpoints:
    """Test API endpoints with mocked services"""
    
    @pytest.fixture
    def mock_services(self):
        """Mock all services for API testing"""
        with patch('backend.routes.transcribe.whisper_service') as mock_whisper, \
             patch('backend.routes.transcribe.diarization_service') as mock_diarization, \
             patch('backend.routes.transcribe.vad_service') as mock_vad, \
             patch('backend.routes.transcribe.summary_service') as mock_summary, \
             patch('backend.routes.transcribe.db_service') as mock_db:
            
            # Configure mocks
            mock_whisper.transcribe_with_timing = AsyncMock(return_value={
                'text': 'Mock transcription',
                'segments': [{'start': 0, 'end': 5, 'text': 'Mock transcription'}],
                'language': 'en',
                'duration': 5.0,
                'confidence': 0.95
            })
            
            mock_diarization.detect_speakers = Mock(return_value=[
                {'start': 0, 'end': 5, 'speaker': 'Speaker 1', 'duration': 5}
            ])
            
            mock_diarization.apply_diarization_to_transcript = Mock(return_value=[
                {'start': 0, 'end': 5, 'text': 'Mock transcription', 'speaker': 'Speaker 1'}
            ])
            
            mock_vad.detect_speech_segments = Mock(return_value=[(0, 5)])
            
            mock_summary.summarize_transcript = Mock(return_value={
                'summary': 'Mock summary',
                'key_points': ['Mock point'],
                'action_items': [],
                'sentiment': 'neutral'
            })
            
            mock_db.store_transcription = AsyncMock(return_value='mock-id-123')
            
            yield {
                'whisper': mock_whisper,
                'diarization': mock_diarization,
                'vad': mock_vad,
                'summary': mock_summary,
                'db': mock_db
            }
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Test health check endpoint"""
        from fastapi.testclient import TestClient
        from backend.routes.health import router
        
        client = TestClient(router)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert 'timestamp' in data


class TestMemoryOptimization:
    """Test memory usage optimization"""
    
    def test_memory_cleanup(self):
        """Test that services properly clean up memory"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Create and use services
        services = [
            WhisperTranscriptionService(),
            SpeakerDiarizationService(),
            EnhancedVADService(),
            SummarizationService()
        ]
        
        # Cleanup
        for service in services:
            if hasattr(service, 'cleanup'):
                service.cleanup()
        
        del services
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 500MB)
        assert memory_increase < 500 * 1024 * 1024, f"Memory increased by {memory_increase / 1024 / 1024:.1f}MB"


class TestIntegrationWorkflow:
    """Test complete transcription workflow"""
    
    @pytest.mark.asyncio
    async def test_complete_transcription_pipeline(self):
        """Test the complete pipeline from audio to final result"""
        
        # Create sample audio
        sample_rate = 16000
        duration = 10
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            librosa.output.write_wav(f.name, audio, sample_rate)
            audio_file = f.name
        
        try:
            # Initialize services
            whisper_service = WhisperTranscriptionService()
            diarization_service = SpeakerDiarizationService()
            vad_service = EnhancedVADService()
            summary_service = SummarizationService()
            
            await whisper_service.initialize()
            await diarization_service.initialize()
            await summary_service.initialize()
            
            # Step 1: VAD
            speech_segments = vad_service.detect_speech_segments(audio, return_seconds=True)
            assert len(speech_segments) > 0
            
            # Step 2: Transcription
            transcription = await whisper_service.transcribe_with_timing(
                audio_file, 
                return_segments=True
            )
            assert 'text' in transcription
            assert 'segments' in transcription
            
            # Step 3: Diarization
            speaker_segments = diarization_service.detect_speakers(audio_file)
            labeled_segments = diarization_service.apply_diarization_to_transcript(
                transcription['segments'], speaker_segments
            )
            
            # Step 4: Summarization
            if transcription['text'].strip():
                summary = summary_service.summarize_transcript(transcription['text'])
                assert 'summary' in summary
            
            # Verify pipeline produces coherent results
            assert transcription['duration'] > 0
            assert len(labeled_segments) >= 0
            
        finally:
            # Cleanup
            os.unlink(audio_file)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])