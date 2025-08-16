#!/usr/bin/env python3
"""
Complete Transcription Testing Suite for Verba
Tests all aspects of the transcription system for full functionality
"""

import os
import sys
import time
import json
import numpy as np
import soundfile as sf
from typing import Dict, List, Any, Tuple
import threading
import queue
from pathlib import Path

# Import your enhanced transcription service
from enhanced_transcription_service import EnhancedTranscriptionService
from real_time_audio_capture import RealTimeAudioCapture

class TranscriptionTester:
    """Comprehensive transcription testing suite"""
    
    def __init__(self):
        self.results = {}
        self.test_audio_dir = "test_audio_samples"
        self.transcription_service = None
        
    def setup_test_environment(self):
        """Setup testing environment and create test audio files"""
        print("🔧 Setting up test environment...")
        
        # Create test directory
        os.makedirs(self.test_audio_dir, exist_ok=True)
        
        # Initialize transcription service
        try:
            self.transcription_service = EnhancedTranscriptionService()
            print("✅ Transcription service initialized")
        except Exception as e:
            print(f"❌ Failed to initialize transcription service: {e}")
            return False
            
        # Create test audio files
        self.create_test_audio_files()
        return True
    
    def create_test_audio_files(self):
        """Create various test audio files for comprehensive testing"""
        print("🎵 Creating test audio files...")
        
        sample_rate = 16000
        test_files = [
            # Short audio (5 seconds)
            ("short_speech.wav", self.generate_speech_like_audio(5, sample_rate)),
            # Medium audio (30 seconds) 
            ("medium_speech.wav", self.generate_speech_like_audio(30, sample_rate)),
            # Long audio (120 seconds)
            ("long_speech.wav", self.generate_speech_like_audio(120, sample_rate)),
            # Silent audio
            ("silence.wav", np.zeros(sample_rate * 5, dtype=np.float32)),
            # Mixed speech and silence
            ("mixed_audio.wav", self.generate_mixed_audio(60, sample_rate)),
        ]
        
        for filename, audio_data in test_files:
            filepath = os.path.join(self.test_audio_dir, filename)
            sf.write(filepath, audio_data, sample_rate)
            print(f"  ✅ Created {filename}")
    
    def generate_speech_like_audio(self, duration: int, sample_rate: int) -> np.ndarray:
        """Generate speech-like audio patterns for testing"""
        samples = duration * sample_rate
        t = np.linspace(0, duration, samples)
        
        # Create speech-like patterns with varying frequencies
        speech_audio = np.zeros(samples)
        
        # Add speech bursts with pauses
        for i in range(0, samples, sample_rate * 2):  # Every 2 seconds
            burst_length = int(sample_rate * 1.5)  # 1.5 second bursts
            if i + burst_length < samples:
                # Create formant-like frequencies (speech characteristics)
                f1 = 800 + 200 * np.sin(2 * np.pi * 0.1 * t[i:i+burst_length])  # First formant
                f2 = 1200 + 300 * np.sin(2 * np.pi * 0.15 * t[i:i+burst_length])  # Second formant
                
                burst = (0.3 * np.sin(2 * np.pi * f1 * t[i:i+burst_length]) +
                        0.2 * np.sin(2 * np.pi * f2 * t[i:i+burst_length]))
                
                # Add envelope for more natural speech patterns
                envelope = np.exp(-3 * np.abs(t[i:i+burst_length] - t[i+burst_length//2]))
                speech_audio[i:i+burst_length] = burst * envelope
        
        # Add some noise for realism
        noise = np.random.normal(0, 0.02, samples)
        return (speech_audio + noise).astype(np.float32)
    
    def generate_mixed_audio(self, duration: int, sample_rate: int) -> np.ndarray:
        """Generate audio with mixed speech and silence periods"""
        samples = duration * sample_rate
        mixed_audio = np.zeros(samples)
        
        # Alternate between speech and silence
        for i in range(0, samples, sample_rate * 10):  # Every 10 seconds
            if (i // (sample_rate * 10)) % 2 == 0:  # Even intervals: speech
                speech_length = min(sample_rate * 8, samples - i)
                mixed_audio[i:i+speech_length] = self.generate_speech_like_audio(8, sample_rate)[:speech_length]
            # Odd intervals remain silent
        
        return mixed_audio.astype(np.float32)
    
    def test_basic_transcription(self) -> Dict[str, Any]:
        """Test basic transcription functionality"""
        print("\n🧪 Testing Basic Transcription...")
        results = {}
        
        test_files = [
            "short_speech.wav",
            "medium_speech.wav", 
            "silence.wav",
            "mixed_audio.wav"
        ]
        
        for filename in test_files:
            filepath = os.path.join(self.test_audio_dir, filename)
            if not os.path.exists(filepath):
                continue
                
            print(f"  📝 Testing {filename}...")
            start_time = time.time()
            
            try:
                result = self.transcription_service.transcribe_audio(filepath)
                end_time = time.time()
                
                processing_time = end_time - start_time
                audio_duration = sf.info(filepath).duration
                realtime_factor = processing_time / audio_duration
                
                results[filename] = {
                    "success": result.success,
                    "text": result.text,
                    "confidence": getattr(result, 'confidence', None),
                    "audio_duration": audio_duration,
                    "processing_time": processing_time,
                    "realtime_factor": realtime_factor,
                    "segments": len(result.segments) if hasattr(result, 'segments') else 0,
                    "error": None
                }
                
                print(f"    ✅ Success: {result.success}")
                print(f"    📊 Duration: {audio_duration:.1f}s")
                print(f"    ⏱️ Processing: {processing_time:.2f}s")
                print(f"    🚀 Speed: {realtime_factor:.2f}x realtime")
                print(f"    📝 Text length: {len(result.text)} chars")
                
            except Exception as e:
                results[filename] = {
                    "success": False,
                    "error": str(e),
                    "processing_time": time.time() - start_time
                }
                print(f"    ❌ Failed: {e}")
        
        return results
    
    def test_chunked_transcription(self) -> Dict[str, Any]:
        """Test chunked transcription for improved speed on low-end devices"""
        print("\n🧪 Testing Chunked Transcription (15-second chunks)...")
        results = {}
        
        # Test with long audio file
        filepath = os.path.join(self.test_audio_dir, "long_speech.wav")
        if not os.path.exists(filepath):
            return {"error": "Long audio file not found"}
        
        print("  📊 Testing chunked vs. full transcription...")
        
        # Test full transcription
        print("    🔄 Full transcription...")
        start_time = time.time()
        try:
            full_result = self.transcription_service.transcribe_audio(filepath)
            full_time = time.time() - start_time
            
            # Test chunked transcription
            print("    🔄 Chunked transcription...")
            chunked_results = self.transcribe_in_chunks(filepath, chunk_duration=15)
            
            results = {
                "full_transcription": {
                    "success": full_result.success,
                    "text": full_result.text,
                    "processing_time": full_time,
                    "text_length": len(full_result.text)
                },
                "chunked_transcription": chunked_results,
                "speed_improvement": (full_time - chunked_results["total_time"]) / full_time if chunked_results["success"] else None
            }
            
            print(f"    📈 Full processing: {full_time:.2f}s")
            print(f"    📈 Chunked processing: {chunked_results['total_time']:.2f}s")
            if results["speed_improvement"]:
                print(f"    🚀 Speed improvement: {results['speed_improvement']*100:.1f}%")
                
        except Exception as e:
            results = {"error": str(e)}
            print(f"    ❌ Failed: {e}")
        
        return results
    
    def transcribe_in_chunks(self, filepath: str, chunk_duration: int = 15) -> Dict[str, Any]:
        """Transcribe audio file in chunks"""
        try:
            # Load audio file
            audio_data, sample_rate = sf.read(filepath)
            total_duration = len(audio_data) / sample_rate
            
            chunk_samples = chunk_duration * sample_rate
            chunks = []
            chunk_results = []
            
            # Split into chunks
            for i in range(0, len(audio_data), chunk_samples):
                chunk = audio_data[i:i+chunk_samples]
                chunks.append(chunk)
            
            print(f"      📊 Split into {len(chunks)} chunks of ~{chunk_duration}s each")
            
            # Transcribe each chunk
            total_processing_time = 0
            combined_text = ""
            
            for i, chunk in enumerate(chunks):
                # Save chunk to temporary file
                temp_path = os.path.join(self.test_audio_dir, f"temp_chunk_{i}.wav")
                sf.write(temp_path, chunk, sample_rate)
                
                # Transcribe chunk
                start_time = time.time()
                chunk_result = self.transcription_service.transcribe_audio(temp_path)
                chunk_time = time.time() - start_time
                
                total_processing_time += chunk_time
                if chunk_result.success and chunk_result.text.strip():
                    combined_text += chunk_result.text + " "
                
                chunk_results.append({
                    "chunk": i,
                    "duration": len(chunk) / sample_rate,
                    "processing_time": chunk_time,
                    "text": chunk_result.text,
                    "success": chunk_result.success
                })
                
                # Clean up temp file
                os.remove(temp_path)
                
                print(f"        Chunk {i+1}/{len(chunks)}: {chunk_time:.2f}s")
            
            return {
                "success": True,
                "total_chunks": len(chunks),
                "total_time": total_processing_time,
                "combined_text": combined_text.strip(),
                "text_length": len(combined_text.strip()),
                "chunk_results": chunk_results,
                "average_chunk_time": total_processing_time / len(chunks)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_real_time_capabilities(self) -> Dict[str, Any]:
        """Test real-time transcription capabilities"""
        print("\n🧪 Testing Real-Time Capabilities...")
        results = {}
        
        try:
            # Test buffer management
            print("  🔄 Testing audio buffer management...")
            
            # Create a mock real-time audio capture test
            transcriptions = []
            errors = []
            
            def transcription_callback(text: str, metadata: Dict[str, Any]):
                transcriptions.append({
                    "text": text,
                    "timestamp": time.time(),
                    "metadata": metadata
                })
                print(f"    📝 Real-time: {text[:50]}...")
            
            def error_callback(error: str):
                errors.append(error)
                print(f"    ❌ Error: {error}")
            
            # Test with a medium-length audio file as simulated real-time input
            test_file = os.path.join(self.test_audio_dir, "medium_speech.wav")
            if os.path.exists(test_file):
                start_time = time.time()
                
                # Simulate real-time processing by processing chunks
                audio_data, sample_rate = sf.read(test_file)
                chunk_size = sample_rate * 2  # 2-second chunks
                
                for i in range(0, len(audio_data), chunk_size):
                    chunk = audio_data[i:i+chunk_size]
                    temp_path = os.path.join(self.test_audio_dir, "realtime_test.wav")
                    sf.write(temp_path, chunk, sample_rate)
                    
                    # Process chunk
                    try:
                        result = self.transcription_service.transcribe_audio(temp_path)
                        if result.success and result.text.strip():
                            transcription_callback(result.text, {
                                "chunk": i // chunk_size,
                                "timestamp": time.time()
                            })
                    except Exception as e:
                        error_callback(str(e))
                    
                    os.remove(temp_path)
                    time.sleep(0.1)  # Simulate real-time delay
                
                total_time = time.time() - start_time
                
                results = {
                    "success": True,
                    "total_transcriptions": len(transcriptions),
                    "total_errors": len(errors),
                    "processing_time": total_time,
                    "transcriptions": transcriptions,
                    "errors": errors,
                    "average_latency": total_time / len(transcriptions) if transcriptions else 0
                }
                
                print(f"    ✅ Real-time test completed")
                print(f"    📊 Transcriptions: {len(transcriptions)}")
                print(f"    ❌ Errors: {len(errors)}")
                print(f"    ⏱️ Average latency: {results['average_latency']:.2f}s")
            
        except Exception as e:
            results = {"success": False, "error": str(e)}
            print(f"    ❌ Real-time test failed: {e}")
        
        return results
    
    def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks for low-end devices"""
        print("\n🧪 Testing Performance Benchmarks...")
        results = {}
        
        # Test memory usage
        print("  📊 Testing memory efficiency...")
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Load and process different file sizes
        test_cases = [
            ("short_speech.wav", "Short (5s)"),
            ("medium_speech.wav", "Medium (30s)"),
            ("long_speech.wav", "Long (120s)")
        ]
        
        for filename, description in test_cases:
            filepath = os.path.join(self.test_audio_dir, filename)
            if not os.path.exists(filepath):
                continue
                
            print(f"    🔄 Processing {description}...")
            
            # Measure memory before processing
            memory_before = process.memory_info().rss / 1024 / 1024
            start_time = time.time()
            
            try:
                result = self.transcription_service.transcribe_audio(filepath)
                processing_time = time.time() - start_time
                
                # Measure memory after processing
                memory_after = process.memory_info().rss / 1024 / 1024
                memory_delta = memory_after - memory_before
                
                audio_info = sf.info(filepath)
                realtime_factor = processing_time / audio_info.duration
                
                results[filename] = {
                    "description": description,
                    "success": result.success,
                    "audio_duration": audio_info.duration,
                    "processing_time": processing_time,
                    "realtime_factor": realtime_factor,
                    "memory_before": memory_before,
                    "memory_after": memory_after,
                    "memory_delta": memory_delta,
                    "text_length": len(result.text)
                }
                
                print(f"      ⏱️ Time: {processing_time:.2f}s ({realtime_factor:.2f}x realtime)")
                print(f"      🧠 Memory: +{memory_delta:.1f}MB (total: {memory_after:.1f}MB)")
                
            except Exception as e:
                results[filename] = {
                    "description": description,
                    "success": False,
                    "error": str(e)
                }
                print(f"      ❌ Failed: {e}")
        
        # Overall memory efficiency
        final_memory = process.memory_info().rss / 1024 / 1024
        results["memory_summary"] = {
            "initial_memory": initial_memory,
            "final_memory": final_memory,
            "total_increase": final_memory - initial_memory,
            "within_4gb_target": final_memory < 4000  # 4GB target
        }
        
        print(f"  📊 Memory Summary:")
        print(f"    Initial: {initial_memory:.1f}MB")
        print(f"    Final: {final_memory:.1f}MB")
        print(f"    Total increase: {final_memory - initial_memory:.1f}MB")
        print(f"    4GB target met: {results['memory_summary']['within_4gb_target']}")
        
        return results
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run the complete transcription test suite"""
        print("🚀 VERBA TRANSCRIPTION TEST SUITE")
        print("=" * 50)
        
        if not self.setup_test_environment():
            return {"error": "Failed to setup test environment"}
        
        # Run all tests
        all_results = {
            "basic_transcription": self.test_basic_transcription(),
            "chunked_transcription": self.test_chunked_transcription(),
            "real_time_capabilities": self.test_real_time_capabilities(),
            "performance_benchmarks": self.test_performance_benchmarks()
        }
        
        # Generate summary
        self.generate_test_summary(all_results)
        
        return all_results
    
    def generate_test_summary(self, results: Dict[str, Any]):
        """Generate a comprehensive test summary"""
        print("\n🎉 TEST SUMMARY")
        print("=" * 30)
        
        # Basic transcription summary
        basic_tests = results.get("basic_transcription", {})
        successful_basic = sum(1 for r in basic_tests.values() if isinstance(r, dict) and r.get("success", False))
        total_basic = len([r for r in basic_tests.values() if isinstance(r, dict)])
        
        print(f"📝 Basic Transcription: {successful_basic}/{total_basic} tests passed")
        
        # Performance summary
        perf_tests = results.get("performance_benchmarks", {})
        if "memory_summary" in perf_tests:
            memory_ok = perf_tests["memory_summary"]["within_4gb_target"]
            print(f"🧠 Memory Usage: {'✅ Within 4GB target' if memory_ok else '❌ Exceeds 4GB target'}")
        
        # Real-time capability summary  
        rt_tests = results.get("real_time_capabilities", {})
        if rt_tests.get("success"):
            print(f"⚡ Real-time Processing: ✅ {rt_tests['total_transcriptions']} successful transcriptions")
        else:
            print("⚡ Real-time Processing: ❌ Failed")
        
        # Chunking efficiency summary
        chunked_tests = results.get("chunked_transcription", {})
        if chunked_tests.get("speed_improvement"):
            improvement = chunked_tests["speed_improvement"] * 100
            print(f"🚀 Chunking Efficiency: ✅ {improvement:.1f}% speed improvement")
        else:
            print("🚀 Chunking Efficiency: ⚠️ No improvement or failed")
        
        # Overall recommendation
        print(f"\n🎯 OVERALL STATUS:")
        if successful_basic >= total_basic * 0.8 and memory_ok:
            print("✅ TRANSCRIPTION SYSTEM IS READY FOR PRODUCTION")
        elif successful_basic >= total_basic * 0.5:
            print("⚠️ TRANSCRIPTION SYSTEM NEEDS OPTIMIZATION")
        else:
            print("❌ TRANSCRIPTION SYSTEM NEEDS MAJOR FIXES")
        
        # Save results to file
        with open("transcription_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Complete results saved to: transcription_test_results.json")

def main():
    """Main testing function"""
    tester = TranscriptionTester()
    results = tester.run_complete_test_suite()
    
    # Return exit code based on results
    basic_results = results.get("basic_transcription", {})
    successful_tests = sum(1 for r in basic_results.values() if isinstance(r, dict) and r.get("success", False))
    total_tests = len([r for r in basic_results.values() if isinstance(r, dict)])
    
    if successful_tests >= total_tests * 0.8:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
