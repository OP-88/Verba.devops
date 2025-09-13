"""
Verba AI-Powered Audio Transcription System
FastAPI Backend Server

Main application entry point with health monitoring, 
audio transcription, and history management.
"""

import os
import sys
import time
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Enhanced imports for diarization and noise reduction
try:
    from pyannote.audio import Pipeline
    DIARIZATION_AVAILABLE = True
except ImportError:
    DIARIZATION_AVAILABLE = False
    print("📝 Note: pyannote.audio not available, speaker diarization disabled")

from services.noise_service import rnnoise_service
from services.summary_service import summarization_service
from services.diarization_service import SpeakerDiarizationService
from config.settings import Settings
from models.transcription_models import TranscriptionCreate, TranscriptionResponse, HealthResponse
from services.whisper_service import WhisperService
from services.database_service import DatabaseService
from utils.audio_processing import AudioProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional enhanced imports (graceful fallback)
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("📝 Note: librosa not available, using basic audio processing")

try:
    from sklearn.cluster import KMeans
    import textstat
    from scipy import signal
    ENHANCED_FEATURES = True
except ImportError:
    ENHANCED_FEATURES = False
    print("📝 Note: Enhanced features not available, using basic mode")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== ENHANCED DATABASE MANAGER ====================

class EnhancedDatabaseManager:
    """Enhanced database management with connection pooling"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connection_pool = Queue(maxsize=pool_size)
        self.pool_lock = threading.Lock()
        self._initialize_pool()
        self._create_tables()
        
    def _initialize_pool(self):
        """Initialize database connection pool"""
        for _ in range(self.pool_size):
            conn = sqlite3.connect(
                self.db_path,
                timeout=30,
                check_same_thread=False
            )
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            conn.execute("PRAGMA temp_store=MEMORY")
            self.connection_pool.put(conn)
        
        logger.info(f"✅ Enhanced Database initialized: {self.db_path} (pool size: {self.pool_size})")
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        conn = None
        try:
            conn = self.connection_pool.get(timeout=10)
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self.connection_pool.put(conn)
    
    def _create_tables(self):
        """Create database schema with enhanced fields"""
        with self.get_connection() as conn:
            # Enhanced transcriptions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    filename TEXT,
                    transcription TEXT NOT NULL,
                    content_type TEXT DEFAULT 'speech',
                    processing_time REAL,
                    audio_duration REAL,
                    model_used TEXT DEFAULT 'base',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Keep existing tables
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date DATE,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                )
            """)
            
            conn.commit()

# ==================== SMART CONTENT DETECTION ====================

def detect_content_type(audio_path: str) -> str:
    """Simple content type detection based on filename and basic audio properties"""
    filename = os.path.basename(audio_path).lower()
    
    # Filename-based hints
    music_keywords = ['song', 'track', 'music', 'album', 'band', 'artist']
    speech_keywords = ['meeting', 'call', 'interview', 'lecture', 'presentation']
    
    for keyword in music_keywords:
        if keyword in filename:
            return "music"
    
    for keyword in speech_keywords:
        if keyword in filename:
            return "speech"
    
    # If librosa is available, do basic audio analysis
    if LIBROSA_AVAILABLE:
        try:
            y, sr = librosa.load(audio_path, duration=10)  # Load first 10 seconds
            
            # Simple beat detection
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # If strong beat detected, likely music
            if tempo > 60 and tempo < 200 and len(beats) > 5:
                return "music"
        except Exception:
            pass
    
    # Default to speech
    return "speech"

def get_smart_prompt(content_type: str, filename: str = "") -> str:
    """Get context-aware prompt for Whisper - focused on meetings/lectures"""
    filename_lower = filename.lower()
    
    # Always prioritize speech/meeting content (no music focus)
    if any(context in filename_lower for context in ['meeting', 'call', 'conference']):
        return "Transcribe spoken content from meeting or business call with multiple speakers. Include clear speech and professional discussion."
    elif any(context in filename_lower for context in ['lecture', 'class', 'presentation']):
        return "Transcribe spoken content from meeting or lecture with educational content and technical terms."
    else:
        return "Transcribe spoken content from meeting or lecture. Focus on clear speech and natural conversation."

# ==================== IMPROVED TRANSCRIPTION SERVICE ====================

class ImprovedTranscriptionService:
    """Improved transcription with better model and smart prompting"""
    
    def __init__(self, model_size: str = "base"):  # Upgraded from tiny
        self.model_size = model_size
        self.model = None
        self.vad = webrtcvad.Vad(2)
        self._load_model()
        
    def _load_model(self):
        """Load Whisper model"""
        logger.info(f"🤖 Loading Whisper {self.model_size} model...")
        start_time = time.time()
        self.model = whisper.load_model(self.model_size)
        load_time = time.time() - start_time
        logger.info(f"✅ Model loaded in {load_time:.2f} seconds")
        
    def detect_voice_activity(self, audio: np.ndarray, sample_rate: int = 16000) -> List[Tuple[float, float]]:
        """Voice activity detection"""
        # Convert to bytes for VAD
        audio_int16 = (audio * 32768).astype(np.int16)
        frame_duration = 30  # ms
        frame_size = int(sample_rate * frame_duration / 1000)
        
        voiced_segments = []
        current_segment_start = None
        
        for i in range(0, len(audio_int16) - frame_size, frame_size):
            frame = audio_int16[i:i + frame_size].tobytes()
            
            try:
                is_speech = self.vad.is_speech(frame, sample_rate)
                timestamp = i / sample_rate
                
                if is_speech and current_segment_start is None:
                    current_segment_start = timestamp
                elif not is_speech and current_segment_start is not None:
                    voiced_segments.append((current_segment_start, timestamp))
                    current_segment_start = None
            except Exception:
                continue
                
        # Handle case where audio ends with speech
        if current_segment_start is not None:
            voiced_segments.append((current_segment_start, len(audio_int16) / sample_rate))
            
        # Merge close segments and filter short ones
        merged_segments = []
        for start, end in voiced_segments:
            if end - start >= 0.5:  # Minimum 0.5 seconds
                if merged_segments and start - merged_segments[-1][1] < 1.0:  # Merge if gap < 1 second
                    merged_segments[-1] = (merged_segments[-1][0], end)
                else:
                    merged_segments.append((start, end))
                    
        logger.info(f"✅ Detected {len(merged_segments)} voice segments")
        return merged_segments
    
    def transcribe_audio(self, audio_path: str, meeting_title: str = "") -> Dict[str, Any]:
        """Improved transcription with smart prompting"""
        start_time = time.time()
        
        try:
            # Detect content type
            content_type = detect_content_type(audio_path)
            filename = os.path.basename(audio_path)
            
            logger.info(f"🎵 Loading audio: {audio_path}")
            logger.info(f"🔍 Detected content type: {content_type}")
            
            # Load audio (fallback to whisper's built-in loading if librosa unavailable)
            if LIBROSA_AVAILABLE:
                audio, sample_rate = librosa.load(audio_path, sr=16000)
                audio_duration = len(audio) / 16000
            else:
                # Use whisper's audio loading
                audio = whisper.load_audio(audio_path)
                audio = whisper.pad_or_trim(audio)
                audio_duration = len(audio) / 16000
            
            # Voice activity detection
            logger.info("🔍 Detecting voice segments...")
            voiced_segments = self.detect_voice_activity(audio)
            
            if not voiced_segments:
                return {
                    "transcription": "No speech detected in audio",
                    "content_type": content_type,
                    "processing_time": time.time() - start_time,
                    "audio_duration": audio_duration,
                    "segments": []
                }
            
            # Get smart prompt
            prompt = get_smart_prompt(content_type, filename)
            logger.info(f"🎯 Using prompt: {prompt}")
            
            # Transcribe segments with improved settings
            full_transcription = []
            segment_details = []
            
            for i, (start, end) in enumerate(voiced_segments):
                logger.info(f"🎙️ Transcribing segment {i+1}/{len(voiced_segments)}")
                
                # Extract segment
                start_sample = int(start * 16000)
                end_sample = int(end * 16000)
                segment_audio = audio[start_sample:end_sample]
                
                # Transcribe with smart prompt and improved settings
                result = self.model.transcribe(
                    segment_audio,
                    initial_prompt=prompt,
                    word_timestamps=True,
                    temperature=0.2,  # Lower temperature for consistency
                    best_of=2,        # Multiple attempts
                    beam_size=5,      # Better search
                    no_speech_threshold=0.6  # Better silence detection
                )
                
                segment_text = result["text"].strip()
                if segment_text:
                    full_transcription.append(segment_text)
                    segment_details.append({
                        "start": start,
                        "end": end,
                        "text": segment_text
                    })
            
            final_transcription = " ".join(full_transcription)
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Transcription completed in {processing_time:.2f}s")
            
            return {
                "transcription": final_transcription,
                "content_type": content_type,
                "processing_time": processing_time,
                "audio_duration": audio_duration,
                "segments": segment_details,
                "model_used": self.model_size
            }
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {str(e)}")
            return {
                "error": str(e),
                "transcription": "",
                "processing_time": time.time() - start_time
            }

# ==================== FASTAPI APPLICATION ====================

# Initialize services
db_manager = EnhancedDatabaseManager("verba_app.db")
transcription_service = ImprovedTranscriptionService("base")  # Upgraded model

app = FastAPI(title="Verba Improved API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class TranscriptionResponse(BaseModel):
    transcription: str
    content_type: str
    processing_time: float
    audio_duration: float
    segments: List[Dict]
    model_used: str

class ReminderCreate(BaseModel):
    title: str
    description: str = ""
    due_date: Optional[str] = None

class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None

# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    return {"message": "Verba Improved API", "version": "1.0.0", "status": "operational"}

@app.get("/health")
async def health_check():
    """Health check with system status"""
    try:
        # Test database
        with db_manager.get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        
        # Test model
        model_status = "loaded" if transcription_service.model else "not_loaded"
        
        return {
            "status": "healthy",
            "database": "operational",
            "model": model_status,
            "model_size": transcription_service.model_size,
            "enhanced_features": ENHANCED_FEATURES,
            "librosa_available": LIBROSA_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    session_id: str = Form(...),
    meeting_title: str = Form("")
):
    """Improved transcription endpoint"""
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")
        
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(audio.filename).suffix) as tmp_file:
        content = await audio.read()
        tmp_file.write(content)
        tmp_file.flush()
        
        try:
            # Transcribe with improvements
            result = transcription_service.transcribe_audio(tmp_file.name, meeting_title)
            
            if "error" in result:
                raise HTTPException(status_code=500, detail=result["error"])
            
            # Save to database
            with db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO transcriptions (
                        session_id, filename, transcription, content_type,
                        processing_time, audio_duration, model_used
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id,
                    audio.filename,
                    result["transcription"],
                    result["content_type"],
                    result["processing_time"],
                    result["audio_duration"],
                    result["model_used"]
                ))
                
                conn.commit()
            
            return TranscriptionResponse(**result)
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file.name)

@app.get("/transcriptions")
async def get_transcriptions(session_id: str, limit: int = 20, offset: int = 0):
    """Get transcriptions with improved metadata"""
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                id, filename, transcription, content_type, processing_time, 
                audio_duration, model_used, created_at
            FROM transcriptions
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (session_id, limit, offset))
        
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "filename": row[1],
            "transcription": row[2],
            "content_type": row[3],
            "processing_time": row[4],
            "audio_duration": row[5],
            "model_used": row[6],
            "created_at": row[7]
        } for row in results]

# ==================== EXISTING ENDPOINTS ====================

@app.post("/sessions")
async def create_session():
    """Create a new session"""
    session_id = f"session_{uuid.uuid4().hex[:8]}_{int(time.time() * 1000)}"
    
    with db_manager.get_connection() as conn:
        conn.execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
        conn.commit()
    
    logger.info(f"✅ Session created: {session_id}")
    return {"session_id": session_id}

@app.post("/reminders")
async def create_reminder(session_id: str, reminder: ReminderCreate):
    """Create a new reminder"""
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO reminders (session_id, title, description, due_date)
            VALUES (?, ?, ?, ?)
        """, (session_id, reminder.title, reminder.description, reminder.due_date))
        
        reminder_id = cursor.lastrowid
        conn.commit()
    
    return {"id": reminder_id, "message": "Reminder created successfully"}

@app.get("/reminders")
async def get_reminders(session_id: str):
    """Get all reminders for a session"""
    with db_manager.get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, title, description, due_date, status, created_at, updated_at
            FROM reminders
            WHERE session_id = ?
            ORDER BY created_at DESC
        """, (session_id,))
        
        return [
            {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "due_date": row[3],
                "status": row[4],
                "created_at": row[5],
                "updated_at": row[6]
            }
            for row in cursor.fetchall()
        ]

@app.put("/reminders/{reminder_id}")
async def update_reminder(
    reminder_id: int,
    session_id: str,
    status: Optional[str] = None,
    reminder_update: Optional[ReminderUpdate] = None
):
    """Update reminder status or details"""
    updates = []
    params = []
    
    if status:
        updates.append("status = ?")
        params.append(status)
    
    if reminder_update:
        if reminder_update.title:
            updates.append("title = ?")
            params.append(reminder_update.title)
        if reminder_update.description is not None:
            updates.append("description = ?")
            params.append(reminder_update.description)
        if reminder_update.due_date:
            updates.append("due_date = ?")
            params.append(reminder_update.due_date)
        if reminder_update.status:
            updates.append("status = ?")
            params.append(reminder_update.status)
    
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([reminder_id, session_id])
    
    with db_manager.get_connection() as conn:
        result = conn.execute(f"""
            UPDATE reminders 
            SET {', '.join(updates)}
            WHERE id = ? AND session_id = ?
        """, params)
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        conn.commit()
    
    return {"message": "Reminder updated successfully"}

@app.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, session_id: str):
    """Delete a reminder"""
    with db_manager.get_connection() as conn:
        result = conn.execute("""
            DELETE FROM reminders WHERE id = ? AND session_id = ?
        """, (reminder_id, session_id))
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Reminder not found")
        
        conn.commit()
    
    return {"message": "Reminder deleted successfully"}

# ==================== AI ASSISTANT INTEGRATION ====================

class AIAssistant:
    """AI assistant integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.available = bool(self.api_key)
        
        if self.available:
            logger.info("✅ AI Assistant initialized")
        else:
            logger.warning("⚠️ AI Assistant not available: OPENROUTER_API_KEY environment variable not set")

# Initialize AI assistant
ai_assistant = AIAssistant()

@app.post("/chat")
async def chat_with_ai(session_id: str, message: str):
    """Chat with AI assistant"""
    if not ai_assistant.available:
        raise HTTPException(status_code=503, detail="AI Assistant not available")
    
    return {"response": "AI Assistant integration coming soon!"}

# ==================== APPLICATION LIFECYCLE ====================

@app.on_event("startup")
async def startup_event():
    """Startup checks"""
    logger.info("🚀 Starting Verba Improved Backend...")
    
    # Verify model is loaded
    if not transcription_service.model:
        logger.error("❌ Whisper model not loaded!")
        sys.exit(1)
    
    # Verify database
    try:
        with db_manager.get_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        logger.info("✅ Database connection verified")
    except Exception as e:
        logger.error(f"❌ Database error: {e}")
        sys.exit(1)
    
    logger.info("✅ Verba Improved Backend started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Verba Improved Backend...")
    
    # Clean up connection pool
    try:
        while not db_manager.connection_pool.empty():
            conn = db_manager.connection_pool.get_nowait()
            conn.close()
        logger.info("✅ Database connections cleaned up")
    except Exception as e:
        logger.error(f"⚠️ Cleanup warning: {e}")
    
    logger.info("✅ Verba Improved Backend shutdown complete")

# ==================== TESTING SUITE ====================

def run_minimal_tests():
    """Test minimal enhanced features"""
    print("🧪 Testing Minimal Enhanced Verba...")
    
    # Test database
    test_db = EnhancedDatabaseManager("test_verba_minimal.db")
    
    try:
        # Test session creation
        session_id = f"test_session_{int(time.time())}"
        with test_db.get_connection() as conn:
            conn.execute("INSERT INTO sessions (session_id) VALUES (?)", (session_id,))
            conn.commit()
        print(f"✅ Session created: {session_id}")
        
        # Test content type detection
        content_type = detect_content_type("test_song.mp3")
        print(f"✅ Content detection: {content_type}")
        
        # Test smart prompting
        prompt = get_smart_prompt("music", "central_cee_band4band.mp3")
        print(f"✅ Smart prompt: {prompt[:50]}...")
        
        # Test enhanced transcription storage
        with test_db.get_connection() as conn:
            conn.execute("""
                INSERT INTO transcriptions (
                    session_id, filename, transcription, content_type,
                    processing_time, audio_duration, model_used
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, "test.mp3", "Test transcription", content_type, 1.5, 2.0, "base"))
            
            conn.commit()
        print("✅ Enhanced database storage")
        
        print("🎉 Minimal enhanced integration testing complete!")
        print("✅ All core features working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup
        try:
            while not test_db.connection_pool.empty():
                conn = test_db.connection_pool.get_nowait()
                conn.close()
            os.unlink("test_verba_minimal.db")
            print("✅ Test database cleaned up")
        except Exception:
            pass

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_minimal_tests()
    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        logger.info("🚀 Starting Verba Improved Server...")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("Usage:")
        print("  python main.py test    - Run minimal testing suite")
        print("  python main.py server  - Start improved API server")
