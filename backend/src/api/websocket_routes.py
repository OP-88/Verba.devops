#!/usr/bin/env python3
"""
WebSocket routes for real-time transcription streaming
Provides live audio transcription with minimal latency
"""

import os
import json
import asyncio
import tempfile
import logging
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from fastapi.routing import APIRouter
import numpy as np

from ..services.enhanced_transcription_service import create_enhanced_transcription_service

logger = logging.getLogger(__name__)

# Global service instance
transcription_service = None

def initialize_transcription_service():
    """Initialize the global transcription service"""
    global transcription_service
    if transcription_service is None:
        transcription_service = create_enhanced_transcription_service(model_size="base")
        logger.info("✅ WebSocket transcription service initialized")

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time transcription"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_sessions: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept and manage new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # Initialize session data
        self.connection_sessions[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "session_start": datetime.now(),
            "chunks_processed": 0,
            "total_audio_duration": 0.0
        }
        
        logger.info(f"🔗 WebSocket connected: {self.connection_sessions[websocket]['client_id']}")
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
            if websocket in self.connection_sessions:
                session_info = self.connection_sessions[websocket]
                logger.info(f"🔌 WebSocket disconnected: {session_info['client_id']} "
                           f"(processed {session_info['chunks_processed']} chunks)")
                del self.connection_sessions[websocket]
    
    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message to specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"❌ Failed to send message to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager
manager = ConnectionManager()

# WebSocket router
websocket_router = APIRouter()

@websocket_router.websocket("/ws/transcribe")
async def websocket_transcribe_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription
    
    Expected message format:
    {
        "type": "audio_chunk",
        "data": "base64_encoded_audio",
        "sample_rate": 16000,
        "format": "wav|mp3|flac",
        "chunk_id": "unique_chunk_identifier",
        "metadata": {...}
    }
    
    Response format:
    {
        "type": "transcription_segment",
        "chunk_id": "unique_chunk_identifier", 
        "text": "transcribed text",
        "start_time": 0.0,
        "end_time": 2.5,
        "speaker": "Speaker 1",
        "confidence": 0.95,
        "processing_time": 0.8
    }
    """
    
    # Initialize service if needed
    initialize_transcription_service()
    
    client_id = websocket.query_params.get("client_id", "anonymous")
    await manager.connect(websocket, client_id)
    
    try:
        # Send initial connection confirmation
        await manager.send_message(websocket, {
            "type": "connection_established",
            "client_id": client_id,
            "services_available": transcription_service.get_service_stats()["services_available"],
            "message": "Ready for real-time transcription"
        })
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError as e:
                await manager.send_message(websocket, {
                    "type": "error",
                    "error": f"Invalid JSON: {str(e)}"
                })
                continue
            
            # Handle different message types
            if message.get("type") == "audio_chunk":
                await handle_audio_chunk(websocket, message)
            
            elif message.get("type") == "audio_file":
                await handle_audio_file(websocket, message)
            
            elif message.get("type") == "ping":
                await manager.send_message(websocket, {"type": "pong"})
            
            elif message.get("type") == "get_stats":
                session_info = manager.connection_sessions[websocket]
                await manager.send_message(websocket, {
                    "type": "stats",
                    "session_stats": session_info,
                    "service_stats": transcription_service.get_service_stats()
                })
            
            else:
                await manager.send_message(websocket, {
                    "type": "error",
                    "error": f"Unknown message type: {message.get('type')}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        await manager.send_message(websocket, {
            "type": "error",
            "error": str(e)
        })
        manager.disconnect(websocket)

async def handle_audio_chunk(websocket: WebSocket, message: Dict[str, Any]):
    """Process real-time audio chunk"""
    try:
        import base64
        import io
        import wave
        
        chunk_id = message.get("chunk_id", f"chunk_{datetime.now().timestamp()}")
        audio_data = message.get("data", "")
        sample_rate = message.get("sample_rate", 16000)
        audio_format = message.get("format", "wav")
        
        if not audio_data:
            await manager.send_message(websocket, {
                "type": "error",
                "chunk_id": chunk_id,
                "error": "No audio data provided"
            })
            return
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            await manager.send_message(websocket, {
                "type": "error",
                "chunk_id": chunk_id,
                "error": f"Failed to decode audio data: {str(e)}"
            })
            return
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            # Process with enhanced transcription service
            result = transcription_service.transcribe_audio(
                temp_path,
                include_diarization=True,
                include_summary=False  # Skip summary for real-time chunks
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Update session stats
            session = manager.connection_sessions[websocket]
            session["chunks_processed"] += 1
            session["total_audio_duration"] += result.audio_duration
            
            # Send transcription result
            if result.text.strip():
                response = {
                    "type": "transcription_chunk",
                    "chunk_id": chunk_id,
                    "text": result.text,
                    "segments": [
                        {
                            "start_time": seg.start_time,
                            "end_time": seg.end_time,
                            "text": seg.text,
                            "speaker": seg.speaker,
                            "confidence": seg.confidence
                        } for seg in result.segments
                    ],
                    "speakers": result.speakers,
                    "processing_time": processing_time,
                    "audio_duration": result.audio_duration,
                    "quality_metrics": result.quality_metrics
                }
            else:
                response = {
                    "type": "transcription_chunk",
                    "chunk_id": chunk_id,
                    "text": "",
                    "message": "No speech detected in audio chunk",
                    "processing_time": processing_time
                }
            
            await manager.send_message(websocket, response)
            
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    
    except Exception as e:
        logger.error(f"❌ Failed to process audio chunk: {e}")
        await manager.send_message(websocket, {
            "type": "error",
            "chunk_id": message.get("chunk_id", "unknown"),
            "error": str(e)
        })

async def handle_audio_file(websocket: WebSocket, message: Dict[str, Any]):
    """Process complete audio file with streaming results"""
    try:
        import base64
        
        file_id = message.get("file_id", f"file_{datetime.now().timestamp()}")
        audio_data = message.get("data", "")
        filename = message.get("filename", "audio.wav")
        include_diarization = message.get("include_diarization", True)
        include_summary = message.get("include_summary", True)
        
        if not audio_data:
            await manager.send_message(websocket, {
                "type": "error",
                "file_id": file_id,
                "error": "No audio data provided"
            })
            return
        
        # Send processing start notification
        await manager.send_message(websocket, {
            "type": "processing_started",
            "file_id": file_id,
            "filename": filename,
            "include_diarization": include_diarization,
            "include_summary": include_summary
        })
        
        # Decode and save audio
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            await manager.send_message(websocket, {
                "type": "error", 
                "file_id": file_id,
                "error": f"Failed to decode audio: {str(e)}"
            })
            return
        
        # Determine file extension
        file_extension = os.path.splitext(filename)[1] or '.wav'
        
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            # Stream transcription results
            async for stream_result in transcription_service.transcribe_audio_stream(temp_path):
                stream_result["file_id"] = file_id
                await manager.send_message(websocket, stream_result)
            
            # Update session stats
            session = manager.connection_sessions[websocket]
            session["chunks_processed"] += 1
            
        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
    
    except Exception as e:
        logger.error(f"❌ Failed to process audio file: {e}")
        await manager.send_message(websocket, {
            "type": "error",
            "file_id": message.get("file_id", "unknown"),
            "error": str(e)
        })

@websocket_router.websocket("/ws/live")
async def websocket_live_transcription(websocket: WebSocket):
    """
    WebSocket endpoint for live microphone transcription
    Optimized for continuous audio streaming
    """
    
    initialize_transcription_service()
    client_id = websocket.query_params.get("client_id", "live_client")
    await manager.connect(websocket, client_id)
    
    try:
        await manager.send_message(websocket, {
            "type": "live_session_started",
            "client_id": client_id,
            "message": "Ready for live transcription",
            "recommended_chunk_size": 1024,  # samples
            "recommended_sample_rate": 16000
        })
        
        audio_buffer = []
        buffer_duration = 2.0  # Process every 2 seconds
        sample_rate = 16000
        
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "live_audio":
                # Accumulate audio data
                audio_chunk = message.get("data", [])
                audio_buffer.extend(audio_chunk)
                
                # Process when buffer is full
                if len(audio_buffer) >= buffer_duration * sample_rate:
                    # Convert to numpy array
                    audio_array = np.array(audio_buffer, dtype=np.float32)
                    
                    # Create temporary WAV file
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                        import wave
                        with wave.open(temp_file.name, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(sample_rate)
                            
                            # Convert float to int16
                            audio_int16 = (audio_array * 32767).astype(np.int16)
                            wav_file.writeframes(audio_int16.tobytes())
                        
                        temp_path = temp_file.name
                    
                    try:
                        # Quick transcription (no diarization for live)
                        result = transcription_service.transcribe_audio(
                            temp_path,
                            include_diarization=False,
                            include_summary=False
                        )
                        
                        if result.text.strip():
                            await manager.send_message(websocket, {
                                "type": "live_transcription",
                                "text": result.text,
                                "timestamp": datetime.now().isoformat(),
                                "confidence": result.quality_metrics.get("avg_confidence", 0.0),
                                "processing_time": result.processing_time
                            })
                    
                    finally:
                        os.unlink(temp_path)
                    
                    # Clear buffer (with small overlap)
                    overlap_samples = int(0.5 * sample_rate)
                    audio_buffer = audio_buffer[-overlap_samples:]
            
            elif message.get("type") == "stop_live":
                break
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Live transcription error: {e}")
        manager.disconnect(websocket)

# Health check for WebSocket services
async def websocket_health_check():
    """Check WebSocket service health"""
    return {
        "websocket_service": "healthy",
        "active_connections": len(manager.active_connections),
        "transcription_service_available": transcription_service is not None,
        "services_status": transcription_service.get_service_stats()["services_available"] if transcription_service else {}
    }