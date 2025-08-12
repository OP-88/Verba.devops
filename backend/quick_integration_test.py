"""
Fixed Quick Integration Test
Resolves NumPy 2.x compatibility issues with VAD and Whisper
"""
import os
import sys
import time
import numpy as np
import logging
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def create_compatible_test_audio(filename: str = "integration_test_audio.wav", duration: float = 10.0):
    """Create test audio with NumPy 2.x compatibility"""
    try:
        import soundfile as sf
        
        sample_rate = 16000
        # Use explicit dtype keyword to avoid position argument error
        t = np.linspace(0, duration, int(duration * sample_rate), dtype=np.float32)
        
        # Create audio with multiple voice segments
        audio = np.zeros(len(t), dtype=np.float32)  # Explicit dtype keyword
        
        # Voice segment 1: 1-3 seconds (human speech simulation)
        voice1_start, voice1_end = int(1.0 * sample_rate), int(3.0 * sample_rate)
        voice1_t = t[voice1_start:voice1_end]
        audio[voice1_start:voice1_end] = 0.3 * (
            np.sin(2 * np.pi * 150 * voice1_t) + 
            0.5 * np.sin(2 * np.pi * 300 * voice1_t)
        )
        
        # Voice segment 2: 5-7 seconds
        voice2_start, voice2_end = int(5.0 * sample_rate), int(7.0 * sample_rate)
        voice2_t = t[voice2_start:voice2_end]
        audio[voice2_start:voice2_end] = 0.3 * (
            np.sin(2 * np.pi * 200 * voice2_t) + 
            0.3 * np.sin(2 * np.pi * 400 * voice2_t)
        )
        
        # Add realistic background noise
        noise = 0.02 * np.random.randn(len(audio)).astype(np.float32)
        audio += noise
        
        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save audio file
        sf.write(filename, audio, sample_rate)
        print(f"✅ Test audio created: {filename} ({duration}s)")
        return filename
        
    except Exception as e:
        print(f"❌ Audio creation failed: {e}")
        raise

def test_vad_service_only():
    """Test VAD service in isolation"""
    print("\n🧪 Testing VAD Service Only...")
    
    try:
        # Import the fixed VAD service
        from vad_service import CompatibleVADService
        print("✅ VAD Service imported successfully")
        
        # Initialize VAD
        vad = CompatibleVADService(aggressiveness=2)
        print("✅ VAD Service initialized")
        
        # Create test audio
        test_file = create_compatible_test_audio("vad_only_test.wav", 10.0)
        
        # Process with VAD
        result = vad.process_audio_file(test_file)
        
        if result['success']:
            print("✅ VAD processing successful")
            print(f"📊 Voice segments detected: {result['num_segments']}")
            print(f"🗣️ Speech ratio: {result['speech_ratio']:.1f}%")
            print(f"⏱️ Processing time: {result['processing_time']:.3f}s")
            
            # Show segments
            for i, segment in enumerate(result['segments'], 1):
                print(f"   Segment {i}: {segment.start_time:.2f}-{segment.end_time:.2f}s")
        else:
            print(f"❌ VAD processing failed: {result.get('error')}")
            return False
            
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
        return True
        
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        return False

def test_whisper_loading():
    """Test Whisper model loading with dtype fixes"""
    print("\n🧪 Testing Whisper Model Loading...")
    
    try:
        import torch
        import whisper
        
        # Check if we're using CPU and apply dtype fix
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {device}")
        
        # Force CPU to use float32 to avoid dtype conflicts
        if device == "cpu":
            torch.set_default_dtype(torch.float32)
        
        print("Loading Whisper tiny model...")
        start_time = time.time()
        
        # Load model with explicit dtype handling
        model = whisper.load_model("tiny", device=device)
        
        # Force model to float32 on CPU to avoid dtype mismatch
        if device == "cpu":
            model = model.float()
        
        load_time = time.time() - start_time
        print(f"✅ Whisper model loaded in {load_time:.2f}s")
        
        # Test basic inference with proper audio format
        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence
        
        # Ensure audio is in correct format for Whisper
        if test_audio.dtype != np.float32:
            test_audio = test_audio.astype(np.float32)
        
        # Test transcription
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = model.transcribe(test_audio, fp16=False)  # Force fp32
        
        print("✅ Basic Whisper transcription test passed")
        return True
        
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False

def test_enhanced_service():
    """Test the full enhanced transcription service"""
    print("\n🧪 Testing Enhanced Transcription Service...")
    
    try:
        # Import enhanced service
        sys.path.insert(0, '.')
        from enhanced_transcription_service import EnhancedTranscriptionService
        
        print("Initializing Enhanced Transcription Service...")
        
        # Initialize with explicit device and dtype settings
        service = EnhancedTranscriptionService(
            model_name="openai/whisper-tiny",
            device="cpu",
            vad_aggressiveness=2
        )
        print("✅ Service initialized successfully")
        
        # Create test audio
        test_file = create_compatible_test_audio("enhanced_test.wav", 8.0)
        
        print(f"🎯 Running transcription on {test_file}...")
        
        # Run transcription
        result = service.transcribe_audio(test_file)
        
        if result.success:
            print("✅ Enhanced transcription successful")
            print(f"📝 Transcription: '{result.text}'")
            print(f"⏱️ Processing time: {result.processing_time:.2f}s")
            print(f"📊 Voice segments: {len(result.segments)}")
            
            if hasattr(result, 'efficiency_gain'):
                print(f"🚀 Efficiency gain: {result.efficiency_gain:.1f}x")
        else:
            print(f"❌ Enhanced transcription failed: {result.error}")
            return False
            
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            
        return True
        
    except Exception as e:
        print(f"❌ Enhanced service test failed: {e}")
        return False

def main():
    """Run comprehensive integration tests"""
    print("🚀 FIXED INTEGRATION TEST")
    print("=" * 50)
    print("Testing Enhanced Transcription Service components with NumPy 2.x fixes...")
    
    # Test results
    results = {
        'vad': False,
        'whisper': False, 
        'enhanced': False
    }
    
    # Test 1: VAD Service
    print("\n" + "=" * 20 + " VAD Service " + "=" * 20)
    results['vad'] = test_vad_service_only()
    
    # Test 2: Whisper Loading  
    print("\n" + "=" * 20 + " Whisper Loading " + "=" * 20)
    results['whisper'] = test_whisper_loading()
    
    # Test 3: Enhanced Service (only if previous tests pass)
    print("\n" + "=" * 20 + " Enhanced Service " + "=" * 20)
    if results['vad'] and results['whisper']:
        results['enhanced'] = test_enhanced_service()
    else:
        print("⏭️ Skipping enhanced service test due to prerequisite failures")
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.upper()} Service")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced Transcription Service is ready!")
    else:
        print(f"⚠️ {total - passed} tests failed")
        print("🔧 Check the errors above for issues to fix")
    
    # Cleanup any remaining test files
    for test_file in ["vad_only_test.wav", "enhanced_test.wav", "integration_test_audio.wav"]:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"🧹 Cleaned up {test_file}")

if __name__ == "__main__":
    main()
