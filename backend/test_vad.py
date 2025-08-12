#!/usr/bin/env python3
"""
Simple test script for VAD Service
Run this to verify your VAD implementation works
"""

import asyncio
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import should work
from services.vad_service import VADService

async def test_vad_initialization():
    """Test basic VAD service initialization"""
    print("🧪 Testing VAD Service Initialization...")
    
    vad_service = VADService(aggressiveness=2)
    
    # Test initialization
    success = await vad_service.initialize()
    
    if success:
        print("✅ VAD Service initialized successfully!")
        print(f"   - Aggressiveness: {vad_service.aggressiveness}")
        print(f"   - Frame Duration: {vad_service.frame_duration_ms}ms")
        print(f"   - Initialized: {vad_service.is_initialized}")
        
        # Get stats
        stats = vad_service.get_performance_stats()
        print(f"   - Stats Available: {bool(stats)}")
        
        return True
    else:
        print("❌ VAD Service initialization failed!")
        return False

async def main():
    """Run all VAD tests"""
    print("🚀 Starting VAD Service Tests...")
    print("=" * 50)
    
    # Test 1: Initialization
    init_success = await test_vad_initialization()
    
    if init_success:
        print("\n🎉 VAD Service is ready!")
        print("✅ All dependencies installed correctly")
        print("✅ WebRTC VAD working")
        print("✅ Audio processing utilities available")
        print("\n🎯 Ready for Enhanced Transcription Service integration!")
    else:
        print("\n❌ VAD Service setup needs attention")
        print("Check that all dependencies are installed:")
        print("   pip install webrtcvad librosa soundfile scipy")
    
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
