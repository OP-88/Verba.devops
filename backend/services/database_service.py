"""
Verba Database Service
SQLite database management for transcription storage and retrieval.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, text, desc, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from config.settings import settings
from models.transcription_models import (
    Base, 
    TranscriptionDB, 
    TranscriptionCreate, 
    TranscriptionResponse
)

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for managing SQLite database operations."""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize database connection and create tables."""
        try:
            # Create database engine with connection pooling
            database_url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///")
            
            self.engine = create_async_engine(
                database_url,
                poolclass=StaticPool,
                pool_size=settings.database_pool_size,
                pool_timeout=settings.database_timeout,
                echo=settings.debug,
                connect_args={
                    "check_same_thread": False,
                    "timeout": settings.database_timeout
                }
            )
            
            # Create async session factory
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            # Create indexes for performance
            await self._create_indexes()
            
            self.is_initialized = True
            logger.info("✅ Database service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise RuntimeError(f"Database initialization failed: {e}")
    
    async def _create_indexes(self):
        """Create database indexes for improved query performance."""
        try:
            async with self.engine.begin() as conn:
                # Index for full-text search on transcription text
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_transcriptions_text_fts 
                    ON transcriptions(text)
                """))
                
                # Composite index for common queries
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_transcriptions_created_language 
                    ON transcriptions(created_at DESC, language)
                """))
                
                # Index for confidence filtering
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_transcriptions_confidence 
                    ON transcriptions(confidence DESC)
                """))
                
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {e}")
    
    async def create_transcription(self, transcription_data: TranscriptionCreate) -> TranscriptionDB:
        """Create new transcription record."""
        try:
            async with self.async_session() as session:
                # Convert segments to JSON-serializable format
                segments_json = None
                if transcription_data.segments:
                    segments_json = [segment.dict() for segment in transcription_data.segments]
                
                db_transcription = TranscriptionDB(
                    text=transcription_data.text,
                    confidence=transcription_data.confidence,
                    language=transcription_data.language,
                    duration=transcription_data.duration,
                    file_name=transcription_data.file_name,
                    file_size=transcription_data.file_size,
                    segments=segments_json
                )
                
                session.add(db_transcription)
                await session.commit()
                await session.refresh(db_transcription)
                
                logger.info(f"Created transcription record with ID: {db_transcription.id}")
                return db_transcription
                
        except Exception as e:
            logger.error(f"Failed to create transcription: {e}")
            raise RuntimeError(f"Database create error: {e}")
    
    async def get_transcription(self, transcription_id: int) -> Optional[TranscriptionDB]:
        """Get transcription by ID."""
        try:
            async with self.async_session() as session:
                result = await session.get(TranscriptionDB, transcription_id)
                return result
                
        except Exception as e:
            logger.error(f"Failed to get transcription {transcription_id}: {e}")
            raise RuntimeError(f"Database get error: {e}")
    
    async def get_transcriptions(
        self, 
        limit: int = 50, 
        offset: int = 0,
        language: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[TranscriptionDB]:
        """Get transcriptions with pagination and filtering."""
        try:
            async with self.async_session() as session:
                query = session.query(TranscriptionDB)
                
                # Apply filters
                if language:
                    query = query.filter(TranscriptionDB.language == language)
                
                if min_confidence is not None:
                    query = query.filter(TranscriptionDB.confidence >= min_confidence)
                
                # Order by creation date (newest first)
                query = query.order_by(desc(TranscriptionDB.created_at))
                
                # Apply pagination
                query = query.offset(offset).limit(limit)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to get transcriptions: {e}")
            raise RuntimeError(f"Database query error: {e}")
    
    async def search_transcriptions(
        self, 
        search_query: str, 
        limit: int = 50,
        language: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> List[TranscriptionDB]:
        """Search transcriptions by text content."""
        try:
            async with self.async_session() as session:
                # Use LIKE for text search (SQLite FTS can be added later)
                search_pattern = f"%{search_query}%"
                
                query = session.query(TranscriptionDB).filter(
                    TranscriptionDB.text.contains(search_query)
                )
                
                # Apply additional filters
                if language:
                    query = query.filter(TranscriptionDB.language == language)
                
                if min_confidence is not None:
                    query = query.filter(TranscriptionDB.confidence >= min_confidence)
                
                # Order by relevance (confidence) and date
                query = query.order_by(
                    desc(TranscriptionDB.confidence),
                    desc(TranscriptionDB.created_at)
                ).limit(limit)
                
                result = await session.execute(query)
                return result.scalars().all()
                
        except Exception as e:
            logger.error(f"Failed to search transcriptions: {e}")
            raise RuntimeError(f"Database search error: {e}")
    
    async def update_transcription(
        self, 
        transcription_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[TranscriptionDB]:
        """Update transcription record."""
        try:
            async with self.async_session() as session:
                transcription = await session.get(TranscriptionDB, transcription_id)
                if not transcription:
                    return None
                
                # Update fields
                for field, value in update_data.items():
                    if hasattr(transcription, field):
                        setattr(transcription, field, value)
                
                await session.commit()
                await session.refresh(transcription)
                
                logger.info(f"Updated transcription {transcription_id}")
                return transcription
                
        except Exception as e:
            logger.error(f"Failed to update transcription {transcription_id}: {e}")
            raise RuntimeError(f"Database update error: {e}")
    
    async def delete_transcription(self, transcription_id: int) -> bool:
        """Delete transcription record."""
        try:
            async with self.async_session() as session:
                transcription = await session.get(TranscriptionDB, transcription_id)
                if not transcription:
                    return False
                
                await session.delete(transcription)
                await session.commit()
                
                logger.info(f"Deleted transcription {transcription_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete transcription {transcription_id}: {e}")
            raise RuntimeError(f"Database delete error: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            async with self.async_session() as session:
                # Total count
                total_result = await session.execute(
                    text("SELECT COUNT(*) FROM transcriptions")
                )
                total_count = total_result.scalar()
                
                # Total duration
                duration_result = await session.execute(
                    text("SELECT SUM(duration) FROM transcriptions WHERE duration IS NOT NULL")
                )
                total_duration = duration_result.scalar() or 0.0
                
                # Average confidence
                confidence_result = await session.execute(
                    text("SELECT AVG(confidence) FROM transcriptions WHERE confidence IS NOT NULL")
                )
                avg_confidence = confidence_result.scalar() or 0.0
                
                # Language distribution
                language_result = await session.execute(
                    text("""
                        SELECT language, COUNT(*) as count 
                        FROM transcriptions 
                        WHERE language IS NOT NULL 
                        GROUP BY language 
                        ORDER BY count DESC 
                        LIMIT 10
                    """)
                )
                languages = {row[0]: row[1] for row in language_result.fetchall()}
                
                # Recent activity (last 10 transcriptions)
                recent_result = await session.execute(
                    text("""
                        SELECT created_at 
                        FROM transcriptions 
                        ORDER BY created_at DESC 
                        LIMIT 10
                    """)
                )
                recent_activity = [row[0] for row in recent_result.fetchall()]
                
                return {
                    "total_transcriptions": total_count,
                    "total_duration": round(total_duration, 2),
                    "average_confidence": round(avg_confidence, 3),
                    "languages": languages,
                    "recent_activity": recent_activity
                }
                
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise RuntimeError(f"Database statistics error: {e}")
    
    async def check_health(self) -> bool:
        """Check database connectivity and health."""
        try:
            async with self.async_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup database connections."""
        logger.info("Cleaning up database service...")
        if self.engine:
            await self.engine.dispose()
        self.is_initialized = False
        logger.info("✅ Database service cleanup complete")
    
    async def vacuum_database(self):
        """Vacuum SQLite database for optimization."""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("VACUUM"))
            logger.info("Database vacuum completed")
            
        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
    
    async def backup_database(self, backup_path: str):
        """Create database backup."""
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text(f"VACUUM INTO '{backup_path}'"))
            logger.info(f"Database backup created: {backup_path}")
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise RuntimeError(f"Backup error: {e}")