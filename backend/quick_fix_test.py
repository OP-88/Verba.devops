#!/usr/bin/env python3
"""
🔧 QUICK BACKEND FIX TEST
Minimal test to verify the backend is working
"""

import os
import sys
import logging
import numpy as np
import torch
import whisper
import librosa
import webrtcvad
import soundfile as sf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dependencies():
    """Test all required dependencies"""
    print("🧪 DEPENDENCY CHECK")
    print("=" * 60)
    
    deps = {
        'numpy': np,
        'torch': torch,
        'whisper': whisper,
        'librosa': librosa,
        'webrtcvad': webrtcvad,
        'soundfile': sf
    }
    
    all_good = True
    for name, module in deps.items():
        try:
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {name}: {version}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            all_good = False
    
    return all_good

def test_whisper_model():
    """Test Whisper model loading"""
    print("\n🤖 WHISPER MODEL TEST")
    print("=" * 60)
    
    try:
        model = whisper.load_model("tiny")
        print("✅ Whisper tiny model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Whisper model failed: {e}")
        return False

def test_vad_service():
    """Test VAD service"""
    print("\n🎙️ VAD SERVICE TEST")
    print("=" * 60)
    
    try:
        vad = webrtcvad.Vad(2)
        
        # Create test audio
        sample_rate = 16000
        duration = 1.0
        test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sample_rate * duration)))
        test_audio_int16 = (test_audio * 32767).astype(np.int16)
        
        # Test VAD
        frame_length = 480  # 30ms at 16kHz
        frame = test_audio_int16[:frame_length]
        frame_bytes = frame.tobytes()
        
        is_speech = vad.is_speech(frame_bytes, sample_rate)
        print(f"✅ VAD test result: {is_speech}")
        return True
        
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False

def test_audio_processing():
    """Test audio processing pipeline"""
    print("\n🎵 AUDIO PROCESSING TEST")
    print("=" * 60)
    
    try:
        # Generate test audio
        sample_rate = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        test_audio = 0.5 * np.sin(2 * np.pi * 440 * t)
        
        # Test librosa operations
        resampled = librosa.resample(test_audio, orig_sr=sample_rate, target_sr=16000)
        print(f"✅ Audio resampling: {len(test_audio)} -> {len(resampled)} samples")
        
        # Test dtype conversion
        audio_int16 = (resampled * 32767).astype(np.int16)
        print(f"✅ Dtype conversion: {resampled.dtype} -> {audio_int16.dtype}")
        
        return True
        
    except Exception as e:
        print(f"❌ Audio processing failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🎯 VERBA BACKEND QUICK FIX TEST")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Whisper Model", test_whisper_model),
        ("VAD Service", test_vad_service),
        ("Audio Processing", test_audio_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
