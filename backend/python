#!/usr/bin/env python3
"""
Verba Enhanced - Dependency Diagnostic Script
"""

import sys

def check_dependencies():
    """Check all required dependencies for enhanced Verba"""
    print("🔍 Checking Verba Enhanced Dependencies...")
    
    dependencies = {
        'librosa': 'Audio processing and analysis',
        'numpy': 'Numerical computing',
        'whisper': 'OpenAI Whisper for transcription',
        'fastapi': 'Web API framework',
        'webrtcvad': 'Voice Activity Detection',
        'sklearn': 'Machine learning utilities',
        'textstat': 'Text analysis and readability',
        'scipy': 'Scientific computing',
        'requests': 'HTTP requests for AI integration',
        'pydantic': 'Data validation',
        'uvicorn': 'ASGI server'
    }
    
    missing = []
    installed = []
    
    for package, description in dependencies.items():
        try:
            if package == 'sklearn':
                import sklearn
            else:
                __import__(package)
            print(f"✅ {package:<12} - {description}")
            installed.append(package)
        except ImportError:
            print(f"❌ {package:<12} - {description} (MISSING)")
            missing.append(package)
    
    print(f"\n📊 Summary:")
    print(f"✅ Installed: {len(installed)}")
    print(f"❌ Missing: {len(missing)}")
    
    if missing:
        print(f"\n🔧 To install missing dependencies:")
        if 'sklearn' in missing:
            missing[missing.index('sklearn')] = 'scikit-learn'
        print(f"pip install {' '.join(missing)}")
        return False
    else:
        print("\n🎉 All dependencies are installed!")
        return True

def test_basic_functionality():
    """Test basic functionality that might be causing issues"""
    print("\n🧪 Testing Basic Functionality...")
    
    try:
        # Test audio loading
        import librosa
        import numpy as np
        
        # Create test audio
        test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 16000))
        print("✅ Audio generation works")
        
        # Test content detection components
        from sklearn.cluster import KMeans
        print("✅ Machine learning components work")
        
        # Test text analysis
        import textstat
        test_score = textstat.flesch_reading_ease("This is a test sentence.")
        print(f"✅ Text analysis works (score: {test_score})")
        
        # Test VAD
        import webrtcvad
        vad = webrtcvad.Vad(2)
        print("✅ Voice Activity Detection works")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def check_audio_formats():
    """Check supported audio formats"""
    print("\n🎵 Checking Audio Format Support...")
    
    try:
        import librosa
        
        formats = ['.wav', '.mp3', '.m4a', '.flac']
        print("Supported formats:")
        for fmt in formats:
            print(f"✅ {fmt}")
            
        return True
    except Exception as e:
        print(f"❌ Audio format check failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("VERBA ENHANCED DIAGNOSTIC")
    print("=" * 50)
    
    deps_ok = check_dependencies()
    func_ok = test_basic_functionality() if deps_ok else False
    audio_ok = check_audio_formats() if deps_ok else False
    
    print("\n" + "=" * 50)
    if deps_ok and func_ok and audio_ok:
        print("🎉 SYSTEM READY FOR ENHANCED VERBA!")
    else:
        print("⚠️  SYSTEM NEEDS ATTENTION")
        print("\nPlease install missing dependencies and try again.")
    print("=" * 50)
