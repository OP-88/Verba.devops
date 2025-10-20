#!/usr/bin/env python3
"""
WebSocket Routes for Real-time Transcription
Provides streaming audio transcription capabilities
"""

import asyncio
import json
import logging
import tempfile
import base64
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import numpy as np
import soundfile as sf

from backend.services.enhanced_transcription_service import EnhancedTranscriptionService
from backend.services.diarization_service import SpeakerDiarizationService
from backend.services.summary_service import SummarizationService
from backend.vad import vad_filter

logger = logging.getLogger(__name__)
router = APIRouter()

class WebSocketManager:
    """Manages WebSocket connections for real-time transcription"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.transcription_service = None
        self.diarization_service = None
        self.summary_service = None
        
    async def initialize_services(self):
        """Initialize AI services for transcription"""
        try:
            logger.info("🚀 Initializing WebSocket services...")
            
            # Initialize services
            self.transcription_service = EnhancedTranscriptionService()
            self.diarization_service = SpeakerDiarizationService()
            self.summary_service = SummarizationService()
            
            # Initialize asynchronously
            await asyncio.gather(
                self.diarization_service.initialize(),
                self.summary_service.initialize(),
                return_exceptions=True
            )
            
            logger.info("✅ WebSocket services initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebSocket services: {e}")
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"🔗 WebSocket client {client_id} connected")
        
        # Send connection confirmation
        await self.send_message(client_id, {
            "type": "connection",
            "status": "connected",
            "message": "Ready for real-time transcription"
        })
    
    def disconnect(self, client_id: str):
        """Remove WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"🔌 WebSocket client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def process_audio_chunk(self, client_id: str, audio_data: bytes, options: Dict[str, Any]):
        """Process streaming audio chunk"""
        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Convert to numpy array
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                # Load audio
                audio, sr = sf.read(temp_path)
                
                # Ensure mono and correct sample rate
                if len(audio.shape) > 1:
                    audio = np.mean(audio, axis=1)
                
                if sr != 16000:
                    import librosa
                    audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)
                    sr = 16000
                
                # Apply VAD if enabled
                if options.get('vad', True):
                    audio = vad_filter(audio, sr)
                
                # Skip if audio too short
                if len(audio) < sr * 0.5:  # Less than 0.5 seconds
                    await self.send_message(client_id, {
                        "type": "status",
                        "message": "Audio chunk too short, skipping..."
                    })
                    return
                
                # Save processed audio for transcription
                sf.write(temp_path, audio, sr)
                
                # Send processing status
                await self.send_message(client_id, {
                    "type": "status",
                    "message": "Processing audio chunk..."
                })
                
                # Transcribe using enhanced service
                try:
                    result = await self.transcription_service.transcribe_audio(
                        temp_path,
                        enable_vad=options.get('vad', True),
                        enable_diarization=options.get('diarization', True),
                        enable_summarization=options.get('summarization', False)  # Skip for real-time
                    )
                    
                    # Send transcription result
                    await self.send_message(client_id, {
                        "type": "transcription",
                        "text": result.text,
                        "segments": [seg.to_dict() for seg in result.segments],
                        "duration": result.duration,
                        "language": result.language,
                        "processing_time": result.processing_time
                    })
                    
                    logger.info(f"✅ Processed audio chunk for {client_id}: {len(result.text)} chars")
                    
                except Exception as e:
                    logger.error(f"❌ Transcription failed for {client_id}: {e}")
                    await self.send_message(client_id, {
                        "type": "error",
                        "message": f"Transcription failed: {str(e)}"
                    })
                
            finally:
                # Cleanup temp file
                try:
                    import os
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Audio processing failed for {client_id}: {e}")
            await self.send_message(client_id, {
                "type": "error",
                "message": f"Audio processing failed: {str(e)}"
            })
    
    async def finalize_session(self, client_id: str, session_data: Dict[str, Any]):
        """Finalize transcription session with summary"""
        try:
            if not self.summary_service or not self.summary_service.is_initialized:
                await self.send_message(client_id, {
                    "type": "session_complete",
                    "message": "Session completed (summarization not available)"
                })
                return
            
            # Get full transcript
            full_text = session_data.get('full_transcript', '')
            
            if not full_text:
                await self.send_message(client_id, {
                    "type": "session_complete",
                    "message": "Session completed (no transcript to summarize)"
                })
                return
            
            # Generate summary
            summary_result = self.summary_service.summarize_transcript(full_text)
            
            # Send final results
            await self.send_message(client_id, {
                "type": "session_summary",
                "summary": summary_result.get('summary', ''),
                "key_points": summary_result.get('key_points', []),
                "action_items": summary_result.get('action_items', []),
                "sentiment": summary_result.get('sentiment', 'neutral'),
                "word_count": summary_result.get('word_count', 0),
                "compression_ratio": summary_result.get('compression_ratio', 1.0)
            })
            
            await self.send_message(client_id, {
                "type": "session_complete",
                "message": "Session completed with summary"
            })
            
            logger.info(f"✅ Session completed for {client_id}")
            
        except Exception as e:
            logger.error(f"❌ Session finalization failed for {client_id}: {e}")
            await self.send_message(client_id, {
                "type": "error",
                "message": f"Session finalization failed: {str(e)}"
            })

# Global WebSocket manager instance
ws_manager = WebSocketManager()

@router.on_event("startup")
async def startup_websocket_services():
    """Initialize WebSocket services on startup"""
    await ws_manager.initialize_services()

@router.websocket("/ws/transcribe/{client_id}")
async def websocket_transcribe(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time transcription
    
    Expected message format:
    {
        "type": "audio_chunk",
        "data": "base64_encoded_audio_data",
        "options": {
            "vad": true,
            "diarization": true,
            "summarization": false
        }
    }
    
    Or:
    {
        "type": "finalize_session",
        "data": {
            "full_transcript": "complete transcript text..."
        }
    }
    """
    await ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
            except json.JSONDecodeError:
                await ws_manager.send_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
                continue
            
            message_type = message.get("type")
            
            if message_type == "audio_chunk":
                # Process audio chunk
                audio_data = message.get("data", "")
                options = message.get("options", {})
                
                if audio_data:
                    # Process asynchronously to avoid blocking
                    asyncio.create_task(
                        ws_manager.process_audio_chunk(client_id, audio_data, options)
                    )
                else:
                    await ws_manager.send_message(client_id, {
                        "type": "error",
                        "message": "No audio data provided"
                    })
            
            elif message_type == "finalize_session":
                # Finalize session with summary
                session_data = message.get("data", {})
                await ws_manager.finalize_session(client_id, session_data)
            
            elif message_type == "ping":
                # Respond to ping
                await ws_manager.send_message(client_id, {
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                })
            
            else:
                await ws_manager.send_message(client_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"🔌 Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error for {client_id}: {e}")
    finally:
        ws_manager.disconnect(client_id)

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket service status"""
    return {
        "status": "active",
        "active_connections": len(ws_manager.active_connections),
        "services_initialized": {
            "transcription": ws_manager.transcription_service is not None,
            "diarization": ws_manager.diarization_service and ws_manager.diarization_service.is_initialized,
            "summarization": ws_manager.summary_service and ws_manager.summary_service.is_initialized
        }
    }