#!/usr/bin/env python3
"""
🎯 VERBA BACKEND DATABASE INTEGRATION - ENHANCED VERSION
Complete backend with enhanced database connection management
"""

import os
import sys
import time
import json
import sqlite3
import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import threading
from contextlib import contextmanager
from queue import Queue, Empty

import numpy as np
import torch
import whisper
import librosa
import webrtcvad
import soundfile as sf
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models (Pydantic for API)
class TranscriptionRequest(BaseModel):
    title: Optional[str] = "Meeting Transcript"
    session_id: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    session_id: str
    context_type: Optional[str] = "general_chat"
    transcription_id: Optional[int] = None

class ReminderRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    due_date: Optional[datetime] = None
    priority: str = "medium"
    session_id: str
    source_transcription_id: Optional[int] = None

class SettingsRequest(BaseModel):
    session_id: str
    settings: Dict[str, Any]

# Your existing dataclasses (unchanged)
@dataclass
class TranscriptionResult:
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
    start_time: float
    end_time: float
    audio_data: np.ndarray
    sample_rate: int
    confidence: float = 1.0

# Enhanced Database Manager with Connection Pooling
class EnhancedVerbaDatabaseManager:
    """Enhanced database manager with connection pooling and better concurrency"""
    
    def __init__(self, db_path: str = "verba_app.db", pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.connection_pool = Queue(maxsize=pool_size)
        self.lock = threading.RLock()  # Reentrant lock
        
        # Initialize connection pool
        self._initialize_pool()
        self.init_database()
        logger.info(f"✅ Enhanced Database initialized: {db_path} (pool size: {pool_size})")
    
    def _initialize_pool(self):
        """Initialize connection pool with optimized connections"""
        for _ in range(self.pool_size):
            conn = self._create_optimized_connection()
            self.connection_pool.put(conn)
    
    def _create_optimized_connection(self) -> sqlite3.Connection:
        """Create an optimized SQLite connection"""
        conn = sqlite3.Connection(
            self.db_path,
            timeout=30.0,
            check_same_thread=False,
            isolation_level=None  # Autocommit mode for better concurrency
        )
        
        # Optimize for concurrent access
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # Faster but still safe
        conn.execute("PRAGMA temp_store=MEMORY")  # Keep temp data in RAM
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
        conn.execute("PRAGMA cache_size=10000")  # Larger cache
        conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
        
        conn.row_factory = sqlite3.Row
        return conn
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with proper cleanup"""
        conn = None
        try:
            # Get connection from pool (with timeout)
            try:
                conn = self.connection_pool.get(timeout=5.0)
            except Empty:
                # Pool exhausted, create temporary connection
                logger.warning("Connection pool exhausted, creating temporary connection")
                conn = self._create_optimized_connection()
                
            yield conn
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                # Retry logic for locked database
                logger.warning(f"Database locked, retrying: {e}")
                time.sleep(0.1)  # Small delay
                try:
                    if conn:
                        conn.close()
                    conn = self._create_optimized_connection()
                    yield conn
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
                    raise e
            else:
                raise e
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise e
        finally:
            if conn:
                try:
                    # Return connection to pool or close if pool is full
                    try:
                        self.connection_pool.put_nowait(conn)
                    except:
                        conn.close()
                except Exception as e:
                    logger.warning(f"Connection cleanup warning: {e}")
    
    def execute_with_retry(self, query: str, params: tuple = (), retries: int = 3):
        """Execute query with retry logic"""
        for attempt in range(retries):
            try:
                with self.get_connection() as conn:
                    cursor = conn.execute(query, params)
                    conn.commit()
                    return cursor
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e).lower() and attempt < retries - 1:
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database locked, retry {attempt + 1}/{retries} in {wait_time}s")
                    time.sleep(wait_time)
                    continue
                else:
                    raise e
    
    def init_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            # Transcriptions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    title TEXT DEFAULT 'Meeting Transcript',
                    transcription_text TEXT NOT NULL,
                    audio_file_path TEXT,
                    duration_seconds REAL,
                    confidence_score REAL,
                    processing_time_ms INTEGER,
                    model_used TEXT,
                    chunks_processed INTEGER DEFAULT 0,
                    vad_segments INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # AI Conversations table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    message_type TEXT NOT NULL CHECK (message_type IN ('user', 'assistant')),
                    message_content TEXT NOT NULL,
                    context_type TEXT DEFAULT 'general_chat',
                    transcription_id INTEGER,
                    processing_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transcription_id) REFERENCES transcriptions (id)
                )
            """)
            
            # Reminders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TIMESTAMP,
                    reminder_time TIMESTAMP,
                    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'overdue')),
                    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
                    source_transcription_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_transcription_id) REFERENCES transcriptions (id)
                )
            """)
            
            # Settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    setting_category TEXT NOT NULL,
                    setting_name TEXT NOT NULL,
                    setting_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(session_id, setting_category, setting_name)
                )
            """)
            
            # Usage stats table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    total_transcriptions INTEGER DEFAULT 0,
                    total_duration_minutes INTEGER DEFAULT 0,
                    average_processing_time_ms INTEGER DEFAULT 0,
                    ai_queries_count INTEGER DEFAULT 0,
                    reminders_created INTEGER DEFAULT 0,
                    active_sessions INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date)
                )
            """)
            
            conn.commit()
    
    def save_transcription(self, result: TranscriptionResult, session_id: str, 
                          title: str, audio_file_path: Optional[str] = None) -> int:
        """Save transcription result to database with retry logic"""
        try:
            with self.get_connection() as conn:
                # Begin explicit transaction
                conn.execute("BEGIN IMMEDIATE")
                
                cursor = conn.execute("""
                    INSERT INTO transcriptions (
                        session_id, title, transcription_text, audio_file_path,
                        duration_seconds, confidence_score, processing_time_ms,
                        model_used, chunks_processed, vad_segments, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, title, result.text, audio_file_path,
                    result.duration, result.confidence, int(result.processing_time * 1000),
                    result.model_used, result.chunks_processed, result.vad_segments,
                    json.dumps(result.metadata)
                ))
                
                transcription_id = cursor.lastrowid
                
                # Update usage stats in same transaction
                self._update_usage_stats_internal(conn, 'transcription')
                
                conn.execute("COMMIT")
                return transcription_id
                
        except Exception as e:
            logger.error(f"❌ Failed to save transcription: {e}")
            raise
    
    def get_transcriptions(self, session_id: str, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get transcriptions for a session"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM transcriptions 
                WHERE session_id = ? 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (session_id, limit, offset))
            
            transcriptions = []
            for row in cursor.fetchall():
                transcription = dict(row)
                if transcription['metadata_json']:
                    transcription['metadata'] = json.loads(transcription['metadata_json'])
                del transcription['metadata_json']
                transcriptions.append(transcription)
            
            return transcriptions
    
    def get_transcription(self, transcription_id: int, session_id: str) -> Optional[Dict]:
        """Get single transcription"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM transcriptions 
                WHERE id = ? AND session_id = ?
            """, (transcription_id, session_id))
            
            row = cursor.fetchone()
            if row:
                transcription = dict(row)
                if transcription['metadata_json']:
                    transcription['metadata'] = json.loads(transcription['metadata_json'])
                del transcription['metadata_json']
                return transcription
            return None
    
    def save_ai_conversation(self, session_id: str, conversation_id: str,
                           message_type: str, content: str, context_type: str = "general_chat",
                           transcription_id: Optional[int] = None, processing_time_ms: int = 0):
        """Save AI conversation message with retry logic"""
        try:
            with self.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                
                conn.execute("""
                    INSERT INTO ai_conversations (
                        session_id, conversation_id, message_type, message_content,
                        context_type, transcription_id, processing_time_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_id, conversation_id, message_type, content, 
                      context_type, transcription_id, processing_time_ms))
                
                if message_type == 'user':
                    self._update_usage_stats_internal(conn, 'ai_query')
                
                conn.execute("COMMIT")
                
        except Exception as e:
            logger.error(f"❌ Failed to save AI conversation: {e}")
            raise
    
    def get_ai_conversations(self, session_id: str, conversation_id: Optional[str] = None,
                           limit: int = 50) -> List[Dict]:
        """Get AI conversation history"""
        with self.get_connection() as conn:
            if conversation_id:
                cursor = conn.execute("""
                    SELECT * FROM ai_conversations 
                    WHERE session_id = ? AND conversation_id = ?
                    ORDER BY created_at ASC 
                    LIMIT ?
                """, (session_id, conversation_id, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM ai_conversations 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (session_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def create_reminder(self, session_id: str, title: str, description: str = "",
                       due_date: Optional[datetime] = None, priority: str = "medium",
                       source_transcription_id: Optional[int] = None) -> int:
        """Create a new reminder"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO reminders (
                    session_id, title, description, due_date, priority, source_transcription_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, title, description, due_date, priority, source_transcription_id))
            
            reminder_id = cursor.lastrowid
            self.update_usage_stats('reminder')
            return reminder_id
    
    def get_reminders(self, session_id: str, status: Optional[str] = None) -> List[Dict]:
        """Get reminders for a session"""
        with self.get_connection() as conn:
            if status:
                cursor = conn.execute("""
                    SELECT * FROM reminders 
                    WHERE session_id = ? AND status = ?
                    ORDER BY due_date ASC, created_at DESC
                """, (session_id, status))
            else:
                cursor = conn.execute("""
                    SELECT * FROM reminders 
                    WHERE session_id = ? 
                    ORDER BY due_date ASC, created_at DESC
                """, (session_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_reminder_status(self, reminder_id: int, session_id: str, status: str) -> bool:
        """Update reminder status"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                UPDATE reminders 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ? AND session_id = ?
            """, (status, reminder_id, session_id))
            
            return cursor.rowcount > 0
    
    def save_settings(self, session_id: str, settings: Dict[str, Any]):
        """Save user settings"""
        with self.get_connection() as conn:
            for category, category_settings in settings.items():
                if isinstance(category_settings, dict):
                    for setting_name, setting_value in category_settings.items():
                        conn.execute("""
                            INSERT OR REPLACE INTO app_settings 
                            (session_id, setting_category, setting_name, setting_value, updated_at)
                            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                        """, (session_id, category, setting_name, json.dumps(setting_value)))
                else:
                    conn.execute("""
                        INSERT OR REPLACE INTO app_settings 
                        (session_id, setting_category, setting_name, setting_value, updated_at)
                        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (session_id, "general", category, json.dumps(category_settings)))
    
    def get_settings(self, session_id: str) -> Dict[str, Any]:
        """Get user settings"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT setting_category, setting_name, setting_value 
                FROM app_settings 
                WHERE session_id = ?
            """, (session_id,))
            
            settings = {}
            for row in cursor.fetchall():
                category = row['setting_category']
                name = row['setting_name']
                value = json.loads(row['setting_value'])
                
                if category not in settings:
                    settings[category] = {}
                settings[category][name] = value
            
            return settings
    
    def _update_usage_stats_internal(self, conn: sqlite3.Connection, stat_type: str):
        """Internal method to update usage stats within existing transaction"""
        today = datetime.now().date().isoformat()
        
        # Check if entry exists
        cursor = conn.execute("SELECT id FROM usage_stats WHERE date = ?", (today,))
        exists = cursor.fetchone()
        
        if exists:
            # Update existing stats
            if stat_type == 'transcription':
                conn.execute("""
                    UPDATE usage_stats 
                    SET total_transcriptions = total_transcriptions + 1 
                    WHERE date = ?
                """, (today,))
            elif stat_type == 'ai_query':
                conn.execute("""
                    UPDATE usage_stats 
                    SET ai_queries_count = ai_queries_count + 1 
                    WHERE date = ?
                """, (today,))
            elif stat_type == 'reminder':
                conn.execute("""
                    UPDATE usage_stats 
                    SET reminders_created = reminders_created + 1 
                    WHERE date = ?
                """, (today,))
        else:
            # Create new stats entry
            if stat_type == 'transcription':
                conn.execute("""
                    INSERT INTO usage_stats 
                    (date, total_transcriptions, total_duration_minutes, ai_queries_count, reminders_created)
                    VALUES (?, 1, 0, 0, 0)
                """, (today,))
            elif stat_type == 'ai_query':
                conn.execute("""
                    INSERT INTO usage_stats 
                    (date, total_transcriptions, total_duration_minutes, ai_queries_count, reminders_created)
                    VALUES (?, 0, 0, 1, 0)
                """, (today,))
            elif stat_type == 'reminder':
                conn.execute("""
                    INSERT INTO usage_stats 
                    (date, total_transcriptions, total_duration_minutes, ai_queries_count, reminders_created)
                    VALUES (?, 0, 0, 0, 1)
                """, (today,))
    
    def update_usage_stats(self, stat_type: str):
        """Update daily usage statistics with connection pooling"""
        try:
            with self.get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                self._update_usage_stats_internal(conn, stat_type)
                conn.execute("COMMIT")
        except Exception as e:
            logger.error(f"❌ Failed to update usage stats: {e}")
    
    def get_usage_stats(self, days: int = 30) -> List[Dict]:
        """Get usage statistics for last N days"""
        start_date = datetime.now().date() - timedelta(days=days)
        
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM usage_stats 
                WHERE date >= ? 
                ORDER BY date DESC
            """, (start_date,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with self.get_connection() as conn:
            # Delete old transcriptions
            conn.execute("DELETE FROM transcriptions WHERE created_at < ?", (cutoff_date,))
            
            # Delete orphaned conversations
            conn.execute("""
                DELETE FROM ai_conversations 
                WHERE transcription_id IS NOT NULL 
                AND transcription_id NOT IN (SELECT id FROM transcriptions)
            """)
            
            # Delete completed reminders older than 30 days
            reminder_cutoff = datetime.now() - timedelta(days=30)
            conn.execute("""
                DELETE FROM reminders 
                WHERE status = 'completed' AND updated_at < ?
            """, (reminder_cutoff,))
            
            logger.info(f"✅ Cleaned up data older than {days_to_keep} days")
    
    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False
    
    def close_all_connections(self):
        """Close all connections in pool (for shutdown)"""
        while not self.connection_pool.empty():
            try:
                conn = self.connection_pool.get_nowait()
                conn.close()
            except:
                break

# Your existing services (unchanged)
class CompatibleVADService:
    """WebRTC VAD service with unified interface"""
    
    def __init__(self, aggressiveness: int = 2):
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = 16000
        logger.info(f"✅ VAD Service initialized (aggressiveness: {aggressiveness})")
    
    def preprocess_audio(self, audio_data: np.ndarray, original_sr: int) -> np.ndarray:
        if original_sr != self.sample_rate:
            audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=self.sample_rate)
        
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        audio_data = np.clip(audio_data, -1.0, 1.0)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        return audio_int16
    
    def detect_voice_segments(self, audio_data: np.ndarray, sample_rate: int) -> List[AudioSegment]:
        try:
            audio_int16 = self.preprocess_audio(audio_data, sample_rate)
            frame_duration = 30
            frame_length = int(self.sample_rate * frame_duration / 1000)
            
            segments = []
            current_segment_start = None
            
            for i in range(0, len(audio_int16) - frame_length + 1, frame_length):
                frame = audio_int16[i:i + frame_length]
                
                if len(frame) < frame_length:
                    frame = np.pad(frame, (0, frame_length - len(frame)), mode='constant')
                
                frame_bytes = frame.tobytes()
                
                try:
                    is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
                except Exception as e:
                    logger.warning(f"VAD frame processing error: {e}")
                    is_speech = True
                
                current_time = i / self.sample_rate
                
                if is_speech and current_segment_start is None:
                    current_segment_start = current_time
                elif not is_speech and current_segment_start is not None:
                    segment = AudioSegment(
                        start_time=current_segment_start,
                        end_time=current_time,
                        audio_data=audio_data[int(current_segment_start * sample_rate):int(current_time * sample_rate)],
                        sample_rate=sample_rate
                    )
                    segments.append(segment)
                    current_segment_start = None
            
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
        if not self.model:
            if not self.load_model():
                raise RuntimeError("Failed to load transcription model")
        
        start_time = time.time()
        
        try:
            logger.info(f"🎵 Loading audio: {audio_file_path}")
            audio_data, sample_rate = librosa.load(audio_file_path, sr=None)
            audio_duration = len(audio_data) / sample_rate
            
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
            
            transcriptions = []
            for i, segment in enumerate(voice_segments):
                logger.info(f"🎙️ Transcribing segment {i+1}/{len(voice_segments)}")
                
                result = self.model.transcribe(
                    segment.audio_data,
                    fp16=False,
                    language='en'
                )
                
                transcriptions.append(result["text"].strip())
            
            final_text = " ".join(transcriptions)
            processing_time = time.time() - start_time
            
            self.stats['total_transcriptions'] += 1
            self.stats['total_processing_time'] += processing_time
            
            result = TranscriptionResult(
                text=final_text,
                confidence=0.95,
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

# Your existing OpenRouter AI Assistant (unchanged)
import requests

class OpenRouterAIAssistant:
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-3.5-sonnet"
        self.context_history = []
        
        logger.info("✅ OpenRouter AI Assistant initialized")
    
    def chat(self, message: str, include_context: bool = True) -> str:
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
            
            self.context_history.append({"role": "user", "content": message})
            self.context_history.append({"role": "assistant", "content": assistant_message})
            
            if len(self.context_history) > 20:
                self.context_history = self.context_history[-20:]
            
            return assistant_message
            
        except Exception as e:
            logger.error(f"❌ Chat request failed: {e}")
            return f"I apologize, but I'm having trouble processing your request: {e}"
    
    def add_transcription_context(self, transcription: str, title: str = "Meeting Transcription"):
        context_message = f"Here's a {title.lower()}: {transcription}"
        self.context_history.append({"role": "user", "content": context_message})
        logger.info(f"Added transcription context: {title} ({len(transcription)} chars)")
    
    def analyze_transcription(self, transcription: str) -> str:
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
        prompt = f"""
        Based on this transcription, suggest 5 relevant follow-up questions that would help clarify or expand on the discussion:
        
        Transcription: {transcription}
        
        Please provide exactly 5 questions, each on a new line starting with a number.
        """
        
        response = self.chat(prompt, include_context=False)
        
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                question = line.split('.', 1)[-1].strip()
                question = question.lstrip('- ')
                if question and question.endswith('?'):
                    questions.append(question)
        
        return questions[:5]

# Enhanced integrated system with database
class VerbaIntegratedSystem:
    """Complete Verba system with database integration"""
    
    def __init__(self, db_path: str = "verba_app.db"):
        self.db = EnhancedVerbaDatabaseManager(db_path)
        self.transcription_service = EnhancedTranscriptionService()
        self.ai_assistant = None
        
        try:
            self.ai_assistant = OpenRouterAIAssistant()
            logger.info("✅ AI Assistant integrated")
        except Exception as e:
            logger.warning(f"⚠️ AI Assistant not available: {e}")
    
    def process_audio_file(self, file_path: str, session_id: str, title: str = "Meeting Transcript") -> Dict[str, Any]:
        """Process audio file with full pipeline and database storage"""
        try:
            # Transcribe audio
            transcription_result = self.transcription_service.transcribe_audio(file_path)
            
            # Save to database
            transcription_id = self.db.save_transcription(
                transcription_result, session_id, title, file_path
            )
            
            result = {
                "transcription_id": transcription_id,
                "transcription": asdict(transcription_result),
                "ai_analysis": None,
                "suggested_questions": []
            }
            
            # Add AI analysis if available
            if self.ai_assistant and transcription_result.text.strip():
                try:
                    conversation_id = str(uuid.uuid4())
                    
                    # Save transcription context
                    self.db.save_ai_conversation(
                        session_id, conversation_id, "user",
                        f"Analyze this transcription: {transcription_result.text}",
                        "transcription_analysis", transcription_id
                    )
                    
                    # Get AI analysis
                    analysis = self.ai_assistant.analyze_transcription(transcription_result.text)
                    questions = self.ai_assistant.suggest_questions(transcription_result.text)
                    
                    # Save AI responses
                    self.db.save_ai_conversation(
                        session_id, conversation_id, "assistant", analysis,
                        "transcription_analysis", transcription_id
                    )
                    
                    result["ai_analysis"] = analysis
                    result["suggested_questions"] = questions
                    
                except Exception as e:
                    logger.error(f"❌ AI analysis failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Audio processing failed: {e}")
            raise
    
    def chat_with_ai(self, message: str, session_id: str, transcription_id: Optional[int] = None) -> str:
        """Chat with AI assistant and save to database"""
        if not self.ai_assistant:
            raise ValueError("AI Assistant not available")
        
        try:
            conversation_id = f"chat_{session_id}_{int(time.time())}"
            
            # Save user message
            self.db.save_ai_conversation(
                session_id, conversation_id, "user", message,
                "general_chat", transcription_id
            )
            
            # Get AI response
            start_time = time.time()
            response = self.ai_assistant.chat(message)
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Save AI response
            self.db.save_ai_conversation(
                session_id, conversation_id, "assistant", response,
                "general_chat", transcription_id, processing_time_ms
            )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ AI chat failed: {e}")
            raise

# Helper functions
def generate_session_id() -> str:
    """Generate anonymous session ID"""
    return str(uuid.uuid4())

def get_session_id(session_id: Optional[str] = None) -> str:
    """Get or generate session ID"""
    if session_id:
        return session_id
    return generate_session_id()

# FastAPI Application with Database Integration
def create_verba_app() -> FastAPI:
    """Create the FastAPI application with database integration"""
    app = FastAPI(
        title="Verba - Enhanced Transcription Service with Database",
        description="AI-powered meeting transcription, analysis, and storage",
        version="2.1.0"
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
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup connections on shutdown"""
        verba_system.db.close_all_connections()
        logger.info("✅ Database connections closed")
    
    @app.get("/")
    async def root():
        return {
            "service": "Verba Enhanced Transcription with Database",
            "version": "2.1.0",
            "status": "operational",
            "features": {
                "transcription": True,
                "vad_optimization": True,
                "ai_analysis": verba_system.ai_assistant is not None,
                "database_storage": True,
                "conversation_history": True,
                "reminders": True,
                "settings": True
            }
        }
    
    @app.post("/transcribe")
    async def transcribe_audio(
        file: UploadFile = File(...),
        session_id: Optional[str] = Query(None),
        title: Optional[str] = Query("Meeting Transcript")
    ):
        """Transcribe uploaded audio file and save to database"""
        if not file.filename.lower().endswith(('.wav', '.mp3', '.flac', '.m4a')):
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = generate_session_id()
        
        try:
            # Save uploaded file temporarily
            temp_path = f"/tmp/{file.filename}"
            with open(temp_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Process audio with database storage
            result = verba_system.process_audio_file(temp_path, session_id, title)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            # Add session ID to response
            result["session_id"] = session_id
            
            return JSONResponse(content=result)
            
        except Exception as e:
            logger.error(f"❌ Transcription endpoint failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/chat")
    async def chat_with_ai(request: ChatRequest):
        """Chat with AI assistant and save conversation"""
        if not verba_system.ai_assistant:
            raise HTTPException(status_code=503, detail="AI Assistant not available")
        
        try:
            response = verba_system.chat_with_ai(
                request.message, 
                request.session_id,
                request.transcription_id
            )
            
            return {"response": response, "session_id": request.session_id}
            
        except Exception as e:
            logger.error(f"❌ Chat endpoint failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/transcriptions")
    async def get_transcriptions(
        session_id: str = Query(...),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0)
    ):
        """Get transcription history for a session"""
        try:
            transcriptions = verba_system.db.get_transcriptions(session_id, limit, offset)
            return {
                "transcriptions": transcriptions,
                "session_id": session_id,
                "count": len(transcriptions)
            }
        except Exception as e:
            logger.error(f"❌ Get transcriptions failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/transcriptions/{transcription_id}")
    async def get_transcription(
        transcription_id: int,
        session_id: str = Query(...)
    ):
        """Get single transcription"""
        try:
            transcription = verba_system.db.get_transcription(transcription_id, session_id)
            if not transcription:
                raise HTTPException(status_code=404, detail="Transcription not found")
            
            return transcription
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Get transcription failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/conversations")
    async def get_conversations(
        session_id: str = Query(...),
        conversation_id: Optional[str] = Query(None),
        limit: int = Query(50, ge=1, le=100)
    ):
        """Get AI conversation history"""
        try:
            conversations = verba_system.db.get_ai_conversations(session_id, conversation_id, limit)
            return {
                "conversations": conversations,
                "session_id": session_id,
                "count": len(conversations)
            }
        except Exception as e:
            logger.error(f"❌ Get conversations failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/reminders")
    async def create_reminder(request: ReminderRequest):
        """Create a new reminder"""
        try:
            reminder_id = verba_system.db.create_reminder(
                request.session_id,
                request.title,
                request.description,
                request.due_date,
                request.priority,
                request.source_transcription_id
            )
            
            return {
                "reminder_id": reminder_id,
                "message": "Reminder created successfully",
                "session_id": request.session_id
            }
        except Exception as e:
            logger.error(f"❌ Create reminder failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/reminders")
    async def get_reminders(
        session_id: str = Query(...),
        status: Optional[str] = Query(None)
    ):
        """Get reminders for a session"""
        try:
            reminders = verba_system.db.get_reminders(session_id, status)
            return {
                "reminders": reminders,
                "session_id": session_id,
                "count": len(reminders)
            }
        except Exception as e:
            logger.error(f"❌ Get reminders failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/reminders/{reminder_id}")
    async def update_reminder(
        reminder_id: int,
        status: str = Query(...),
        session_id: str = Query(...)
    ):
        """Update reminder status"""
        if status not in ['pending', 'completed', 'overdue']:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        try:
            success = verba_system.db.update_reminder_status(reminder_id, session_id, status)
            if not success:
                raise HTTPException(status_code=404, detail="Reminder not found")
            
            return {"message": "Reminder updated successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Update reminder failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/settings")
    async def save_settings(request: SettingsRequest):
        """Save user settings"""
        try:
            verba_system.db.save_settings(request.session_id, request.settings)
            return {
                "message": "Settings saved successfully",
                "session_id": request.session_id
            }
        except Exception as e:
            logger.error(f"❌ Save settings failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/settings")
    async def get_settings(session_id: str = Query(...)):
        """Get user settings"""
        try:
            settings = verba_system.db.get_settings(session_id)
            return {
                "settings": settings,
                "session_id": session_id
            }
        except Exception as e:
            logger.error(f"❌ Get settings failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/stats")
    async def get_stats(
        session_id: Optional[str] = Query(None),
        days: int = Query(30, ge=1, le=365)
    ):
        """Get system and usage statistics"""
        try:
            usage_stats = verba_system.db.get_usage_stats(days)
            transcription_stats = verba_system.transcription_service.stats
            
            return {
                "usage_stats": usage_stats,
                "transcription_stats": transcription_stats,
                "ai_assistant_available": verba_system.ai_assistant is not None,
                "system_status": "operational",
                "database_status": "connected"
            }
        except Exception as e:
            logger.error(f"❌ Get stats failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/maintenance/cleanup")
    async def cleanup_old_data(
        days_to_keep: int = Query(90, ge=1, le=365),
        admin_key: str = Query(...)  # Simple admin protection
    ):
        """Clean up old data (admin endpoint)"""
        # Simple admin protection - in production use proper authentication
        if admin_key != os.getenv('VERBA_ADMIN_KEY', 'default_admin_key'):
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        try:
            verba_system.db.cleanup_old_data(days_to_keep)
            return {"message": f"Cleaned up data older than {days_to_keep} days"}
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/session/new")
    async def create_new_session():
        """Create a new anonymous session"""
        session_id = generate_session_id()
        return {
            "session_id": session_id,
            "message": "New session created"
        }
    
    return app

def test_database_integration():
    """Test the database integration"""
    print("🧪 Testing Enhanced Database Integration...")
    
    try:
        # Test database manager
        db = EnhancedVerbaDatabaseManager("test_verba.db")
        print("✅ Enhanced Database initialized")
        
        # Test session ID generation
        session_id = generate_session_id()
        print(f"✅ Session ID generated: {session_id[:8]}...")
        
        # Test settings
        test_settings = {
            "theme": "dark",
            "transcription": {
                "model": "tiny",
                "auto_summarize": True
            }
        }
        db.save_settings(session_id, test_settings)
        retrieved_settings = db.get_settings(session_id)
        print(f"✅ Settings test: {len(retrieved_settings)} categories saved")
        
        # Test reminder creation
        reminder_id = db.create_reminder(
            session_id, 
            "Test Reminder", 
            "This is a test reminder",
            datetime.now() + timedelta(days=1),
            "high"
        )
        print(f"✅ Reminder created: ID {reminder_id}")
        
        # Test usage stats
        db.update_usage_stats('transcription')
        stats = db.get_usage_stats(1)
        print(f"✅ Usage stats: {len(stats)} entries")
        
        # Test database health
        health = db.health_check()
        print(f"✅ Database health check: {'Passed' if health else 'Failed'}")
        
        # Test connection pool
        db.close_all_connections()
        print("✅ Connection pool cleanup successful")
        
        # Cleanup test database
        os.unlink("test_verba.db")
        print("✅ Test database cleaned up")
        
        print("🎉 Enhanced database integration testing complete!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test database integration
        if test_database_integration():
            print("\n✅ All tests passed! Ready to run with enhanced database integration.")
        else:
            print("\n❌ Tests failed. Check the output above.")
    elif len(sys.argv) > 1 and sys.argv[1] == "server":
        # Run the server
        app = create_verba_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("🎯 Verba Enhanced System with Database Connection Pooling")
        print("Commands:")
        print("  python main.py test    # Test the enhanced system")
        print("  python main.py server  # Start the enhanced server")
        print("  uvicorn main:create_verba_app --host 0.0.0.0 --port 8000")
