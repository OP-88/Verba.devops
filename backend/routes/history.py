"""
History and export endpoints for Verba AI Transcription System
"""

import json
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io
import logging

from ..models.database import DatabaseManager
from ..models.transcription_models import TranscriptionResponse

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db_manager():
    """Dependency to get database manager"""
    return DatabaseManager()

@router.get("/history", response_model=List[TranscriptionResponse])
async def get_transcription_history(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session_id: Optional[str] = Query(default=None),
    db: DatabaseManager = Depends(get_db_manager)
):
    """
    Get transcription history with pagination
    
    - **limit**: Maximum number of results (1-500)
    - **offset**: Number of results to skip
    - **session_id**: Filter by session ID (optional)
    """
    try:
        transcriptions = db.get_all_transcriptions(
            limit=limit,
            offset=offset,
            session_id=session_id
        )
        
        # Convert to response models
        result = []
        for t in transcriptions:
            result.append(TranscriptionResponse(
                id=t['id'],
                text=t['text'],
                confidence=t['confidence'] or 0.0,
                language=t['language'] or 'en',
                duration=t['duration'] or 0.0,
                created_at=t['created_at'] or '',
                file_name=t['file_name'] or '',
                file_size=t['file_size'] or 0,
                segments=t['segments'] or []
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Get a specific transcription by ID"""
    try:
        transcription = db.get_transcription(transcription_id)
        
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        return TranscriptionResponse(
            id=transcription['id'],
            text=transcription['text'],
            confidence=transcription['confidence'] or 0.0,
            language=transcription['language'] or 'en',
            duration=transcription['duration'] or 0.0,
            created_at=transcription['created_at'] or '',
            file_name=transcription['file_name'] or '',
            file_size=transcription['file_size'] or 0,
            segments=transcription['segments'] or []
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get transcription {transcription_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve transcription: {str(e)}")

@router.delete("/history/{transcription_id}")
async def delete_transcription(
    transcription_id: int,
    db: DatabaseManager = Depends(get_db_manager)
):
    """Delete a specific transcription"""
    try:
        success = db.delete_transcription(transcription_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        return {"message": "Transcription deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to delete transcription {transcription_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete transcription: {str(e)}")

@router.get("/search")
async def search_transcriptions(
    q: str = Query(..., description="Search query"),
    limit: int = Query(default=50, ge=1, le=200),
    db: DatabaseManager = Depends(get_db_manager)
):
    """Search transcriptions by text content"""
    try:
        if len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")
        
        transcriptions = db.search_transcriptions(q, limit)
        
        # Convert to response models
        result = []
        for t in transcriptions:
            result.append(TranscriptionResponse(
                id=t['id'],
                text=t['text'],
                confidence=t['confidence'] or 0.0,
                language=t['language'] or 'en',
                duration=t['duration'] or 0.0,
                created_at=t['created_at'] or '',
                file_name=t['file_name'] or '',
                file_size=t['file_size'] or 0,
                segments=t['segments'] or []
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/export/{transcription_id}/{format}")
async def export_transcription(
    transcription_id: int,
    format: str,
    db: DatabaseManager = Depends(get_db_manager)
):
    """
    Export transcription in specified format
    
    - **transcription_id**: ID of the transcription to export
    - **format**: Export format (txt, json, srt)
    """
    
    # Validate format
    if format not in ['txt', 'json', 'srt']:
        raise HTTPException(status_code=400, detail="Supported formats: txt, json, srt")
    
    try:
        # Get transcription
        transcription = db.get_transcription(transcription_id)
        if not transcription:
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        # Generate content based on format
        if format == 'txt':
            content = transcription['text']
            media_type = 'text/plain'
            filename = f"transcription_{transcription_id}.txt"
            
        elif format == 'json':
            content = json.dumps({
                'id': transcription['id'],
                'text': transcription['text'],
                'confidence': transcription['confidence'],
                'language': transcription['language'],
                'duration': transcription['duration'],
                'created_at': transcription['created_at'],
                'file_name': transcription['file_name'],
                'file_size': transcription['file_size'],
                'segments': transcription['segments']
            }, indent=2)
            media_type = 'application/json'
            filename = f"transcription_{transcription_id}.json"
            
        elif format == 'srt':
            # Generate SRT format
            segments = transcription['segments'] or []
            if not segments:
                # If no segments, create one for the entire transcription
                segments = [{
                    'start': 0,
                    'end': transcription['duration'] or 60,
                    'text': transcription['text']
                }]
            
            srt_content = []
            for i, segment in enumerate(segments, 1):
                start_time = format_srt_time(segment['start'])
                end_time = format_srt_time(segment['end'])
                srt_content.append(f"{i}\n{start_time} --> {end_time}\n{segment['text']}\n")
            
            content = '\n'.join(srt_content)
            media_type = 'text/plain'
            filename = f"transcription_{transcription_id}.srt"
        
        # Return file as download
        return Response(
            content=content.encode('utf-8'),
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Export failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    milliseconds = int((secs % 1) * 1000)
    whole_seconds = int(secs)
    
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"

@router.get("/statistics")
async def get_statistics(db: DatabaseManager = Depends(get_db_manager)):
    """Get transcription statistics"""
    try:
        stats = db.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")