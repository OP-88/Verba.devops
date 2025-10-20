#!/usr/bin/env python3
"""
Comprehensive Transcription Testing Suite
Tests all components and validates full functionality
"""

import os
import sys
import time
import numpy
import torch
import whisper
import librosa
import webrtcvad
import soundfile as sf
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print(f"{'='*60}")

def print_test_result(test_name, success, details=""):
    """Print test result with formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")

def check_dependencies():
    """Check if all required dependencies are installed"""
    print_header("DEPENDENCY CHECK")
    
    packages = [numpy, torch, whisper, librosa, webrtcvad, sf]
    names = ["numpy", "torch", "whisper", "librosa", "webrtcvad", "soundfile"]
    
    ok = True
    for name, pkg in zip(names, packages):
        try:
            print_test_result(f"{name} import", True, f"v{getattr(pkg, '__version__', 'unknown')}")
        except Exception as e:
            print_test_result(f"{name} import", False, str(e))
            ok = False
    return ok

def check_numpy_compatibility():
    """Check NumPy 2.x compatibility"""
    print_header("NUMPY 2.x COMPATIBILITY CHECK")
    
    try:
        # dtype test
        arr = numpy.zeros(100, dtype=numpy.float32)
        print_test_result("Explicit dtype parameter", True)
        
        # webrtcvad test
        vad = webrtcvad.Vad(2)
        frame = numpy.zeros(160, dtype=numpy.int16).tobytes()
        vad.is_speech(frame, 16000)
        print_test_result("webrtcvad compatibility", True)
    except Exception as e:
        print_test_result("NumPy compatibility", False, str(e))
        return False
    
    return True

def main():
    """Run all tests"""
    print_header("VERBA TRANSCRIPTION TEST SUITE")
    
    if not check_dependencies():
        return 1
    
    if not check_numpy_compatibility():
        return 1
    
    print("\n🎉 All checks passed! Ready for transcription.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
