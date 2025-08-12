#!/usr/bin/env python3
"""
Quick test script for Verba real-time audio feature
"""
import time
from real_time_audio_capture import create_microphone_capture
from enhanced_transcription_service import EnhancedTranscriptionService

def test_transcription_callback(result):
    if result.success and result.text.strip():
        print(f"📝 TRANSCRIBED: {result.text}")
        print(f"⏱️ Time: {result.processing_time:.2f}s | 🚀 Gain: {result.efficiency_gain:.1f}x")
        print("-" * 50)

def main():
    print("🧪 QUICK AUDIO FEATURE TEST")
    print("===========================")
    
    try:
        # Initialize transcription service
        print("🔧 Initializing transcription service...")
        service = EnhancedTranscriptionService(
            model_name="openai/whisper-tiny",
            device="cpu",
            vad_aggressiveness=2
        )
        print("✅ Service ready!")
        
        # Create audio capture
        print("🎤 Creating microphone capture...")
        capture = create_microphone_capture(
            transcription_service=service,
            transcription_callback=test_transcription_callback
        )
        print("✅ Capture ready!")
        
        # Start recording
        print("🎤 Starting recording... (speak now)")
        print("⏹️ Press Ctrl+C to stop")
        capture.start_recording()
        
        # Run until interrupted
        try:
            while True:
                time.sleep(1)
                stats = capture.get_stats()
                print(f"\r📊 Buffer: {stats['buffer_duration']:.1f}s | "
                      f"Processed: {stats['total_audio_processed']:.1f}s", end="")
        except KeyboardInterrupt:
            print("\n⏹️ Stopping...")
        
        capture.stop_recording()
        
        # Show final stats
        final_stats = capture.get_stats()
        print(f"\n✅ Test completed!")
        print(f"📈 Total audio: {final_stats['total_audio_processed']:.1f}s")
        print(f"📊 Transcriptions: {final_stats['transcription_chunks']}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
