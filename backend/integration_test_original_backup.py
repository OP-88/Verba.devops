import fix_numpy_dtype
#!/usr/bin/env python3
"""
Quick Integration Test for Enhanced Transcription Service
Tests basic functionality with minimal setup
"""

import sys
import time
import numpy as np
import soundfile as sf
from pathlib import Path

def create_test_audio():
    """Create a simple test audio file"""
    print("🎵 Creating test audio file...")
    
    # Generate 10 seconds of test audio
    sample_rate = 16000
    duration = 10.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create speech-like segments (sine waves)
    audio = np.zeros_like(t)
    
    # Add some "speech" segments
    for start in [1, 4, 7]:  # Speech at 1s, 4s, 7s
        segment_start = int(start * sample_rate)
        segment_end = int((start + 2) * sample_rate)
        
        if segment_end <= len(audio):
            # Create formant-like frequencies
            segment_t = t[segment_start:segment_end]
            speech = (
                0.3 * np.sin(2 * np.pi * 200 * segment_t) +
                0.2 * np.sin(2 * np.pi * 400 * segment_t) +
                0.1 * np.sin(2 * np.pi * 800 * segment_t)
            )
            audio[segment_start:segment_end] = speech
    
    # Add some noise
    audio += 0.02 * np.random.randn(len(audio))
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    # Save to file
    test_file = "quick_test_audio.wav"
    sf.write(test_file, audio, sample_rate)
    
    print(f"✅ Test audio created: {test_file} ({duration}s)")
    return test_file

def test_vad_only():
    """Test just the VAD service"""
    print("\n🧪 Testing VAD Service Only...")
    
    try:
        from vad_service import VADService
        
        # Initialize VAD
        vad = VADService(aggressiveness=2)
        print("✅ VAD Service initialized")
        
        # Create test audio
        test_file = create_test_audio()
        
        # Load and process audio
        import librosa
        audio, sr = librosa.load(test_file, sr=16000)
        
        print(f"📊 Audio loaded: {len(audio)/sr:.1f}s")
        
        # Process with VAD
        start_time = time.time()
        result = vad.process_audio(audio, sr)
        vad_time = time.time() - start_time
        
        if result['success']:
            segments = result['voice_segments']
            total_speech = sum(seg['duration'] for seg in segments)
            
            print(f"✅ VAD processed in {vad_time:.2f}s")
            print(f"📊 Found {len(segments)} voice segments")
            print(f"🗣️ Total speech: {total_speech:.2f}s")
            print(f"📈 Speech ratio: {total_speech/(len(audio)/sr):.1%}")
            
            return True
        else:
            print("❌ VAD processing failed")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure vad_service.py exists in the current directory")
        return False
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False

def test_whisper_loading():
    """Test Whisper model loading"""
    print("\n🧪 Testing Whisper Model Loading...")
    
    try:
        import whisper
        
        print("Loading Whisper tiny model...")
        start_time = time.time()
        model = whisper.load_model("tiny")
        load_time = time.time() - start_time
        
        print(f"✅ Whisper model loaded in {load_time:.2f}s")
        
        # Test transcription with dummy audio
        dummy_audio = np.random.randn(16000)  # 1 second of noise
        result = model.transcribe(dummy_audio)
        
        print(f"✅ Whisper transcription test completed")
        print(f"📝 Sample output: '{result['text'][:50]}...'")
        
        return True
        
    except ImportError:
        print("❌ Whisper not installed. Install with: pip install openai-whisper")
        return False
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False

def test_enhanced_service():
    """Test the complete Enhanced Transcription Service"""
    print("\n🧪 Testing Enhanced Transcription Service...")
    
    try:
        from enhanced_transcription_service import EnhancedTranscriptionService
        
        # Initialize service
        print("Initializing Enhanced Transcription Service...")
        service = EnhancedTranscriptionService(
            model_name="openai/whisper-tiny",  # Use tiny for quick testing
            vad_aggressiveness=2
        )
        
        # Load model
        print("Loading Whisper model...")
        if not service.load_whisper_model():
            print("❌ Failed to load model")
            return False
        
        print("✅ Service initialized successfully")
        
        # Create test audio if needed
        test_file = "quick_test_audio.wav"
        if not Path(test_file).exists():
            test_file = create_test_audio()
        
        # Run transcription
        print(f"🎯 Running transcription on {test_file}...")
        start_time = time.time()
        
        result = service.transcribe_file(test_file)
        
        total_time = time.time() - start_time
        
        # Display results
        print(f"✅ Transcription completed in {total_time:.2f}s")
        print(f"📝 Text: '{result.text[:100]}...'")
        print(f"⏱️  Total duration: {result.total_duration:.2f}s")
        print(f"🗣️  Speech duration: {result.speech_duration:.2f}s")
        print(f"📊 Speech ratio: {result.speech_ratio:.1%}")
        print(f"⚡ Processing speed: {result.processing_stats.get('processing_speed_ratio', 0):.2f}x")
        print(f"📈 Efficiency gain: {result.processing_stats.get('efficiency_gain', 0):.1%}")
        
        # Show service stats
        stats = service.get_service_stats()
        print(f"📈 Service processed {stats['total_files_processed']} files")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure enhanced_transcription_service.py exists")
        return False
    except Exception as e:
        print(f"❌ Enhanced service test failed: {e}")
        return False

def main():
    """Run quick integration tests"""
    print("🚀 QUICK INTEGRATION TEST")
    print("=" * 50)
    print("Testing Enhanced Transcription Service components...")
    
    tests = [
        ("VAD Service", test_vad_only),
        ("Whisper Loading", test_whisper_loading),
        ("Enhanced Service", test_enhanced_service)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            success = test_func()
            results.append((test_name, success))
        except KeyboardInterrupt:
            print("\n⏹️ Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Enhanced Transcription Service is ready to use!")
        print("\nNext steps:")
        print("1. Run the full test suite: python test_enhanced_transcription.py")
        print("2. Integrate with your main Verba application")
        print("3. Add audio format support")
    else:
        print(f"\n⚠️ {total-passed} tests failed")
        print("🔧 Review the errors above and fix issues before proceeding")
    
    # Cleanup
    test_file = "quick_test_audio.wav"
    if Path(test_file).exists():
        Path(test_file).unlink()
        print(f"🧹 Cleaned up {test_file}")

if __name__ == "__main__":
    main()
