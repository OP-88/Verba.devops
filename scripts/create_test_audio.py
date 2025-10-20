#!/usr/bin/env python3
"""
Generate test audio files for Verba testing
Creates synthetic speech-like audio with different speakers
"""

import numpy as np
import soundfile as sf
import os
from pathlib import Path

def create_test_audio():
    """Create a test audio file with synthetic speech patterns"""
    
    sample_rate = 16000
    duration = 30  # 30 seconds
    
    # Create time array
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create different frequency patterns for different "speakers"
    audio = np.zeros_like(t)
    
    # Speaker 1: 0-15 seconds (lower frequency)
    speaker1_end = len(t) // 2
    freq1 = 220  # Base frequency
    speaker1_t = t[:speaker1_end]
    
    # Add modulation to simulate speech patterns
    modulation1 = 1 + 0.3 * np.sin(2 * np.pi * 2 * speaker1_t)  # 2 Hz modulation
    formants1 = (np.sin(2 * np.pi * freq1 * speaker1_t) +
                 0.5 * np.sin(2 * np.pi * freq1 * 2 * speaker1_t) +
                 0.3 * np.sin(2 * np.pi * freq1 * 3 * speaker1_t))
    audio[:speaker1_end] = formants1 * modulation1 * 0.1
    
    # Add brief pause (1 second)
    pause_samples = sample_rate // 2
    pause_start = speaker1_end
    pause_end = pause_start + pause_samples
    if pause_end < len(t):
        audio[pause_start:pause_end] = 0
    
    # Speaker 2: 16-30 seconds (higher frequency)
    speaker2_start = pause_end if pause_end < len(t) else speaker1_end
    speaker2_t = t[speaker2_start:] - t[speaker2_start]
    freq2 = 330  # Higher frequency
    
    modulation2 = 1 + 0.4 * np.sin(2 * np.pi * 1.5 * speaker2_t)  # 1.5 Hz modulation
    formants2 = (np.sin(2 * np.pi * freq2 * speaker2_t) +
                 0.4 * np.sin(2 * np.pi * freq2 * 1.8 * speaker2_t) +
                 0.2 * np.sin(2 * np.pi * freq2 * 2.5 * speaker2_t))
    audio[speaker2_start:] = formants2 * modulation2 * 0.08
    
    # Add some noise for realism
    noise = np.random.normal(0, 0.01, len(audio))
    audio += noise
    
    # Normalize to prevent clipping
    audio = np.clip(audio, -0.95, 0.95)
    
    return audio, sample_rate

def create_short_test_audio():
    """Create a shorter 10-second test file"""
    sample_rate = 16000
    duration = 10
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Simple sine wave with modulation
    base_freq = 440
    modulation = 1 + 0.2 * np.sin(2 * np.pi * 3 * t)
    audio = 0.1 * np.sin(2 * np.pi * base_freq * t) * modulation
    
    # Add brief pauses to simulate speech
    for i in range(0, len(audio), sample_rate * 2):  # Every 2 seconds
        pause_end = min(i + sample_rate // 4, len(audio))  # 0.25 second pause
        audio[i:pause_end] *= 0.1
    
    return audio, sample_rate

def main():
    """Generate test audio files"""
    
    # Ensure output directory exists
    output_dir = Path(__file__).parent.parent / "frontend" / "public" / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🎵 Creating test audio files in {output_dir}")
    
    try:
        # Create 30-second test file with two speakers
        print("Creating test.wav (30s, 2 speakers)...")
        audio, sample_rate = create_test_audio()
        output_file = output_dir / "test.wav"
        sf.write(str(output_file), audio, sample_rate)
        print(f"✅ Created {output_file}")
        
        # Create shorter test file
        print("Creating test_short.wav (10s, single speaker)...")
        audio_short, sample_rate = create_short_test_audio()
        output_file_short = output_dir / "test_short.wav"
        sf.write(str(output_file_short), audio_short, sample_rate)
        print(f"✅ Created {output_file_short}")
        
        # Create a very short sample for quick testing
        print("Creating test_quick.wav (3s)...")
        quick_duration = 3
        t_quick = np.linspace(0, quick_duration, int(sample_rate * quick_duration))
        audio_quick = 0.1 * np.sin(2 * np.pi * 440 * t_quick) * (1 + 0.3 * np.sin(2 * np.pi * 5 * t_quick))
        output_file_quick = output_dir / "test_quick.wav"
        sf.write(str(output_file_quick), audio_quick, sample_rate)
        print(f"✅ Created {output_file_quick}")
        
        print("\n🎉 Test audio files created successfully!")
        print("\nFiles created:")
        for file in output_dir.glob("*.wav"):
            size = file.stat().st_size / 1024  # Size in KB
            print(f"  - {file.name}: {size:.1f} KB")
        
    except Exception as e:
        print(f"❌ Error creating test audio: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())