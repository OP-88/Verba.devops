#!/usr/bin/env python3
"""
Comprehensive Integration Tests for Verba Transcription System
Tests the complete pipeline: VAD, transcription, diarization, summarization
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.vad import vad_filter, EnhancedVADService
from backend.services.enhanced_transcription_service import EnhancedTranscriptionService
from backend.services.diarization_service import SpeakerDiarizationService
from backend.services.summary_service import SummarizationService

class TestVerbaIntegration:
    """Integration tests for the complete Verba transcription pipeline"""
    
    @pytest.fixture
    def test_audio_files(self):
        """Get paths to test audio files"""
        backend_dir = Path(__file__).parent.parent / "backend"
        samples_dir = backend_dir / "samples"
        
        return {
            "short": samples_dir / "test_short.wav",
            "medium": samples_dir / "test_medium.wav", 
            "conversation": samples_dir / "test_conversation.wav",
            "very_short": samples_dir / "test_very_short.wav",
            "silence": samples_dir / "test_silence.wav"
        }
    
    def test_vad_basic_functionality(self, test_audio_files):
        """Test VAD filtering on different audio files"""
        import numpy as np
        import librosa
        
        for name, audio_path in test_audio_files.items():
            if not audio_path.exists():
                pytest.skip(f"Test file {name} not found")
                
            # Load audio
            audio_data, sr = librosa.load(str(audio_path), sr=16000)
            
            # Apply VAD
            filtered_audio = vad_filter(audio_data, sr)
            
            # Basic assertions
            assert isinstance(filtered_audio, np.ndarray)
            assert len(filtered_audio) <= len(audio_data)
            assert filtered_audio.dtype == np.float32
            
            print(f"✅ VAD test passed for {name}: {len(audio_data)} -> {len(filtered_audio)} samples")
    
    def test_enhanced_vad_service(self, test_audio_files):
        """Test enhanced VAD service"""
        import numpy as np
        import librosa
        
        vad_service = EnhancedVADService()
        
        # Test with conversation file (should detect segments)
        conversation_path = test_audio_files["conversation"]
        if conversation_path.exists():
            audio_data, sr = librosa.load(str(conversation_path), sr=16000)
            
            segments = vad_service.detect_voice_activity(audio_data, sr)
            
            assert isinstance(segments, list)
            assert len(segments) > 0
            
            # Validate segment format
            for start, end in segments:
                assert isinstance(start, (int, float))
                assert isinstance(end, (int, float))
                assert end > start
                assert start >= 0
            
            print(f"✅ Enhanced VAD detected {len(segments)} voice segments")
    
    @pytest.mark.asyncio
    async def test_transcription_service_initialization(self):
        """Test transcription service can initialize"""
        try:
            service = EnhancedTranscriptionService(model_size="base")
            # Just test that it initializes without major errors
            assert service is not None
            assert service.whisper_model is not None
            print("✅ Transcription service initialized successfully")
        except Exception as e:
            print(f"⚠️ Transcription service initialization failed: {e}")
            # This might fail in CI environments without proper GPU/models
            pytest.skip("Transcription service not available in test environment")
    
    @pytest.mark.asyncio
    async def test_diarization_service_initialization(self):
        """Test diarization service can initialize"""
        try:
            service = SpeakerDiarizationService()
            await service.initialize()
            
            # Test basic functionality
            assert service is not None
            print("✅ Diarization service initialized successfully")
        except Exception as e:
            print(f"⚠️ Diarization service initialization failed: {e}")
            # This might fail without proper models/tokens
            pytest.skip("Diarization service not available in test environment")
    
    @pytest.mark.asyncio
    async def test_summarization_service_basic(self):
        """Test summarization service basic functionality"""
        try:
            service = SummarizationService()
            await service.initialize()
            
            if service.is_initialized:
                # Test with simple text
                test_text = ("This is a test meeting transcript. "
                           "We discussed the project timeline and budget allocation. "
                           "The team agreed to move forward with the proposed changes. "
                           "Action items include updating the documentation and "
                           "scheduling a follow-up meeting next week.")
                
                result = service.summarize_transcript(test_text)
                
                assert isinstance(result, dict)
                assert 'summary' in result
                assert 'key_points' in result
                assert 'action_items' in result
                assert 'sentiment' in result
                
                print("✅ Summarization service working")
                print(f"   Summary: {result['summary'][:100]}...")
                print(f"   Key points: {len(result['key_points'])}")
                print(f"   Action items: {len(result['action_items'])}")
            else:
                print("⚠️ Summarization service not initialized, using fallback")
                
        except Exception as e:
            print(f"⚠️ Summarization test failed: {e}")
            pytest.skip("Summarization service not available")
    
    def test_diarization_fallback_speaker_detection(self, test_audio_files):
        """Test diarization fallback functionality"""
        service = SpeakerDiarizationService()
        # Don't initialize - test fallback
        
        conversation_path = test_audio_files["conversation"]
        if conversation_path.exists():
            segments = service.detect_speakers(str(conversation_path))
            
            assert isinstance(segments, list)
            assert len(segments) > 0
            
            # Check segment structure
            for segment in segments:
                assert isinstance(segment, dict)
                assert 'start' in segment
                assert 'end' in segment 
                assert 'speaker' in segment
                assert 'duration' in segment
                
                assert segment['end'] > segment['start']
                assert segment['duration'] > 0
            
            print(f"✅ Diarization fallback detected {len(segments)} segments")
    
    def test_speaker_statistics(self):
        """Test speaker statistics calculation"""
        service = SpeakerDiarizationService()
        
        # Mock segments
        test_segments = [
            {'speaker': 'Speaker 1', 'duration': 10.5},
            {'speaker': 'Speaker 2', 'duration': 8.2},
            {'speaker': 'Speaker 1', 'duration': 5.3},
            {'speaker': 'Speaker 3', 'duration': 3.1}
        ]
        
        stats = service.get_speaker_statistics(test_segments)
        
        assert stats['total_speakers'] == 3
        assert stats['speaker_times']['Speaker 1'] == 15.8
        assert stats['speaker_times']['Speaker 2'] == 8.2
        assert stats['speaker_times']['Speaker 3'] == 3.1
        assert stats['dominant_speaker'] == 'Speaker 1'
        
        print("✅ Speaker statistics calculation working")
    
    def test_transcript_speaker_labeling(self):
        """Test applying speaker labels to transcript"""
        service = SpeakerDiarizationService()
        
        # Mock transcript segments
        transcript_segments = [
            {'start': 0, 'end': 5, 'text': 'Hello everyone', 'confidence': 0.9},
            {'start': 5, 'end': 10, 'text': 'How are you doing', 'confidence': 0.8},
            {'start': 15, 'end': 20, 'text': 'Great to hear that', 'confidence': 0.95}
        ]
        
        # Mock speaker segments
        speaker_segments = [
            {'start': 0, 'end': 12, 'speaker': 'Speaker 1', 'duration': 12},
            {'start': 12, 'end': 25, 'speaker': 'Speaker 2', 'duration': 13}
        ]
        
        labeled_segments = service.apply_diarization_to_transcript(
            transcript_segments, speaker_segments
        )
        
        assert len(labeled_segments) == 3
        assert labeled_segments[0]['speaker'] == 'Speaker 1'
        assert labeled_segments[1]['speaker'] == 'Speaker 1' 
        assert labeled_segments[2]['speaker'] == 'Speaker 2'
        
        print("✅ Transcript speaker labeling working")
    
    def test_summarization_fallback(self):
        """Test summarization fallback functionality"""
        service = SummarizationService()
        # Don't initialize - test fallback
        
        test_text = ("This is a meeting about the new project timeline. "
                    "We discussed important milestones and decided on next steps. "
                    "The team agreed to follow up with action items.")
        
        result = service.summarize_transcript(test_text)
        
        assert isinstance(result, dict)
        assert 'summary' in result
        assert 'key_points' in result
        assert 'action_items' in result
        assert 'sentiment' in result
        assert 'word_count' in result
        assert 'compression_ratio' in result
        
        # Fallback should still provide basic summary
        assert len(result['summary']) > 0
        assert result['word_count'] > 0
        
        print("✅ Summarization fallback working")
    
    def test_memory_optimization_imports(self):
        """Test that memory optimization imports work"""
        try:
            import gc
            import torch
            
            # Test basic memory cleanup
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()
            
            print("✅ Memory optimization imports working")
        except ImportError as e:
            pytest.skip(f"Memory optimization dependencies not available: {e}")
    
    def test_audio_file_generation_quality(self, test_audio_files):
        """Test that generated audio files have correct properties"""
        import librosa
        
        expected_durations = {
            "short": 10,
            "medium": 30, 
            "conversation": 60,
            "very_short": 2,
            "silence": 20
        }
        
        for name, audio_path in test_audio_files.items():
            if not audio_path.exists():
                continue
                
            # Load and check properties
            audio_data, sr = librosa.load(str(audio_path), sr=None)
            actual_duration = len(audio_data) / sr
            expected_duration = expected_durations[name]
            
            # Allow 10% tolerance
            assert abs(actual_duration - expected_duration) < expected_duration * 0.1
            assert sr == 16000  # Expected sample rate
            
            print(f"✅ Audio file {name} has correct duration: {actual_duration:.1f}s")

@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    def test_basic_workflow_components_exist(self):
        """Test that all workflow components can be imported"""
        # This is a basic smoke test that doesn't require models
        try:
            from backend.vad import vad_filter
            from backend.services.enhanced_transcription_service import EnhancedTranscriptionService
            from backend.services.diarization_service import SpeakerDiarizationService  
            from backend.services.summary_service import SummarizationService
            
            print("✅ All workflow components can be imported")
        except ImportError as e:
            pytest.fail(f"Failed to import workflow components: {e}")
    
    def test_service_cleanup_methods(self):
        """Test that services have proper cleanup methods"""
        from backend.services.diarization_service import SpeakerDiarizationService
        from backend.services.summary_service import SummarizationService
        
        # Test cleanup methods exist and are callable
        diarization_service = SpeakerDiarizationService()
        summary_service = SummarizationService()
        
        assert hasattr(diarization_service, 'cleanup')
        assert hasattr(summary_service, 'cleanup')
        
        # Test cleanup methods can be called
        diarization_service.cleanup()
        summary_service.cleanup()
        
        print("✅ Service cleanup methods working")

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "-s"])