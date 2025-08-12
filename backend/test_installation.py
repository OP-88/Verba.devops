#!/usr/bin/env python3
"""Test script to verify all dependencies are working"""

def test_imports():
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
        
        import torch
        print(f"✅ PyTorch {torch.__version__} imported")
        
        import whisper
        print("✅ Whisper imported successfully")
        
        import sounddevice as sd
        print("✅ SoundDevice imported successfully")
        
        import webrtcvad
        print("✅ WebRTC VAD imported successfully")
        
        import librosa
        print("✅ Librosa imported successfully")
        
        print("\n🎉 All dependencies successfully installed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_whisper_model():
    try:
        import whisper
        print("\n🔄 Testing Whisper model loading...")
        model = whisper.load_model("tiny")
        print("✅ Whisper tiny model loaded successfully")
        print(f"Model device: {next(model.parameters()).device}")
        return True
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Verba Backend Dependencies...\n")
    
    if test_imports():
        test_whisper_model()
    else:
        print("❌ Dependency installation incomplete")
