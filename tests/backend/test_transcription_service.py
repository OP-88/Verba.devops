#!/usr/bin/env python3
"""
Test suite for Enhanced Transcription Service
Tests VAD, diarization, summarization, and WebSocket functionality
"""

import pytest
import asyncio
import tempfile
import os
import json
import wave
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import the modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.services.enhanced_transcription_service import (
    EnhancedTranscriptionService,
    TranscriptionResult,
    TranscriptionSegment
)

class TestEnhancedTranscriptionService:
    """Test suite for Enhanced Transcription Service"""
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a sample WAV file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            # Generate 2 seconds of sine wave audio
            sample_rate = 16000
            duration = 2.0
            frequency = 440  # A4 note
            
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio_data = np.sin(2 * np.pi * frequency * t)
            
            # Convert to int16
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(f.name, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int16.tobytes())
            
            yield f.name
            
            # Cleanup
            try:
                os.unlink(f.name)
            except:
                pass
    
    @pytest.fixture
    def transcription_service(self):
        """Create transcription service instance with mocked dependencies"""
        with patch('backend.services.enhanced_transcription_service.whisper.load_model') as mock_whisper:
            # Mock Whisper model
            mock_model = Mock()
            mock_model.transcribe.return_value = {
                'text': 'Hello, this is a test transcription.',
                'segments': [{
                    'start': 0.0,
                    'end': 2.0,
                    'text': 'Hello, this is a test transcription.',
                    'avg_logprob': -0.5
                }]
            }
            mock_whisper.return_value = mock_model
            
            service = EnhancedTranscriptionService(model_size="base")
            return service
    
    def test_service_initialization(self, transcription_service):
        """Test that the service initializes correctly"""
        assert transcription_service is not None
        assert transcription_service.whisper_model is not None
        assert transcription_service.sample_rate == 16000
        assert transcription_service.model_size == "base"
    
    def test_audio_preprocessing(self, transcription_service, sample_audio_file):
        """Test audio preprocessing functionality"""
        audio, duration = transcription_service._preprocess_audio(sample_audio_file)
        
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert duration > 0
        assert len(audio) == int(duration * transcription_service.sample_rate)
    
    @patch('backend.services.enhanced_transcription_service.torch.hub.load')
    def test_vad_service_initialization(self, mock_torch_hub):
        """Test VAD service initialization with Silero VAD"""
        # Mock successful Silero VAD loading
        mock_model = Mock()
        mock_utils = (Mock(), Mock(), Mock(), Mock(), Mock())
        mock_torch_hub.return_value = (mock_model, mock_utils)
        
        from backend.services.enhanced_transcription_service import EnhancedVADService
        vad_service = EnhancedVADService()
        
        assert vad_service.model is not None
        assert vad_service.utils is not None
        mock_torch_hub.assert_called_once()
    
    @patch('backend.services.enhanced_transcription_service.torch.hub.load')
    def test_vad_service_fallback(self, mock_torch_hub):
        """Test VAD service fallback to WebRTC when Silero fails"""
        # Mock Silero VAD failure
        mock_torch_hub.side_effect = Exception("Failed to load Silero VAD")
        
        with patch('webrtcvad.Vad') as mock_webrtc:
            mock_webrtc.return_value = Mock()
            
            from backend.services.enhanced_transcription_service import EnhancedVADService
            vad_service = EnhancedVADService()
            
            assert vad_service.model is None
            assert vad_service.fallback_vad is not None
            mock_webrtc.assert_called_once()
    
    def test_speech_detection(self, transcription_service):
        """Test speech segment detection"""
        # Create sample audio data
        sample_rate = 16000
        duration = 3.0
        audio = np.random.randn(int(sample_rate * duration)).astype(np.float32)
        
        # Mock VAD service response
        with patch.object(transcription_service.vad_service, 'detect_speech_segments') as mock_vad:
            mock_vad.return_value = [(0.5, 2.5)]
            
            segments = transcription_service.vad_service.detect_speech_segments(audio)
            
            assert len(segments) == 1
            assert segments[0] == (0.5, 2.5)
    
    @patch('backend.services.enhanced_transcription_service.Pipeline.from_pretrained')
    def test_diarization_service(self, mock_pipeline):
        """Test speaker diarization functionality"""
        # Mock diarization pipeline
        mock_diarization = Mock()
        mock_diarization.itertracks.return_value = [
            (Mock(start=0.0, end=1.0), None, "SPEAKER_00"),
            (Mock(start=1.0, end=2.0), None, "SPEAKER_01")
        ]
        mock_pipeline.return_value = mock_diarization
        
        from backend.services.enhanced_transcription_service import SpeakerDiarizationService
        diarization_service = SpeakerDiarizationService()
        
        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            segments = diarization_service.diarize_audio(temp_file.name)
            
            assert len(segments) == 2
            assert segments[0] == (0.0, 1.0, "Speaker SPEAKER_00")
            assert segments[1] == (1.0, 2.0, "Speaker SPEAKER_01")
    
    @patch('backend.services.enhanced_transcription_service.pipeline')
    def test_summarization_service(self, mock_pipeline):
        """Test text summarization functionality"""
        # Mock summarization pipeline
        mock_summarizer = Mock()
        mock_summarizer.return_value = [{
            'summary_text': 'This is a test summary.'
        }]
        mock_pipeline.return_value = mock_summarizer
        
        from backend.services.enhanced_transcription_service import SummarizationService
        summarization_service = SummarizationService()
        
        test_text = "This is a long text that needs to be summarized. " * 10
        summary = summarization_service.summarize_text(test_text)
        
        assert summary == "This is a test summary."
        mock_summarizer.assert_called_once()
    
    def test_segment_speaker_merging(self, transcription_service):
        """Test merging transcription segments with speaker information"""
        # Create test segments
        transcription_segments = [
            TranscriptionSegment(start_time=0.0, end_time=1.0, text="Hello", confidence=0.9),
            TranscriptionSegment(start_time=1.0, end_time=2.0, text="World", confidence=0.8)
        ]
        
        speaker_segments = [
            (0.0, 1.5, "Speaker 1"),
            (1.5, 2.0, "Speaker 2")
        ]
        
        merged_segments = transcription_service._merge_segments_with_speakers(
            transcription_segments, speaker_segments
        )
        
        assert len(merged_segments) == 2
        assert merged_segments[0].speaker == "Speaker 1"
        assert merged_segments[1].speaker == "Speaker 2"
    
    def test_complete_transcription_workflow(self, transcription_service, sample_audio_file):
        """Test complete transcription workflow"""
        with patch.object(transcription_service.vad_service, 'detect_speech_segments') as mock_vad:
            mock_vad.return_value = [(0.0, 2.0)]
            
            with patch.object(transcription_service.diarization_service, 'diarize_audio') as mock_diarization:
                mock_diarization.return_value = [(0.0, 2.0, "Speaker 1")]
                
                with patch.object(transcription_service.summarization_service, 'summarize_text') as mock_summarization:
                    mock_summarization.return_value = "Test summary"
                    
                    result = transcription_service.transcribe_audio(sample_audio_file)
                    
                    assert isinstance(result, TranscriptionResult)
                    assert result.text == "Hello, this is a test transcription."
                    assert result.summary == "Test summary"
                    assert len(result.segments) == 1
                    assert result.processing_time > 0
                    assert result.audio_duration > 0
    
    @pytest.mark.asyncio
    async def test_streaming_transcription(self, transcription_service, sample_audio_file):
        """Test streaming transcription functionality"""
        results = []
        
        with patch.object(transcription_service, 'transcribe_audio') as mock_transcribe:
            mock_result = TranscriptionResult(
                text="Test transcription",
                summary="Test summary",
                segments=[TranscriptionSegment(start_time=0.0, end_time=2.0, text="Test", confidence=0.9)],
                speakers=["Speaker 1"],
                processing_time=1.0,
                audio_duration=2.0,
                model_info={"whisper_model": "base"},
                quality_metrics={"speech_ratio": 0.8, "avg_confidence": 0.9, "processing_speed": 2.0}
            )
            mock_transcribe.return_value = mock_result
            
            async for result in transcription_service.transcribe_audio_stream(sample_audio_file):
                results.append(result)
            
            assert len(results) >= 2  # At least one segment and one final result
            assert any(r["type"] == "segment" for r in results)
            assert any(r["type"] == "final" for r in results)
    
    def test_service_statistics(self, transcription_service):
        """Test service statistics tracking"""
        stats = transcription_service.get_service_stats()
        
        assert "transcriptions_completed" in stats
        assert "total_audio_duration" in stats
        assert "total_processing_time" in stats
        assert "services_available" in stats
        assert "model_info" in stats
        
        # Check initial values
        assert stats["transcriptions_completed"] == 0
        assert stats["total_audio_duration"] == 0.0
        assert stats["total_processing_time"] == 0.0

class TestVADService:
    """Test VAD Service specifically"""
    
    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio for VAD testing"""
        sample_rate = 16000
        duration = 3.0
        
        # Create audio with speech-like characteristics
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Mix of frequencies to simulate speech
        audio = (
            0.3 * np.sin(2 * np.pi * 200 * t) +  # Low frequency
            0.3 * np.sin(2 * np.pi * 800 * t) +  # Mid frequency
            0.2 * np.sin(2 * np.pi * 2000 * t)   # High frequency
        )
        
        # Add silence periods
        audio[:sample_rate//2] = 0  # First 0.5s silence
        audio[-sample_rate//2:] = 0  # Last 0.5s silence
        
        return audio.astype(np.float32)
    
    def test_webrtc_vad_detection(self, sample_audio):
        """Test WebRTC VAD detection"""
        with patch('webrtcvad.Vad') as mock_vad_class:
            mock_vad = Mock()
            mock_vad.is_speech.side_effect = lambda frame, sr: len(frame) > 0 and np.frombuffer(frame, dtype=np.int16).std() > 1000
            mock_vad_class.return_value = mock_vad
            
            from services.enhanced_transcription_service import EnhancedVADService
            vad_service = EnhancedVADService()
            vad_service.model = None  # Force fallback to WebRTC
            
            segments = vad_service._webrtc_vad_detection(sample_audio)
            
            assert isinstance(segments, list)
            assert all(isinstance(seg, tuple) and len(seg) == 2 for seg in segments)

# Integration tests for WebSocket functionality
@pytest.mark.asyncio
class TestWebSocketIntegration:
    """Test WebSocket transcription endpoints"""
    
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        # Mock WebSocket connection
        mock_ws = AsyncMock()
        mock_ws.query_params = {"client_id": "test_client"}
        
        from api.websocket_routes import ConnectionManager
        manager = ConnectionManager()
        
        await manager.connect(mock_ws, "test_client")
        
        assert mock_ws in manager.active_connections
        assert "test_client" in [session["client_id"] for session in manager.connection_sessions.values()]
    
    async def test_websocket_message_handling(self):
        """Test WebSocket message processing"""
        from api.websocket_routes import handle_audio_chunk
        
        mock_ws = AsyncMock()
        test_message = {
            "type": "audio_chunk",
            "data": "UklGRiQAAABXQVZFZm10IBAAAAABAAEAwF0AAIC7AAACABAAZGF0YQAAAAAA",  # Empty WAV
            "chunk_id": "test_chunk",
            "sample_rate": 16000,
            "format": "wav"
        }
        
        with patch('api.websocket_routes.transcription_service') as mock_service:
            mock_result = Mock()
            mock_result.text = "Test transcription"
            mock_result.segments = []
            mock_result.speakers = []
            mock_result.processing_time = 1.0
            mock_result.audio_duration = 1.0
            mock_result.quality_metrics = {"speech_ratio": 0.8}
            
            mock_service.transcribe_audio.return_value = mock_result
            
            await handle_audio_chunk(mock_ws, test_message)
            
            # Verify WebSocket response was sent
            mock_ws.send_text.assert_called()

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])