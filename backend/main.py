from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import asyncio
from services.whisper_service import WhisperService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Verba Backend API",
    description="Offline AI Transcription Service",
    version="1.0.0-dev",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "tauri://localhost",
        "http://localhost:1420",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Whisper service
whisper_service = WhisperService(model_size="tiny")

@app.on_event("startup")
async def startup_event():
    """Load AI models on startup"""
    logger.info("🚀 Starting Verba Backend...")
    await whisper_service.load_model()
    logger.info("✅ Backend startup complete")

@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("🛑 Shutting down Verba Backend...")
    await whisper_service.unload_model()
    logger.info("✅ Backend shutdown complete")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Verba Backend is running!",
        "status": "healthy",
        "version": "1.0.0-dev"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        import torch
        
        model_info = whisper_service.get_model_info()
        
        return {
            "status": "ok",
            "backend": "ready",
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "whisper_loaded": model_info["is_loaded"],
            "whisper_model": model_info["model_size"]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/api/v1/system/info")
async def system_info():
    """System information"""
    try:
        import psutil
        import platform
        
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": f"{psutil.virtual_memory().total / (1024**3):.1f}GB",
            "memory_available": f"{psutil.virtual_memory().available / (1024**3):.1f}GB",
            "memory_percent": f"{psutil.virtual_memory().percent}%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"System info error: {str(e)}")

@app.post("/api/v1/transcribe/test")
async def test_transcription():
    """Test transcription with a simple audio sample"""
    try:
        # Create a simple test audio (1 second of silence)
        import numpy as np
        test_audio = np.zeros(16000, dtype=np.float32)  # 1 second of silence at 16kHz
        
        result = await whisper_service.transcribe_audio(test_audio)
        
        return {
            "status": "success",
            "message": "Transcription system is working",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription test failed: {str(e)}")

if __name__ == "__main__":
    logger.info("🎙️ Starting Verba Backend Server...")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
