#!/usr/bin/env python3
"""
Generate test audio files for Verba transcription testing
Creates synthetic speech samples for testing VAD, diarization, and transcription
"""

import numpy as np
import soundfile as sf
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def generate_sine_wave(frequency, duration, sample_rate=16000, amplitude=0.5):
    """Generate a sine wave for testing"""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = amplitude * np.sin(2 * np.pi * frequency * t)
    return wave.astype(np.float32)

def generate_speech_like_audio(duration=30, sample_rate=16000):
    """Generate speech-like audio with multiple frequencies"""
    # Create base frequencies for speech-like sounds
    fundamental = 200  # Base frequency (Hz)
    formants = [800, 1200, 2400]  # Formant frequencies
    
    audio = np.zeros(int(sample_rate * duration), dtype=np.float32)
    
    # Add fundamental frequency
    audio += 0.3 * generate_sine_wave(fundamental, duration, sample_rate)
    
    # Add formants with varying amplitudes
    for i, formant in enumerate(formants):
        amplitude = 0.2 / (i + 1)  # Decreasing amplitude for higher formants
        audio += amplitude * generate_sine_wave(formant, duration, sample_rate)
    
    # Add some modulation to make it more speech-like
    modulation = 0.1 * np.sin(2 * np.pi * 10 * np.linspace(0, duration, len(audio)))
    audio = audio * (1 + modulation)
    
    # Add silence periods to simulate pauses
    silence_points = np.random.choice(len(audio), size=int(len(audio) * 0.1), replace=False)
    for point in silence_points:
        silence_length = min(int(0.5 * sample_rate), len(audio) - point)
        audio[point:point + silence_length] *= 0.1
    
    return audio

def generate_two_speaker_audio(duration=60, sample_rate=16000):
    """Generate audio simulating two speakers"""
    audio = np.zeros(int(sample_rate * duration), dtype=np.float32)
    
    # Speaker 1: Lower pitch (150-300 Hz range)
    speaker1_segments = [
        (0, 10),      # 0-10 seconds
        (20, 30),     # 20-30 seconds  
        (40, 50)      # 40-50 seconds
    ]
    
    # Speaker 2: Higher pitch (250-450 Hz range)
    speaker2_segments = [
        (10, 20),     # 10-20 seconds
        (30, 40),     # 30-40 seconds
        (50, 60)      # 50-60 seconds
    ]
    
    for start, end in speaker1_segments:
        start_idx = int(start * sample_rate)
        end_idx = int(end * sample_rate)
        segment_duration = end - start
        
        # Generate speaker 1 audio (lower pitch)
        segment_audio = generate_sine_wave(200, segment_duration, sample_rate, 0.4)
        segment_audio += 0.2 * generate_sine_wave(400, segment_duration, sample_rate)
        segment_audio += 0.1 * generate_sine_wave(800, segment_duration, sample_rate)
        
        audio[start_idx:end_idx] = segment_audio
    
    for start, end in speaker2_segments:
        start_idx = int(start * sample_rate)
        end_idx = int(end * sample_rate) 
        segment_duration = end - start
        
        # Generate speaker 2 audio (higher pitch)
        segment_audio = generate_sine_wave(300, segment_duration, sample_rate, 0.4)
        segment_audio += 0.2 * generate_sine_wave(600, segment_duration, sample_rate)
        segment_audio += 0.1 * generate_sine_wave(1200, segment_duration, sample_rate)
        
        audio[start_idx:end_idx] = segment_audio
    
    # Add some background noise
    noise = 0.02 * np.random.randn(len(audio))
    audio += noise
    
    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8
    
    return audio

def generate_test_files():
    """Generate all test audio files"""
    test_dir = Path("samples")
    test_dir.mkdir(exist_ok=True)
    
    logger.info("🎵 Generating test audio files...")
    
    # 1. Short single speaker test (10 seconds)
    short_audio = generate_speech_like_audio(duration=10)
    sf.write(test_dir / "test_short.wav", short_audio, 16000)
    logger.info("✅ Generated test_short.wav (10s, single speaker)")
    
    # 2. Medium single speaker test (30 seconds)
    medium_audio = generate_speech_like_audio(duration=30)
    sf.write(test_dir / "test_medium.wav", medium_audio, 16000)
    logger.info("✅ Generated test_medium.wav (30s, single speaker)")
    
    # 3. Two speaker conversation test (60 seconds)
    conversation_audio = generate_two_speaker_audio(duration=60)
    sf.write(test_dir / "test_conversation.wav", conversation_audio, 16000)
    logger.info("✅ Generated test_conversation.wav (60s, two speakers)")
    
    # 4. Very short test for edge cases (2 seconds)
    very_short_audio = generate_speech_like_audio(duration=2)
    sf.write(test_dir / "test_very_short.wav", very_short_audio, 16000)
    logger.info("✅ Generated test_very_short.wav (2s, edge case)")
    
    # 5. Silence with speech test
    silence_audio = np.zeros(int(16000 * 20), dtype=np.float32)
    speech_segment = generate_speech_like_audio(duration=5)
    # Insert speech in middle of silence
    start_idx = int(7.5 * 16000)
    end_idx = start_idx + len(speech_segment)
    silence_audio[start_idx:end_idx] = speech_segment
    
    sf.write(test_dir / "test_silence.wav", silence_audio, 16000)
    logger.info("✅ Generated test_silence.wav (20s, speech in middle)")
    
    logger.info(f"🎉 All test files generated in {test_dir}")
    return test_dir

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    generate_test_files()