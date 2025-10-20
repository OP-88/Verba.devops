#!/usr/bin/env python3
"""
Optimized Audio Chunking System for Verba
Implements smart 15-second chunking for improved transcription speed on low-end devices
"""

import os
import time
import numpy as np
import librosa
import soundfile as sf
from typing import List, Dict, Any, Optional, Tuple, Generator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import logging
from pathlib import Path
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Audio chunk data structure"""
    chunk_id: int
    start_time: float
    end_time: float
    duration: float
    audio_data: np.ndarray
    sample_rate: int
    has_speech: bool
    confidence: float
    file_path: Optional[str] = None

@dataclass
class ChunkingResult:
    """Result of audio chunking process"""
    success: bool
    total_chunks: int
    total_duration: float
    speech_chunks: int
    silence_chunks: int
    processing_time: float
    chunks: List[AudioChunk]
    error: Optional[str] = None

@dataclass
class TranscriptionChunk:
    """Transcription result for a chunk"""
    chunk_id: int
    start_time: float
    end_time: float
    text: str
    confidence: float
    processing_time: float
    success: bool
    error: Optional[str] = None

class SmartAudioChunker:
    """Smart audio chunking system optimized for transcription speed"""
    
    def __init__(self, 
                 chunk_duration: float = 15.0,
                 overlap_duration: float = 1.0,
                 vad_service=None,
                 min_speech_duration: float = 0.5,
                 silence_threshold: float = 0.01):
        """
        Initialize the audio chunker
        
        Args:
            chunk_duration: Target duration for each chunk (seconds)
            overlap_duration: Overlap between chunks (seconds) 
            vad_service: Voice Activity Detection service
            min_speech_duration: Minimum speech duration to consider chunk valid
            silence_threshold: Threshold for considering audio as silence
        """
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.vad_service = vad_service
        self.min_speech_duration = min_speech_duration
        self.silence_threshold = silence_threshold
        
        # Performance tracking
        self.stats = {
            "total_chunks_processed": 0,
            "speech_chunks": 0,
            "silence_chunks": 0,
            "total_processing_time": 0,
            "average_chunk_time": 0
        }
    
    def chunk_audio_file(self, audio_path: str, output_dir: Optional[str] = None) -> ChunkingResult:
        """
        Chunk an audio file into optimized segments
        
        Args:
            audio_path: Path to input audio file
            output_dir: Directory to save chunk files (optional)
        """
        start_time = time.time()
        
        try:
            # Load audio file
            logger.info(f"Loading audio file: {audio_path}")
            audio_data, sample_rate = librosa.load(audio_path, sr=16000, dtype=np.float32)
            total_duration = len(audio_data) / sample_rate
            
            logger.info(f"Audio loaded: {total_duration:.2f}s, {sample_rate}Hz")
            
            # Create chunks
            chunks = self._create_smart_chunks(audio_data, sample_rate)
            
            # Apply VAD if available
            if self.vad_service:
                chunks = self._apply_vad_to_chunks(chunks)
            else:
                # Simple silence detection fallback
                chunks = self._apply_simple_silence_detection(chunks)
            
            # Save chunks if output directory provided
            if output_dir:
                self._save_chunks_to_files(chunks, output_dir)
            
            processing_time = time.time() - start_time
            speech_chunks = sum(1 for chunk in chunks if chunk.has_speech)
            silence_chunks = len(chunks) - speech_chunks
            
            # Update stats
            self._update_stats(len(chunks), speech_chunks, silence_chunks, processing_time)
            
            result = ChunkingResult(
                success=True,
                total_chunks=len(chunks),
                total_duration=total_duration,
                speech_chunks=speech_chunks,
                silence_chunks=silence_chunks,
                processing_time=processing_time,
                chunks=chunks
            )
            
            logger.info(f"Chunking completed: {len(chunks)} chunks, {speech_chunks} with speech")
            return result
            
        except Exception as e:
            logger.error(f"Chunking failed: {e}")
            return ChunkingResult(
                success=False,
                total_chunks=0,
                total_duration=0,
                speech_chunks=0,
                silence_chunks=0,
                processing_time=time.time() - start_time,
                chunks=[],
                error=str(e)
            )
    
    def _create_smart_chunks(self, audio_data: np.ndarray, sample_rate: int) -> List[AudioChunk]:
        """Create smart audio chunks with optimal boundaries"""
        chunks = []
        total_samples = len(audio_data)
        chunk_samples = int(self.chunk_duration * sample_rate)
        overlap_samples = int(self.overlap_duration * sample_rate)
        
        chunk_id = 0
        current_position = 0
        
        while current_position < total_samples:
            # Calculate chunk boundaries
            start_sample = current_position
            end_sample = min(start_sample + chunk_samples, total_samples)
            
            # Extract chunk data
            chunk_data = audio_data[start_sample:end_sample]
            
            # Calculate time boundaries
            start_time = start_sample / sample_rate
            end_time = end_sample / sample_rate
            duration = len(chunk_data) / sample_rate
            
            # Find optimal chunk boundary (avoid cutting mid-word)
            if end_sample < total_samples and duration >= self.chunk_duration * 0.8:
                # Look for silence in the last 2 seconds to find better boundary
                boundary_search_samples = int(2.0 * sample_rate)
                search_start = max(0, end_sample - boundary_search_samples)
                search_end = min(total_samples, end_sample + boundary_search_samples)
                
                optimal_boundary = self._find_optimal_boundary(
                    audio_data[search_start:search_end], 
                    sample_rate
                )
                
                if optimal_boundary is not None:
                    end_sample = search_start + optimal_boundary
                    chunk_data = audio_data[start_sample:end_sample]
                    end_time = end_sample / sample_rate
                    duration = len(chunk_data) / sample_rate
            
            # Create chunk
            chunk = AudioChunk(
                chunk_id=chunk_id,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                audio_data=chunk_data,
                sample_rate=sample_rate,
                has_speech=False,  # Will be determined by VAD
                confidence=0.0
            )
            
            chunks.append(chunk)
            
            # Move to next position with overlap
            current_position = end_sample - overlap_samples
            if current_position >= total_samples - overlap_samples:
                break
                
            chunk_id += 1
        
        return chunks
    
    def _find_optimal_boundary(self, audio_segment: np.ndarray, sample_rate: int) -> Optional[int]:
        """Find optimal chunk boundary by detecting silence"""
        if len(audio_segment) == 0:
            return None
        
        # Calculate RMS energy in small windows
        window_size = int(0.1 * sample_rate)  # 100ms windows
        energy_values = []
        
        for i in range(0, len(audio_segment) - window_size, window_size // 2):
            window = audio_segment[i:i + window_size]
            energy = np.sqrt(np.mean(window ** 2))
            energy_values.append((i, energy))
        
        if not energy_values:
            return None
        
        # Find the quietest point
        min_energy_idx, min_energy = min(energy_values, key=lambda x: x[1])
        
        # Only use this boundary if it's significantly quieter
        avg_energy = np.mean([e[1] for e in energy_values])
        if min_energy < avg_energy * 0.3:  # 30% of average energy
            return min_energy_idx
        
        return None
    
    def _apply_vad_to_chunks(self, chunks: List[AudioChunk]) -> List[AudioChunk]:
        """Apply Voice Activity Detection to chunks"""
        logger.info("Applying VAD to chunks...")
        
        for chunk in chunks:
            try:
                # Use VAD service to detect speech
                vad_result = self.vad_service.detect_voice_activity(
                    chunk.audio_data, 
                    chunk.sample_rate
                )
                
                if hasattr(vad_result, 'has_speech'):
                    chunk.has_speech = vad_result.has_speech
                    chunk.confidence = getattr(vad_result, 'confidence', 0.5)
                else:
                    # Fallback: check if result indicates speech
                    chunk.has_speech = bool(vad_result)
                    chunk.confidence = 0.5
                    
            except Exception as e:
                logger.warning(f"VAD failed for chunk {chunk.chunk_id}: {e}")
                # Fallback to simple energy-based detection
                chunk.has_speech = self._simple_speech_detection(chunk.audio_data)
                chunk.confidence = 0.3
        
        return chunks
    
    def _apply_simple_silence_detection(self, chunks: List[AudioChunk]) -> List[AudioChunk]:
        """Apply simple silence detection as VAD fallback"""
        logger.info("Applying simple silence detection...")
        
        for chunk in chunks:
            chunk.has_speech = self._simple_speech_detection(chunk.audio_data)
            chunk.confidence = 0.4  # Lower confidence for simple detection
        
        return chunks
    
    def _simple_speech_detection(self, audio_data: np.ndarray) -> bool:
        """Simple energy-based speech detection"""
        if len(audio_data) == 0:
            return False
        
        # Calculate RMS energy
        rms_energy = np.sqrt(np.mean(audio_data ** 2))
        
        # Check if energy is above silence threshold
        has_speech = rms_energy > self.silence_threshold
        
        # Additional check: ensure minimum duration of activity
        if has_speech:
            # Count samples above threshold
            active_samples = np.sum(np.abs(audio_data) > self.silence_threshold * 0.5)
            activity_ratio = active_samples / len(audio_data)
            has_speech = activity_ratio > 0.1  # At least 10% of chunk should be active
        
        return has_speech
    
    def _save_chunks_to_files(self, chunks: List[AudioChunk], output_dir: str):
        """Save chunks to individual audio files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for chunk in chunks:
            # Only save chunks with speech to save space
            if chunk.has_speech:
                filename = f"chunk_{chunk.chunk_id:03d}_{chunk.start_time:.2f}-{chunk.end_time:.2f}s.wav"
                filepath = os.path.join(output_dir, filename)
                
                try:
                    sf.write(filepath, chunk.audio_data, chunk.sample_rate)
                    chunk.file_path = filepath
                except Exception as e:
                    logger.warning(f"Failed to save chunk {chunk.chunk_id}: {e}")
    
    def _update_stats(self, total_chunks: int, speech_chunks: int, silence_chunks: int, processing_time: float):
        """Update performance statistics"""
        self.stats["total_chunks_processed"] += total_chunks
        self.stats["speech_chunks"] += speech_chunks
        self.stats["silence_chunks"] += silence_chunks
        self.stats["total_processing_time"] += processing_time
        
        if self.stats["total_chunks_processed"] > 0:
            self.stats["average_chunk_time"] = (
                self.stats["total_processing_time"] / self.stats["total_chunks_processed"]
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chunking performance statistics"""
        return self.stats.copy()

class OptimizedChunkTranscriber:
    """Optimized transcriber for audio chunks"""
    
    def __init__(self, transcription_service, max_workers: int = 2):
        """
        Initialize the chunk transcriber
        
        Args:
            transcription_service: Enhanced transcription service
            max_workers: Maximum parallel transcription workers
        """
        self.transcription_service = transcription_service
        self.max_workers = max_workers
        self.stats = {
            "total_chunks_transcribed": 0,
            "successful_transcriptions": 0,
            "failed_transcriptions": 0,
            "total_transcription_time": 0,
            "total_audio_duration": 0
        }
    
    def transcribe_chunks(self, chunks: List[AudioChunk], parallel: bool = True) -> List[TranscriptionChunk]:
        """
        Transcribe audio chunks with optimization for speed
        
        Args:
            chunks: List of audio chunks to transcribe
            parallel: Whether to use parallel processing
        """
        speech_chunks = [chunk for chunk in chunks if chunk.has_speech]
        
        logger.info(f"Transcribing {len(speech_chunks)} speech chunks (skipping {len(chunks) - len(speech_chunks)} silent chunks)")
        
        if parallel and self.max_workers > 1:
            return self._transcribe_parallel(speech_chunks)
        else:
            return self._transcribe_sequential(speech_chunks)
    
    def _transcribe_sequential(self, chunks: List[AudioChunk]) -> List[TranscriptionChunk]:
        """Transcribe chunks sequentially"""
        results = []
        
        for chunk in chunks:
            result = self._transcribe_single_chunk(chunk)
            results.append(result)
            self._update_stats(result)
        
        return results
    
    def _transcribe_parallel(self, chunks: List[AudioChunk]) -> List[TranscriptionChunk]:
        """Transcribe chunks in parallel for better performance"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all chunks for transcription
            future_to_chunk = {
                executor.submit(self._transcribe_single_chunk, chunk): chunk 
                for chunk in chunks
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_chunk):
                result = future.result()
                results.append(result)
                self._update_stats(result)
        
        # Sort results by chunk_id to maintain order
        results.sort(key=lambda x: x.chunk_id)
        return results
    
    def _transcribe_single_chunk(self, chunk: AudioChunk) -> TranscriptionChunk:
        """Transcribe a single audio chunk"""
        start_time = time.time()
        
        try:
            # Create temporary file for chunk if needed
            temp_file = None
            if chunk.file_path and os.path.exists(chunk.file_path):
                audio_path = chunk.file_path
            else:
                # Create temporary file
                temp_file = f"/tmp/chunk_{chunk.chunk_id}_{time.time()}.wav"
                sf.write(temp_file, chunk.audio_data, chunk.sample_rate)
                audio_path = temp_file
            
            # Transcribe chunk
            result = self.transcription_service.transcribe_audio(audio_path)
            processing_time = time.time() - start_time
            
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            return TranscriptionChunk(
                chunk_id=chunk.chunk_id,
                start_time=chunk.start_time,
                end_time=chunk.end_time,
                text=result.text if result.success else "",
                confidence=getattr(result, 'confidence', chunk.confidence),
                processing_time=processing_time,
                success=result.success,
                error=None if result.success else getattr(result, 'error', 'Transcription failed')
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Failed to transcribe chunk {chunk.chunk_id}: {e}")
            
            return TranscriptionChunk(
                chunk_id=chunk.chunk_id,
                start_time=chunk.start_time,
                end_time=chunk.end_time,
                text="",
                confidence=0.0,
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    def _update_stats(self, result: TranscriptionChunk):
        """Update transcription statistics"""
        self.stats["total_chunks_transcribed"] += 1
        self.stats["total_transcription_time"] += result.processing_time
        self.stats["total_audio_duration"] += result.end_time - result.start_time
        
        if result.success:
            self.stats["successful_transcriptions"] += 1
        else:
            self.stats["failed_transcriptions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get transcription performance statistics"""
        stats = self.stats.copy()
        
        # Calculate derived metrics
        if stats["total_chunks_transcribed"] > 0:
            stats["success_rate"] = stats["successful_transcriptions"] / stats["total_chunks_transcribed"]
            stats["average_processing_time"] = stats["total_transcription_time"] / stats["total_chunks_transcribed"]
        
        if stats["total_audio_duration"] > 0:
            stats["realtime_factor"] = stats["total_transcription_time"] / stats["total_audio_duration"]
            stats["speed_improvement"] = max(0, 1 - stats["realtime_factor"])
        
        return stats
    
    def combine_transcriptions(self, transcription_chunks: List[TranscriptionChunk]) -> str:
        """Combine chunk transcriptions into final text"""
        # Sort by chunk_id to ensure proper order
        sorted_chunks = sorted(transcription_chunks, key=lambda x: x.chunk_id)
        
        # Combine successful transcriptions
        combined_text = ""
        for chunk in sorted_chunks:
            if chunk.success and chunk.text.strip():
                # Add timestamp annotation for long transcriptions
                if len(combined_text) > 1000:  # Add timestamps every ~1000 characters
                    timestamp = f"[{chunk.start_time:.1f}s] "
                    combined_text += f"\n{timestamp}{chunk.text} "
                else:
                    combined_text += f"{chunk.text} "
        
        return combined_text.strip()

class ChunkedTranscriptionPipeline:
    """Complete pipeline for chunked transcription processing"""
    
    def __init__(self, transcription_service, vad_service=None, 
                 chunk_duration: float = 15.0, max_workers: int = 2):
        """
        Initialize the chunked transcription pipeline
        
        Args:
            transcription_service: Enhanced transcription service
            vad_service: Voice Activity Detection service
            chunk_duration: Duration of each chunk in seconds
            max_workers: Maximum parallel transcription workers
        """
        self.chunker = SmartAudioChunker(
            chunk_duration=chunk_duration,
            vad_service=vad_service
        )
        self.transcriber = OptimizedChunkTranscriber(
            transcription_service=transcription_service,
            max_workers=max_workers
        )
        self.pipeline_stats = {}
    
    def process_audio_file(self, audio_path: str, save_chunks: bool = False, 
                          output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Process complete audio file with chunked transcription
        
        Args:
            audio_path: Path to input audio file
            save_chunks: Whether to save individual chunk files
            output_dir: Directory for saving chunks and results
        """
        start_time = time.time()
        logger.info(f"Starting chunked transcription pipeline for: {audio_path}")
        
        try:
            # Step 1: Chunk the audio
            chunk_output_dir = os.path.join(output_dir, "chunks") if output_dir and save_chunks else None
            chunking_result = self.chunker.chunk_audio_file(audio_path, chunk_output_dir)
            
            if not chunking_result.success:
                return {
                    "success": False,
                    "error": f"Chunking failed: {chunking_result.error}",
                    "processing_time": time.time() - start_time
                }
            
            # Step 2: Transcribe chunks
            transcription_chunks = self.transcriber.transcribe_chunks(
                chunking_result.chunks, 
                parallel=True
            )
            
            # Step 3: Combine results
            final_text = self.transcriber.combine_transcriptions(transcription_chunks)
            
            # Step 4: Calculate performance metrics
            total_processing_time = time.time() - start_time
            audio_duration = chunking_result.total_duration
            realtime_factor = total_processing_time / audio_duration if audio_duration > 0 else 0
            speed_improvement = max(0, 1 - realtime_factor) if realtime_factor < 1 else 0
            
            # Compile results
            result = {
                "success": True,
                "final_text": final_text,
                "audio_duration": audio_duration,
                "processing_time": total_processing_time,
                "realtime_factor": realtime_factor,
                "speed_improvement": speed_improvement,
                "chunking_stats": {
                    "total_chunks": chunking_result.total_chunks,
                    "speech_chunks": chunking_result.speech_chunks,
                    "silence_chunks": chunking_result.silence_chunks,
                    "chunking_time": chunking_result.processing_time
                },
                "transcription_stats": self.transcriber.get_stats(),
                "chunk_results": [
                    {
                        "chunk_id": chunk.chunk_id,
                        "start_time": chunk.start_time,
                        "end_time": chunk.end_time,
                        "text": chunk.text,
                        "success": chunk.success,
                        "confidence": chunk.confidence
                    }
                    for chunk in transcription_chunks
                ]
            }
            
            # Save detailed results if output directory provided
            if output_dir:
                self._save_results(result, output_dir, os.path.basename(audio_path))
            
            # Log performance summary
            self._log_performance_summary(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _save_results(self, result: Dict[str, Any], output_dir: str, audio_filename: str):
        """Save processing results to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save transcription text
        text_file = os.path.join(output_dir, f"{Path(audio_filename).stem}_transcription.txt")
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(result["final_text"])
        
        # Save detailed results as JSON
        json_file = os.path.join(output_dir, f"{Path(audio_filename).stem}_results.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Results saved to: {output_dir}")
    
    def _log_performance_summary(self, result: Dict[str, Any]):
        """Log performance summary"""
        logger.info("🚀 CHUNKED TRANSCRIPTION PERFORMANCE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"📊 Audio Duration: {result['audio_duration']:.2f}s")
        logger.info(f"⏱️ Processing Time: {result['processing_time']:.2f}s")
        logger.info(f"🚀 Realtime Factor: {result['realtime_factor']:.2f}x")
        logger.info(f"📈 Speed Improvement: {result['speed_improvement']*100:.1f}%")
        logger.info(f"🔢 Total Chunks: {result['chunking_stats']['total_chunks']}")
        logger.info(f"🗣️ Speech Chunks: {result['chunking_stats']['speech_chunks']}")
        logger.info(f"🔇 Silence Chunks: {result['chunking_stats']['silence_chunks']}")
        logger.info(f"✅ Success Rate: {result['transcription_stats'].get('success_rate', 0)*100:.1f}%")
        
        # Performance assessment
        if result['speed_improvement'] > 0.3:
            logger.info("🎉 EXCELLENT: >30% speed improvement achieved!")
        elif result['speed_improvement'] > 0.15:
            logger.info("✅ GOOD: 15-30% speed improvement")
        elif result['speed_improvement'] > 0:
            logger.info("⚠️ MODEST: <15% speed improvement")
        else:
            logger.info("❌ NO IMPROVEMENT: Consider optimizing chunk size or hardware")

# Integration with existing Verba services
class VerbaChunkedTranscriptionService:
    """Service class for integrating chunked transcription with Verba backend"""
    
    def __init__(self, transcription_service, vad_service=None):
        """Initialize the Verba chunked transcription service"""
        self.pipeline = ChunkedTranscriptionPipeline(
            transcription_service=transcription_service,
            vad_service=vad_service,
            chunk_duration=15.0,  # Optimal for low-end devices
            max_workers=2  # Conservative for 4GB RAM target
        )
    
    def transcribe_with_chunking(self, audio_path: str, 
                               enable_chunking: bool = True,
                               chunk_duration: float = 15.0) -> Dict[str, Any]:
        """
        Transcribe audio with optional chunking
        
        Args:
            audio_path: Path to audio file
            enable_chunking: Whether to use chunking (True for better performance)
            chunk_duration: Duration of chunks if chunking enabled
        """
        if enable_chunking:
            # Update chunk duration if different from default
            if chunk_duration != self.pipeline.chunker.chunk_duration:
                self.pipeline.chunker.chunk_duration = chunk_duration
            
            return self.pipeline.process_audio_file(audio_path)
        else:
            # Fallback to regular transcription
            start_time = time.time()
            result = self.pipeline.transcriber.transcription_service.transcribe_audio(audio_path)
            processing_time = time.time() - start_time
            
            # Get audio duration
            try:
                import soundfile as sf
                audio_info = sf.info(audio_path)
                audio_duration = audio_info.duration
                realtime_factor = processing_time / audio_duration
            except:
                audio_duration = 0
                realtime_factor = 0
            
            return {
                "success": result.success,
                "final_text": result.text,
                "audio_duration": audio_duration,
                "processing_time": processing_time,
                "realtime_factor": realtime_factor,
                "speed_improvement": 0,  # No chunking benefit
                "chunking_enabled": False,
                "error": getattr(result, 'error', None) if not result.success else None
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get overall performance statistics"""
        return {
            "chunker_stats": self.pipeline.chunker.get_stats(),
            "transcriber_stats": self.pipeline.transcriber.get_stats()
        }

# FastAPI integration
def setup_chunked_transcription_routes(app, transcription_service, vad_service=None):
    """Setup FastAPI routes for chunked transcription"""
    
    chunked_service = VerbaChunkedTranscriptionService(transcription_service, vad_service)
    
    @app.post("/api/transcription/chunked")
    async def chunked_transcription(request: dict):
        """Transcribe audio using optimized chunking"""
        audio_path = request.get("audio_path")
        enable_chunking = request.get("enable_chunking", True)
        chunk_duration = request.get("chunk_duration", 15.0)
        
        if not audio_path or not os.path.exists(audio_path):
            return {"success": False, "error": "Audio file not found"}
        
        try:
            result = chunked_service.transcribe_with_chunking(
                audio_path, 
                enable_chunking, 
                chunk_duration
            )
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @app.get("/api/transcription/performance")
    async def get_transcription_performance():
        """Get transcription performance statistics"""
        return chunked_service.get_performance_stats()

# Testing function
def test_chunked_transcription(audio_path: str, transcription_service):
    """Test the chunked transcription system"""
    print("🔄 Testing Chunked Transcription System...")
    
    # Test with chunking enabled
    chunked_service = VerbaChunkedTranscriptionService(transcription_service)
    
    print("📊 Testing with 15-second chunks...")
    result_chunked = chunked_service.transcribe_with_chunking(audio_path, enable_chunking=True)
    
    print("📊 Testing without chunking...")  
    result_normal = chunked_service.transcribe_with_chunking(audio_path, enable_chunking=False)
    
    # Compare results
    print("\n🔍 PERFORMANCE COMPARISON")
    print("=" * 40)
    
    if result_chunked["success"] and result_normal["success"]:
        chunked_time = result_chunked["processing_time"]
        normal_time = result_normal["processing_time"]
        improvement = (normal_time - chunked_time) / normal_time if normal_time > 0 else 0
        
        print(f"⚡ Normal Processing: {normal_time:.2f}s")
        print(f"🚀 Chunked Processing: {chunked_time:.2f}s")
        print(f"📈 Speed Improvement: {improvement*100:.1f}%")
        print(f"🎯 Chunked Realtime Factor: {result_chunked['realtime_factor']:.2f}x")
        
        if improvement > 0.15:
            print("✅ CHUNKING PROVIDES SIGNIFICANT BENEFIT!")
        elif improvement > 0:
            print("⚠️ CHUNKING PROVIDES MODEST BENEFIT")
        else:
            print("❌ CHUNKING DOESN'T IMPROVE PERFORMANCE")
    else:
        print("❌ One or both tests failed")
        if not result_chunked["success"]:
            print(f"Chunked error: {result_chunked.get('error')}")
        if not result_normal["success"]:
            print(f"Normal error: {result_normal.get('error')}")

if __name__ == "__main__":
    # Example usage
    print("🎯 Optimized Audio Chunking System Ready")
    print("Use this system to improve transcription speed on low-end devices!")
    print("Recommended settings:")
    print("  - Chunk duration: 15 seconds")  
    print("  - Max workers: 2 (for 4GB RAM)")
    print("  - Enable VAD: True (for best efficiency)")
