#!/usr/bin/env python3
"""
Simple VAD test - just test core dependencies
"""

import asyncio

async def test_vad_dependencies():
    """Test that all VAD dependencies work"""
    print("🧪 Testing VAD Dependencies...")
    
    try:
        import webrtcvad
        print("✅ WebRTC VAD imported successfully")
        
        # Test basic VAD creation
        vad = webrtcvad.Vad(2)
        print("✅ WebRTC VAD instance created")
        
    except ImportError as e:
        print(f"❌ WebRTC VAD import failed: {e}")
        return False
    
    try:
        import librosa
        print("✅ Librosa imported successfully")
    except ImportError as e:
        print(f"❌ Librosa import failed: {e}")
        return False
    
    try:
        import soundfile
        print("✅ SoundFile imported successfully")
    except ImportError as e:
        print(f"❌ SoundFile import failed: {e}")
        return False
    
    try:
        import scipy
        print("✅ SciPy imported successfully")
    except ImportError as e:
        print(f"❌ SciPy import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
        
        # Test basic audio array creation
        test_audio = np.random.randn(1000).astype(np.float32)
        print(f"✅ Created test audio array: {test_audio.shape}")
        
    except ImportError as e:
        print(f"❌ NumPy import failed: {e}")
        return False
    
    return True

async def main():
    """Run dependency tests"""
    print("🚀 VAD Dependency Test")
    print("=" * 40)
    
    success = await test_vad_dependencies()
    
    if success:
        print("\n🎉 All VAD dependencies working!")
        print("✅ Ready to implement VAD service")
    else:
        print("\n❌ Some dependencies missing")
        print("Run: pip install webrtcvad librosa soundfile scipy numpy")
    
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(main())
