#!/usr/bin/env python3
"""
Simple audio transcription test - no complex imports
"""

import time
from real_time_audio_capture import RealTimeAudioCapture

def test_callback(text, metadata):
    print(f"🗣️ [{metadata.get('timestamp', 'unknown')}] {text}")

def main():
    print("🎤 Simple Audio Test")
    print("====================")

    try:
        # Create audio capture with minimal config
        capture = RealTimeAudioCapture(
            config={"buffer_seconds": 1.0},
            transcription_callback=test_callback
        )

        print("🎤 Starting microphone...")
        capture.start_microphone_capture()

        print("🗣️ Speak into your microphone...")
        print("⏹️ Press Ctrl+C to stop")

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n⏹️ Stopping...")
        capture.stop_capture()
        print("✅ Done!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
