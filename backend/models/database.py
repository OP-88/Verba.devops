"""
Database models and schema for Verba AI Transcription System
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager for transcriptions"""
    
    def __init__(self, db_path: str = "verba_app.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize database and create tables"""
        try:
            with self.get_connection() as conn:
                self.create_tables(conn)
                self.create_indexes(conn)
            logger.info(f"✅ Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=30,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA cache_size=10000")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""
        # Main transcriptions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                language VARCHAR(10) DEFAULT 'en',
                duration REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_name VARCHAR(255),
                file_size INTEGER DEFAULT 0,
                segments JSON,
                session_id TEXT DEFAULT 'default',
                processing_time REAL DEFAULT 0.0,
                model_used TEXT DEFAULT 'base'
            )
        """)
        
        # Sessions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Export history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS export_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcription_id INTEGER,
                format TEXT NOT NULL,
                exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transcription_id) REFERENCES transcriptions (id)
            )
        """)
        
        conn.commit()
    
    def create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_transcriptions_created_at ON transcriptions(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_transcriptions_session_id ON transcriptions(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_transcriptions_language ON transcriptions(language)",
            "CREATE INDEX IF NOT EXISTS idx_transcriptions_text ON transcriptions(text)",
            "CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id)",
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        conn.commit()
    
    def insert_transcription(self, 
                           text: str,
                           confidence: float = 0.0,
                           language: str = 'en',
                           duration: float = 0.0,
                           file_name: str = '',
                           file_size: int = 0,
                           segments: List[Dict] = None,
                           session_id: str = 'default',
                           processing_time: float = 0.0,
                           model_used: str = 'base') -> int:
        """Insert a new transcription record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO transcriptions 
                    (text, confidence, language, duration, file_name, file_size, 
                     segments, session_id, processing_time, model_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    text, confidence, language, duration, file_name, file_size,
                    json.dumps(segments) if segments else None,
                    session_id, processing_time, model_used
                ))
                
                transcription_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"✅ Transcription saved with ID: {transcription_id}")
                return transcription_id
                
        except Exception as e:
            logger.error(f"❌ Failed to insert transcription: {e}")
            raise
    
    def get_transcription(self, transcription_id: int) -> Optional[Dict[str, Any]]:
        """Get a single transcription by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM transcriptions WHERE id = ?
                """, (transcription_id,))
                
                row = cursor.fetchone()
                if row:
                    result = dict(row)
                    # Parse segments JSON
                    if result['segments']:
                        result['segments'] = json.loads(result['segments'])
                    return result
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get transcription {transcription_id}: {e}")
            return None
    
    def get_all_transcriptions(self, 
                              limit: int = 100, 
                              offset: int = 0,
                              session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all transcriptions with pagination"""
        try:
            with self.get_connection() as conn:
                query = "SELECT * FROM transcriptions"
                params = []
                
                if session_id:
                    query += " WHERE session_id = ?"
                    params.append(session_id)
                
                query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    # Parse segments JSON
                    if result['segments']:
                        result['segments'] = json.loads(result['segments'])
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Failed to get transcriptions: {e}")
            return []
    
    def search_transcriptions(self, 
                            query: str, 
                            limit: int = 50) -> List[Dict[str, Any]]:
        """Search transcriptions by text content"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM transcriptions 
                    WHERE text LIKE ? OR file_name LIKE ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    result = dict(row)
                    # Parse segments JSON
                    if result['segments']:
                        result['segments'] = json.loads(result['segments'])
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Failed to search transcriptions: {e}")
            return []
    
    def delete_transcription(self, transcription_id: int) -> bool:
        """Delete a transcription by ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    DELETE FROM transcriptions WHERE id = ?
                """, (transcription_id,))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Transcription {transcription_id} deleted")
                    return True
                else:
                    logger.warning(f"⚠️  Transcription {transcription_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Failed to delete transcription {transcription_id}: {e}")
            return False
    
    def update_session_activity(self, session_id: str):
        """Update session last activity"""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions (session_id, last_activity)
                    VALUES (?, ?)
                """, (session_id, datetime.now().isoformat()))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update session activity: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                # Total transcriptions
                total_count = conn.execute(
                    "SELECT COUNT(*) FROM transcriptions"
                ).fetchone()[0]
                
                # Total duration
                total_duration = conn.execute(
                    "SELECT SUM(duration) FROM transcriptions"
                ).fetchone()[0] or 0
                
                # Languages
                languages = conn.execute("""
                    SELECT language, COUNT(*) as count 
                    FROM transcriptions 
                    GROUP BY language
                """).fetchall()
                
                # Recent activity (last 7 days)
                recent_count = conn.execute("""
                    SELECT COUNT(*) FROM transcriptions 
                    WHERE created_at >= datetime('now', '-7 days')
                """).fetchone()[0]
                
                return {
                    'total_transcriptions': total_count,
                    'total_duration_hours': round(total_duration / 3600, 2),
                    'languages': dict(languages),
                    'recent_activity': recent_count
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get statistics: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                return True
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False