#!/usr/bin/env python3
"""
Enhanced Transcription Service Test Suite
Tests VAD integration, performance, and accuracy
"""

import os
import time
import json
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import asdict

# Test imports
try:
    from enhanced_transcription_service import EnhancedTranscriptionService, TranscriptionResult
    from vad_service import VADService
    import librosa
    import soundfile as sf
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all required files are in the same directory:")
    print("  - enhanced_transcription_service.py")
    print("  - vad_service.py")
    exit(1)

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranscriptionTester:
    """Comprehensive test suite for Enhanced Transcription Service"""
    
    def __init__(self):
        self.service = None
        self.test_results = {}
        self.sample_rate = 16000
    
    def generate_test_audio(self, duration: float = 10.0, 
                          speech_ratio: float = 0.6) -> np.ndarray:
        """
        Generate synthetic test audio with speech and silence periods
        
        Args:
            duration: Total audio duration in seconds
            speech_ratio: Ratio of speech to silence
            
        Returns:
            Generated audio array
        """
        total_samples = int(duration * self.sample_rate)
        audio = np.zeros(total_samples)
        
        # Generate speech-like segments
        speech_duration = duration * speech_ratio
        speech_samples = int(speech_duration * self.sample_rate)
        
        # Create segments of "speech" (sine waves with noise)
        segment_length = int(2.0 * self.sample_rate)  # 2-second segments
        current_pos = 0
        
        while current_pos + segment_length < speech_samples:
            # Generate speech-like signal
            t = np.linspace(0, 2.0, segment_length)
            frequencies = [200, 400, 800, 1600]  # Formant-like frequencies
            signal = np.zeros(segment_length)
            
            for freq in frequencies:
                signal += 0.25 * np.sin(2 * np.pi * freq * t)
            
            # Add noise for realism
            noise = 0.1 * np.random.randn(segment_length)
            signal += noise
            
            # Add to audio with some spacing
            audio[current_pos:current_pos + segment_length] = signal
            current_pos += int(3.0 * self.sample_rate)  # 3-second spacing
            
            if current_pos >= total_samples:
                break
        
        # Normalize
        if np.max(np.abs(audio)) > 0:
            audio = audio / np.max(np.abs(audio)) * 0.8
        
        return audio
    
    def save_test_audio(self, audio: np.ndarray, filename: str) -> str:
        """Save test audio to file"""
        filepath = f"test_audio_{filename}.wav"
        sf.write(filepath, audio, self.sample_rate)
        return filepath
    
    def test_service_initialization(self) -> bool:
        """Test 1: Service initialization and model loading"""
        print("\n🧪 Test 1: Service Initialization")
        print("-" * 40)
        
        try:
            start_time = time.time()
            
            # Initialize service
            self.service = EnhancedTranscriptionService(
                model_name="openai/whisper-tiny",  # Use tiny model for faster testing
                vad_aggressiveness=2,
                device="auto"
            )
            
            init_time = time.time() - start_time
            print(f"✅ Service initialized in {init_time:.2f}s")
            
            # Load model
            model_start = time.time()
            model_loaded = self.service.load_whisper_model()
            model_time = time.time() - model_start
            
            if model_loaded:
                print(f"✅ Whisper model loaded in {model_time:.2f}s")
                self.test_results['initialization'] = {
                    'success': True,
                    'init_time': init_time,
                    'model_load_time': model_time,
                    'total_time': init_time + model_time
                }
                return True
            else:
                print("❌ Failed to load Whisper model")
                self.test_results['initialization'] = {
                    'success': False,
                    'error': 'Model loading failed'
                }
                return False
                
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            self.test_results['initialization'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_vad_integration(self) -> bool:
        """Test 2: VAD integration and voice detection"""
        print("\n🧪 Test 2: VAD Integration")
        print("-" * 40)
        
        try:
            # Generate test audio with known speech ratio
            test_duration = 15.0
            expected_speech_ratio = 0.4
            
            print(f"Generating test audio: {test_duration}s, {expected_speech_ratio:.0%} speech")
            test_audio = self.generate_test_audio(test_duration, expected_speech_ratio)
            
            # Detect voice segments
            segments = self.service.detect_voice_segments(test_audio)
            
            # Calculate detected speech ratio
            total_speech_duration = sum(seg.duration for seg in segments)
            detected_ratio = total_speech_duration / test_duration
            
            print(f"📊 Expected speech ratio: {expected_speech_ratio:.2%}")
            print(f"📊 Detected speech ratio: {detected_ratio:.2%}")
            print(f"📊 Detected segments: {len(segments)}")
            print(f"📊 Total speech duration: {total_speech_duration:.2f}s")
            
            # Check if detection is reasonable (within 50% of expected)
            ratio_accuracy = abs(detected_ratio - expected_speech_ratio) / expected_speech_ratio
            success = ratio_accuracy < 0.5  # Within 50% tolerance
            
            if success:
                print(f"✅ VAD detection accuracy: {(1-ratio_accuracy)*100:.1f}%")
            else:
                print(f"⚠️  VAD detection accuracy: {(1-ratio_accuracy)*100:.1f}% (below threshold)")
            
            self.test_results['vad_integration'] = {
                'success': success,
                'expected_ratio': expected_speech_ratio,
                'detected_ratio': detected_ratio,
                'accuracy': (1-ratio_accuracy)*100,
                'segments_count': len(segments),
                'total_speech_duration': total_speech_duration
            }
            
            return success
            
        except Exception as e:
            print(f"❌ VAD integration test failed: {e}")
            self.test_results['vad_integration'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_transcription_pipeline(self) -> bool:
        """Test 3: Complete transcription pipeline"""
        print("\n🧪 Test 3: Transcription Pipeline")
        print("-" * 40)
        
        try:
            # Generate test audio
            test_audio = self.generate_test_audio(duration=8.0, speech_ratio=0.5)
            test_file = self.save_test_audio(test_audio, "pipeline_test")
            
            print(f"Testing with: {test_file}")
            
            # Run complete transcription
            start_time = time.time()
            result = self.service.transcribe_file(test_file)
            processing_time = time.time() - start_time
            
            # Analyze results
            print(f"📝 Transcription completed")
            print(f"⏱️  Processing time: {processing_time:.2f}s")
            print(f"📊 Total duration: {result.total_duration:.2f}s")
            print(f"📊 Speech duration: {result.speech_duration:.2f}s")
            print(f"📊 Speech ratio: {result.speech_ratio:.2%}")
            print(f"⚡ Speed ratio: {result.processing_stats.get('processing_speed_ratio', 0):.2f}x")
            print(f"📈 Efficiency gain: {result.processing_stats.get('efficiency_gain', 0):.2%}")
            
            # Check if we got reasonable results
            success = (
                result.total_duration > 0 and
                result.speech_duration >= 0 and
                len(result.segments) > 0 and
                processing_time < result.total_duration * 3  # Should be reasonably fast
            )
            
            if success:
                print("✅ Transcription pipeline working correctly")
            else:
                print("⚠️  Transcription pipeline has issues")
            
            self.test_results['transcription_pipeline'] = {
                'success': success,
                'processing_time': processing_time,
                'total_duration': result.total_duration,
                'speech_duration': result.speech_duration,
                'speech_ratio': result.speech_ratio,
                'segments_count': len(result.segments),
                'efficiency_gain': result.processing_stats.get('efficiency_gain', 0),
                'speed_ratio': result.processing_stats.get('processing_speed_ratio', 0)
            }
            
            # Cleanup
            if os.path.exists(test_file):
                os.remove(test_file)
            
            return success
            
        except Exception as e:
            print(f"❌ Transcription pipeline test failed: {e}")
            self.test_results['transcription_pipeline'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """Test 4: Performance benchmarks"""
        print("\n🧪 Test 4: Performance Benchmarks")
        print("-" * 40)
        
        try:
            # Test with different audio lengths
            test_durations = [5.0, 15.0, 30.0]
            performance_results = []
            
            for duration in test_durations:
                print(f"\nTesting {duration}s audio...")
                
                # Generate test audio
                test_audio = self.generate_test_audio(duration, speech_ratio=0.3)
                test_file = self.save_test_audio(test_audio, f"perf_test_{duration}s")
                
                # Measure performance
                start_time = time.time()
                result = self.service.transcribe_file(test_file)
                processing_time = time.time() - start_time
                
                # Calculate metrics
                speed_ratio = duration / processing_time if processing_time > 0 else 0
                efficiency_gain = result.processing_stats.get('efficiency_gain', 0)
                
                performance_results.append({
                    'duration': duration,
                    'processing_time': processing_time,
                    'speed_ratio': speed_ratio,
                    'efficiency_gain': efficiency_gain,
                    'speech_ratio': result.speech_ratio
                })
                
                print(f"  ⏱️  Processing: {processing_time:.2f}s")
                print(f"  ⚡ Speed: {speed_ratio:.2f}x realtime")
                print(f"  📈 Efficiency: {efficiency_gain:.2%}")
                
                # Cleanup
                if os.path.exists(test_file):
                    os.remove(test_file)
            
            # Analyze performance trends
            avg_speed = np.mean([r['speed_ratio'] for r in performance_results])
            avg_efficiency = np.mean([r['efficiency_gain'] for r in performance_results])
            
            print(f"\n📊 Performance Summary:")
            print(f"   Average Speed: {avg_speed:.2f}x realtime")
            print(f"   Average Efficiency: {avg_efficiency:.2%}")
            
            # Success criteria: average speed > 1.0x, efficiency > 20%
            success = avg_speed > 1.0 and avg_efficiency > 0.2
            
            if success:
                print("✅ Performance benchmarks passed")
            else:
                print("⚠️  Performance benchmarks below targets")
            
            self.test_results['performance_benchmarks'] = {
                'success': success,
                'results': performance_results,
                'average_speed': avg_speed,
                'average_efficiency': avg_efficiency
            }
            
            return success
            
        except Exception as e:
            print(f"❌ Performance benchmark test failed: {e}")
            self.test_results['performance_benchmarks'] = {
                'success': False,
                'error': str(e)
            }
            return False
    
    def test_error_handling(self) -> bool:
        """Test 5: Error handling and edge cases"""
        print("\n🧪 Test 5: Error Handling")
        print("-" * 40)
        
        error_tests = []
        
        # Test 1: Non-existent file
        try:
            print("Testing non-existent file...")
            result = self.service.transcribe_file("nonexistent_file.wav")
            error_tests.append({'test': 'nonexistent_file', 'success': False, 'note': 'Should have failed'})
        except Exception as e:
            print(f"  ✅ Correctly handled non-existent file: {type(e).__name__}")
            error_tests.append({'test': 'nonexistent_file', 'success': True})
        
        # Test 2: Empty audio
        try:
            print("Testing empty audio...")
            empty_audio = np.zeros(int(0.1 * self.sample_rate))  # 100ms of silence
            test_file = self.save_test_audio(empty_audio, "empty")
            
            result = self.service.transcribe_file(test_file)
            print(f"  ✅ Empty audio handled: '{result.text}' ({len(result.segments)} segments)")
            error_tests.append({'test': 'empty_audio', 'success': True})
            
            if os.path.exists(test_file):
                os.remove(test_file)
                
        except Exception as e:
            print(f"  ⚠️  Empty audio error: {e}")
            error_tests.append({'test': 'empty_audio', 'success': False, 'error': str(e)})
        
        # Test 3: Very short audio
        try:
            print("Testing very short audio...")
            short_audio = self.generate_test_audio(duration=0.3, speech_ratio=1.0)  # 300ms
            test_file = self.save_test_audio(short_audio, "short")
            
            result = self.service.transcribe_file(test_file)
            print(f"  ✅ Short audio handled: {len(result.segments)} segments")
            error_tests.append({'test': 'short_audio', 'success': True})
            
            if os.path.exists(test_file):
                os.remove(test_file)
                
        except Exception as e:
            print(f"  ⚠️  Short audio error: {e}")
            error_tests.append({'test': 'short_audio', 'success': False, 'error': str(e)})
        
        # Evaluate error handling
        successful_tests = sum(1 for test in error_tests if test['success'])
        total_tests = len(error_tests)
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        print(f"\n📊 Error Handling Results: {successful_tests}/{total_tests} passed")
        
        overall_success = success_rate >= 0.7  # 70% success rate acceptable for error handling
        
        if overall_success:
            print("✅ Error handling working adequately")
        else:
            print("⚠️  Error handling needs improvement")
        
        self.test_results['error_handling'] = {
            'success': overall_success,
            'tests': error_tests,
            'success_rate': success_rate
        }
        
        return overall_success
    
    def test_real_audio_files(self) -> bool:
        """Test 6: Real audio files (if available)"""
        print("\n🧪 Test 6: Real Audio Files")
        print("-" * 40)
        
        # Look for real audio files in common locations
        test_paths = [
            "*.wav", "*.mp3", "*.m4a", "*.flac",
            "test_audio/*.wav", "test_audio/*.mp3",
            "samples/*.wav", "samples/*.mp3",
            "../test_audio/*.wav", "../test_audio/*.mp3"
        ]
        
        import glob
        real_files = []
        for pattern in test_paths:
            real_files.extend(glob.glob(pattern))
        
        if not real_files:
            print("ℹ️  No real audio files found for testing")
            print("   Place audio files in current directory or test_audio/ folder")
            self.test_results['real_audio_files'] = {
                'success': True,
                'note': 'No real files available for testing'
            }
            return True
        
        # Test with available real files
        results = []
        for audio_file in real_files[:3]:  # Test up to 3 files
            try:
                print(f"\nTesting real file: {audio_file}")
                
                start_time = time.time()
                result = self.service.transcribe_file(audio_file)
                processing_time = time.time() - start_time
                
                print(f"  📝 Text: {result.text[:80]}...")
                print(f"  ⏱️  Time: {processing_time:.2f}s")
                print(f"  📊 Duration: {result.total_duration:.2f}s")
                print(f"  🗣️  Speech: {result.speech_duration:.2f}s ({result.speech_ratio:.1%})")
                print(f"  ⚡ Speed: {result.processing_stats.get('processing_speed_ratio', 0):.2f}x")
                
                results.append({
                    'file': audio_file,
                    'success': True,
                    'processing_time': processing_time,
                    'duration': result.total_duration,
                    'speech_ratio': result.speech_ratio,
                    'text_length': len(result.text),
                    'segments_count': len(result.segments)
                })
                
            except Exception as e:
                print(f"  ❌ Failed: {e}")
                results.append({
                    'file': audio_file,
                    'success': False,
                    'error': str(e)
                })
        
        # Evaluate real file tests
        successful_files = sum(1 for r in results if r['success'])
        total_files = len(results)
        success_rate = successful_files / total_files if total_files > 0 else 0
        
        print(f"\n📊 Real Files Results: {successful_files}/{total_files} successful")
        
        overall_success = success_rate >= 0.8  # 80% success rate for real files
        
        if overall_success:
            print("✅ Real audio file processing working well")
        else:
            print("⚠️  Real audio file processing has issues")
        
        self.test_results['real_audio_files'] = {
            'success': overall_success,
            'results': results,
            'success_rate': success_rate
        }
        
        return overall_success
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("\n📋 TEST REPORT")
        print("=" * 60)
        
        # Count successes
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results.values() if result.get('success', False))
        
        print(f"Overall Results: {successful_tests}/{total_tests} tests passed")
        print(f"Success Rate: {successful_tests/total_tests*100:.1f}%")
        
        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
            print(f"\n{status} {test_name.replace('_', ' ').title()}")
            
            # Show key metrics
            if 'error' in result:
                print(f"   Error: {result['error']}")
            elif test_name == 'performance_benchmarks' and result.get('success'):
                print(f"   Average Speed: {result['average_speed']:.2f}x")
                print(f"   Average Efficiency: {result['average_efficiency']:.2%}")
            elif test_name == 'transcription_pipeline' and result.get('success'):
                print(f"   Speed Ratio: {result['speed_ratio']:.2f}x")
                print(f"   Efficiency Gain: {result['efficiency_gain']:.2%}")
        
        # Service statistics
        if self.service:
            print(f"\n📈 SERVICE STATISTICS")
            stats = self.service.get_service_stats()
            print(f"   Files Processed: {stats['total_files_processed']}")
            print(f"   Total Audio: {stats['total_audio_duration']:.2f}s")
            print(f"   Total Processing: {stats['total_processing_time']:.2f}s")
            print(f"   Efficiency Ratio: {stats['efficiency_ratio']:.2%}")
            if stats['total_processing_time'] > 0:
                print(f"   Average Speed: {stats['average_processing_speed']:.2f}x")
        
        # Overall assessment
        overall_grade = "EXCELLENT" if successful_tests == total_tests else \
                       "GOOD" if successful_tests >= total_tests * 0.8 else \
                       "FAIR" if successful_tests >= total_tests * 0.6 else "POOR"
        
        print(f"\n🎯 OVERALL ASSESSMENT: {overall_grade}")
        
        if successful_tests == total_tests:
            print("🎉 All systems operational! Ready for production use.")
        elif successful_tests >= total_tests * 0.8:
            print("👍 System working well with minor issues to address.")
        else:
            print("⚠️  System needs attention before production use.")
        
        # Generate JSON report
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'overall_success_rate': successful_tests / total_tests,
            'overall_grade': overall_grade,
            'tests_passed': successful_tests,
            'tests_total': total_tests,
            'detailed_results': self.test_results,
            'service_stats': self.service.get_service_stats() if self.service else {}
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save test report to JSON file"""
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"transcription_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"📄 Test report saved to: {filename}")
    
    def run_all_tests(self) -> bool:
        """Run the complete test suite"""
        print("🚀 ENHANCED TRANSCRIPTION SERVICE TEST SUITE")
        print("=" * 60)
        print("Testing VAD integration, performance, and accuracy...")
        
        # Run tests in sequence
        tests = [
            ('Service Initialization', self.test_service_initialization),
            ('VAD Integration', self.test_vad_integration),
            ('Transcription Pipeline', self.test_transcription_pipeline),
            ('Performance Benchmarks', self.test_performance_benchmarks),
            ('Error Handling', self.test_error_handling),
            ('Real Audio Files', self.test_real_audio_files)
        ]
        
        for test_name, test_func in tests:
            try:
                success = test_func()
                if not success:
                    print(f"⚠️  {test_name} had issues but continuing...")
            except Exception as e:
                print(f"❌ {test_name} failed critically: {e}")
                self.test_results[test_name.lower().replace(' ', '_')] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Generate final report
        report = self.generate_test_report()
        self.save_report(report)
        
        return report['overall_success_rate'] >= 0.8


def main():
    """Main test execution"""
    try:
        # Initialize tester
        tester = TranscriptionTester()
        
        # Run all tests
        overall_success = tester.run_all_tests()
        
        if overall_success:
            print("\n🎉 TEST SUITE COMPLETED SUCCESSFULLY!")
            print("✅ Enhanced Transcription Service is ready for production use.")
        else:
            print("\n⚠️  TEST SUITE COMPLETED WITH ISSUES")
            print("🔧 Review the report and address failing tests before production use.")
        
        return 0 if overall_success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite failed critically: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
