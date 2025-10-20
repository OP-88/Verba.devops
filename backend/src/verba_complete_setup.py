#!/usr/bin/env python3
"""
🎯 VERBA COMPLETE SETUP - FIXED VERSION
Complete integration of transcription and AI assistant services
"""

import os
import sys
import time
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import torch
import whisper
import librosa
import webrtcvad
import soundfile as sf
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """Enhanced transcription result with metadata"""
    text: str
    confidence: float
    duration: float
    processing_time: float
    model_used: str
    chunks_processed: int = 0
    vad_segments: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AudioSegment:
    """Audio segment detected by VAD"""
    start_time: float
    end_time: float
    audio_data: np.ndarray
    sample_rate: int
    confidence: float = 1.0

class CompatibleVADService:
    """WebRTC VAD service with unified interface"""
    
    def __init__(self, aggressiveness: int = 2):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = 16000  # WebRTC VAD requires 16kHz
        logger.info(f"✅ VAD Service initialized (aggressiveness: {aggressiveness})")
    
    def preprocess_audio(self, audio_data: np.ndarray, original_sr: int) -> np.ndarray:
        """Preprocess audio for VAD compatibility"""
        # Resample to 16kHz if needed
        if original_sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=self.sample_rate)
        
        # Ensure proper dtype and range
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Normalize to [-1, 1] range
        audio_data = np.clip(audio_data, -1.0, 1.0)
        
        # Convert to int16 for WebRTC VAD
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        return audio_int16
    
    def detect_voice_segments(self, audio_data: np.ndarray, sample_rate: int) -> List[AudioSegment]:
        """Detect voice segments using WebRTC VAD"""
        try:
            # Preprocess audio
            audio_int16 = self.preprocess_audio(audio_data, sample_rate)
            
            # Frame settings for WebRTC VAD
            frame_duration = 30  # ms
            frame_length = int(self.sample_rate * frame_duration / 1000)  # 480 samples at 16kHz
            
            segments = []
            current_segment_start = None
            
            # Process audio in frames
            for i in range(0, len(audio_int16) - frame_length + 1, frame_length):
                frame = audio_int16[i:i + frame_length]
                
                # Ensure frame is exactly the right size
                if len(frame) < frame_length:
                    frame = np.pad(frame, (0, frame_length - len(frame)), mode='constant')
                
                # Convert to bytes for WebRTC VAD
                frame_bytes = frame.tobytes()
                
                try:
                    is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
                except Exception as e:
                    logger.warning(f"VAD frame processing error: {e}")
                    is_speech = True  # Fallback: assume speech
                
                current_time = i / self.sample_rate
                
                if is_speech and current_segment_start is None:
                    current_segment_start = current_time
                elif not is_speech and current_segment_start is not None:
                    # End of speech segment
                    segment = AudioSegment(
                        start_time=current_segment_start,
                        end_time=current_time,
                        audio_data=audio_data[int(current_segment_start * sample_rate):int(current_time * sample_rate)],
                        sample_rate=sample_rate
                    )
                    segments.append(segment)
                    current_segment_start = None
            
            # Handle case where audio ends with speech
            if current_segment_start is not None:
                segment = AudioSegment(
                    start_time=current_segment_start,
                    end_time=len(audio_data) / sample_rate,
                    audio_data=audio_data[int(current_segment_start * sample_rate):],
                    sample_rate=sample_rate
                )
                segments.append(segment)
            
            logger.info(f"✅ Detected {len(segments)} voice segments")
            return segments
            
        except Exception as e:
            logger.error(f"❌ VAD processing failed: {e}")
            # Fallback: return entire audio as one segment
            return [AudioSegment(
                start_time=0.0,
                end_time=len(audio_data) / sample_rate,
                audio_data=audio_data,
                sample_rate=sample_rate,
                confidence=0.5
            )]

class EnhancedTranscriptionService:
    """Enhanced transcription service with VAD integration"""
    
    def __init__(self, model_size: str = "tiny"):
        self.model_size = model_size
        self.model = None
        self.vad_service = CompatibleVADService(aggressiveness=2)
        self.stats = {
            'total_transcriptions': 0,
            'total_processing_time': 0.0,
            'average_confidence': 0.0
        }
        
    def load_model(self) -> bool:
        """Load Whisper model"""
        try:
            start_time = time.time()
            logger.info(f"🤖 Loading Whisper {self.model_size} model...")
            
            self.model = whisper.load_model(self.model_size)
            
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded in {load_time:.2f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            return False
    
    def transcribe_audio(self, audio_file_path: str) -> TranscriptionResult:
        """Transcribe audio file with VAD optimization"""
        if not self.model:
            if not self.load_model():
                raise RuntimeError("Failed to load transcription model")
        
        start_time = time.time()
        
        try:
            # Load audio
            logger.info(f"🎵 Loading audio: {audio_file_path}")
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None)
            audio_duration = len(audio_data) / sample_rate
            
            # Detect voice segments
            logger.info("🔍 Detecting voice segments...")
            voice_segments = self.vad_service.detect_voice_segments(audio_data, sample_rate)
            
            if not voice_segments:
                logger.warning("⚠️ No voice segments detected, processing entire audio")
                voice_segments = [AudioSegment(
                    start_time=0.0,
                    end_time=audio_duration,
                    audio_data=audio_data,
                    sample_rate=sample_rate
                )]
            
            # Transcribe segments
            transcriptions = []
            for i, segment in enumerate(voice_segments):
                logger.info(f"🎙️ Transcribing segment {i+1}/{len(voice_segments)}")
                
                # Use Whisper's direct API
                result = self.model.transcribe(
                    segment.audio_data,
                    fp16=False,  # Disable FP16 for CPU compatibility
                    language='en'
                )
                
                transcriptions.append(result["text"].strip())
            
            # Combine transcriptions
            final_text = " ".join(transcriptions)
            processing_time = time.time() - start_time
            
            # Update statistics
            self.stats['total_transcriptions'] += 1
            self.stats['total_processing_time'] += processing_time
            
            # Create result
            result = TranscriptionResult(
                text=final_text,
                confidence=0.95,  # Placeholder confidence
                duration=audio_duration,
                processing_time=processing_time,
                model_used=self.model_size,
                chunks_processed=len(voice_segments),
                vad_segments=len(voice_segments),
                metadata={
                    'sample_rate': sample_rate,
                    'file_path': audio_file_path,
                    'segments_count': len(voice_segments)
                }
            )
            
            logger.info(f"✅ Transcription completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            raise

# OpenRouter AI Assistant Integration
import requests

class OpenRouterAIAssistant:
    """OpenRouter AI Assistant for meeting analysis"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3.5-sonnet"
        self.context_history = []
        
        logger.info("✅ OpenRouter AI Assistant initialized")
    
    def chat(self, message: str, include_context: bool = True) -> str:
        """Send a chat message to the AI assistant"""
        try:
            messages = []
            
            if include_context and self.context_history:
                messages.extend(self.context_history)
            
            messages.append({"role": "user", "content": message})
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code}")
            
            result = response.json()
            assistant_message = result['choices'][0]['message']['content']
            
            # Update context
            self.context_history.append({"role": "user", "content": message})
            self.context_history.append({"role": "assistant", "content": assistant_message})
            
            # Keep only last 10 exchanges
            if len(self.context_history) > 20:
                self.context_history = self.context_history[-20:]
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"❌ Chat request failed: {e}")
            return f"I apologize, but I'm having trouble processing your request: {e}"
    
    def add_transcription_context(self, transcription: str, title: str = "Meeting Transcription"):
        """Add transcription to the conversation context"""
        context_message = f"Here's a {title.lower()}: {transcription}"
        self.context_history.append({"role": "user", "content": context_message})
        logger.info(f"Added transcription context: {title} ({len(transcription)} chars)")
    
    def analyze_transcription(self, transcription: str) -> str:
        """Analyze a transcription for key insights"""
        prompt = f"""
        Please analyze this meeting transcription and provide:
        1. Key points discussed
        2. Action items and decisions made  
        3. Next steps or follow-up needed
        4. Any important deadlines mentioned
        
        Transcription: {transcription}
        """
        return self.chat(prompt, include_context=False)
    
    def suggest_questions(self, transcription: str) -> List[str]:
        """Generate follow-up questions based on transcription"""
        prompt = f"""
        Based on this transcription, suggest 5 relevant follow-up questions that would help clarify or expand on the discussion:
        
        Transcription: {transcription}
        
        Please provide exactly 5 questions, each on a new line starting with a number.
        """
        
        response = self.chat(prompt, include_context=False)
        
        # Extract questions from response
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # Remove numbering and clean up
                question = line.split('.', 1)[-1].strip()
                question = question.lstrip('- ')
                if question and question.endswith('?'):
                    questions.append(question)
        
        return questions[:5]  # Return max 5 questions

class VerbaIntegratedSystem:
    """Complete Verba system integrating transcription and AI assistant"""
    
    def __init__(self):
        self.transcription_service = EnhancedTranscriptionService()
        self.ai_assistant = None
        
        # Initialize AI assistant if API key is available
        try:
            self.ai_assistant = OpenRouterAIAssistant()
            logger.info("✅ AI Assistant integrated")
        except Exception as e:
            logger.warning(f"⚠️ AI Assistant not available: {e}")
    
    def process_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Process audio file with full pipeline"""
        try:
            # Transcribe audio
            transcription_result = self.transcription_service.transcribe_audio(file_path)
            
            result = {
                "transcription": asdict(transcription_result),
                "ai_analysis": None,
                "suggested_questions": []
            }
            
            # Add AI analysis if available
            if self.ai_assistant and transcription_result.text.strip():
                try:
                    # Add context and analyze
                    self.ai_assistant.add_transcription_context(
                        transcription_result.text,
                        f"Audio Transcription ({Path(file_path).name})"
                    )
                    
                    result["ai_analysis"] = self.ai_assistant.analyze_transcription(
                        transcription_result.text
                    )
                    
                    result["suggested_questions"] = self.ai_assistant.suggest_questions(
                        transcription_result.text
                    )
                    
                except Exception as e:
                    logger.error(f"❌ AI analysis failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Audio processing failed: {e}")
            raise

# FastAPI Application
def create_verba_app() -> FastAPI:
    """Create the FastAPI application"""
    app = FastAPI(
        title="Verba - Enhanced Transcription Service",
        description="AI-powered meeting transcription and analysis",
        version="2.0.0"
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize system
    verba_system = VerbaIntegratedSystem()
    
    @app.get("/")
    async def root():
        return {
            "service": "Verba Enhanced Transcription",
            "version": "2.0.0",
            "status": "operational",
            "features": {
                "transcription": True,
                "vad_optimization": True,
                "ai_analysis": verba_system.ai_assistant is not None
            }
        }
    
    @app.post("/transcribe")
    async def transcribe_audio(file: UploadFile = File(...)):
        """Transcribe uploaded audio file"""
        if not file.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a')):
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        try:
            # Save uploaded file temporarily
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Process audio
            result = verba_system.process_audio_file(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            return JSONResponse(content=result)
            
        except Exception as e:
            logger.error(f"❌ Transcription endpoint failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/chat")
    async def chat_with_ai(message: dict):
        """Chat with AI assistant"""
        if not verba_system.ai_assistant:
            raise HTTPException(status_code=503, detail="AI Assistant not available")
        
        try:
            user_message = message.get("message", "")
            if not user_message:
                raise HTTPException(status_code=400, detail="Message is required")
            
            response = verba_system.ai_assistant.chat(user_message)
            return {"response": response}
            
        except Exception as e:
            logger.error(f"❌ Chat endpoint failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/stats")
    async def get_stats():
        """Get transcription statistics"""
        stats = verba_system.transcription_service.stats
        return {
            "transcription_stats": stats,
            "ai_assistant_available": verba_system.ai_assistant is not None,
            "system_status": "operational"
        }
    
    return app

def test_verba_system():
    """Test the complete Verba system"""
    print("🧪 Testing Verba Integrated System...")
    
    try:
        # Test transcription service
        transcription_service = EnhancedTranscriptionService("tiny")
        if transcription_service.load_model():
            print("✅ Transcription service ready")
        
        # Test AI assistant if available
        if os.getenv('OPENROUTER_API_KEY'):
            ai_assistant = OpenRouterAIAssistant()
            test_response = ai_assistant.chat("Hello, can you help me analyze meeting notes?")
            print(f"✅ AI Assistant test: {test_response[:100]}...")
        else:
            print("⚠️ AI Assistant not tested (no API key)")
        
        print("🎉 System testing complete!")
        
    except Exception as e:
        print(f"❌ System test failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_verba_system()
    else:
        print("🎯 Verba Integrated System")
        print("Use: python verba_complete_setup.py test")
        print("Or import VerbaIntegratedSystem in your application")
