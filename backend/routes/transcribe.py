"""
Transcription endpoints for Verba AI Transcription System
"""

import os
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..models.database import DatabaseManager
from ..services.whisper_service import WhisperService
from ..models.transcription_models import TranscriptionResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Supported audio formats
SUPPORTED_FORMATS = {'.wav', '.mp3', '.m4a', '.flac', '.ogg', '.webm', '.mp4'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

def get_db_manager():
    """Dependency to get database manager"""
    return DatabaseManager()

def get_whisper_service():
    """Dependency to get whisper service"""
    return WhisperService()

def validate_audio_file(file: UploadFile) -> None:
    """Validate uploaded audio file"""
    
    # Check file size
    if hasattr(file.file, 'seek') and hasattr(file.file, 'tell'):
        # Get file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB"
            )
    
    # Check file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported format. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )
    
    # Check MIME type
    if file.content_type and not (
        file.content_type.startswith('audio/') or 
        file.content_type.startswith('video/') or
        file.content_type == 'application/octet-stream'
    ):
        raise HTTPException(
            status_code=415,
            detail="Invalid content type. Please upload an audio file."
        )

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    session_id: str = Form(default="default"),
    meeting_title: str = Form(default=""),
    db: DatabaseManager = Depends(get_db_manager),
    whisper: WhisperService = Depends(get_whisper_service)
):
    """
    Transcribe uploaded audio file using Whisper AI
    
    - **audio**: Audio file (WAV, MP3, M4A, FLAC, OGG, WebM, MP4)
    - **session_id**: Session identifier for grouping transcriptions
    - **meeting_title**: Optional title for the meeting/recording
    """
    
    # Validate input
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
    
    # Validate file
    validate_audio_file(audio)
    
    # Check if Whisper service is ready
    if not whisper.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Transcription service is not ready. Please try again in a few moments."
        )
    
    # Save uploaded file temporarily
    temp_file = None
    try:
        # Read file content
        content = await audio.read()
        
        # Create temporary file
        suffix = Path(audio.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(content)
            temp_file = tmp_file.name
        
        logger.info(f"📁 Processing file: {audio.filename} ({len(content)} bytes)")
        
        # Transcribe audio
        transcription_options = {
            'meeting_title': meeting_title,
            'session_id': session_id
        }
        
        result = await whisper.transcribe(content, transcription_options)
        
        if 'error' in result:
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Save to database
        transcription_id = db.insert_transcription(
            text=result['text'],
            confidence=result.get('confidence', 0.0),
            language=result.get('language', 'en'),
            duration=result.get('duration', 0.0),
            file_name=audio.filename,
            file_size=len(content),
            segments=result.get('segments', []),
            session_id=session_id,
            processing_time=result.get('processing_time', 0.0),
            model_used=whisper.model_size
        )
        
        # Update session activity
        db.update_session_activity(session_id)
        
        logger.info(f"✅ Transcription completed: ID={transcription_id}")
        
        # Return response
        return TranscriptionResponse(
            id=transcription_id,
            text=result['text'],
            confidence=result.get('confidence', 0.0),
            language=result.get('language', 'en'),
            duration=result.get('duration', 0.0),
            created_at=result.get('created_at', ''),
            file_name=audio.filename,
            file_size=len(content),
            segments=result.get('segments', [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transcription failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.warning(f"⚠️  Failed to cleanup temp file: {e}")

@router.get("/transcribe/formats")
async def get_supported_formats():
    """Get list of supported audio formats"""
    return {
        "supported_formats": list(SUPPORTED_FORMATS),
        "max_file_size_mb": MAX_FILE_SIZE // 1024 // 1024,
        "description": "Supported audio formats for transcription"
    }

@router.get("/transcribe/status")
async def get_transcription_status(whisper: WhisperService = Depends(get_whisper_service)):
    """Get current transcription service status"""
    return {
        "service_ready": whisper.is_ready(),
        "model_info": whisper.get_model_info() if whisper.is_ready() else None,
        "uptime_seconds": whisper.get_uptime()
    }