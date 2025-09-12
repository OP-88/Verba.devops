"""
Health check endpoints for Verba AI Transcription System
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
import psutil
import platform
from typing import Dict, Any

from ..models.database import DatabaseManager
from ..services.whisper_service import WhisperService

router = APIRouter()

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: str
    model: str
    model_size: str
    enhanced_features: bool
    librosa_available: bool
    system_info: Dict[str, Any]
    performance: Dict[str, Any]

def get_db_manager():
    """Dependency to get database manager"""
    return DatabaseManager()

def get_whisper_service():
    """Dependency to get whisper service"""
    return WhisperService()

@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: DatabaseManager = Depends(get_db_manager),
    whisper: WhisperService = Depends(get_whisper_service)
):
    """Comprehensive health check"""
    
    # Check database
    db_status = "operational" if db.health_check() else "error"
    
    # Check Whisper model
    model_status = "loaded" if whisper.is_ready() else "not_loaded"
    
    # System information
    system_info = {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "available_memory_gb": round(psutil.virtual_memory().available / 1024**3, 2),
        "total_memory_gb": round(psutil.virtual_memory().total / 1024**3, 2)
    }
    
    # Performance metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    
    performance = {
        "cpu_usage_percent": cpu_percent,
        "memory_usage_percent": memory.percent,
        "memory_available_gb": round(memory.available / 1024**3, 2),
        "disk_usage_percent": psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:').percent
    }
    
    # Overall status
    overall_status = "healthy" if db_status == "operational" and model_status == "loaded" else "degraded"
    
    # Check for enhanced features
    enhanced_features = True
    librosa_available = True
    
    try:
        import librosa
    except ImportError:
        librosa_available = False
    
    try:
        import sklearn
        import textstat
        import scipy
    except ImportError:
        enhanced_features = False
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        database=db_status,
        model=model_status,
        model_size=whisper.model_size if whisper.is_ready() else "unknown",
        enhanced_features=enhanced_features,
        librosa_available=librosa_available,
        system_info=system_info,
        performance=performance
    )

@router.get("/health/quick")
async def quick_health_check():
    """Quick health check for basic status"""
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health/database")
async def database_health(db: DatabaseManager = Depends(get_db_manager)):
    """Database-specific health check"""
    is_healthy = db.health_check()
    stats = db.get_statistics() if is_healthy else {}
    
    return {
        "status": "operational" if is_healthy else "error",
        "timestamp": datetime.now().isoformat(),
        "statistics": stats
    }

@router.get("/health/model")
async def model_health(whisper: WhisperService = Depends(get_whisper_service)):
    """Model-specific health check"""
    return {
        "status": "loaded" if whisper.is_ready() else "not_loaded",
        "model_info": whisper.get_model_info() if whisper.is_ready() else None,
        "timestamp": datetime.now().isoformat()
    }