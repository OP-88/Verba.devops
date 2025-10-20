#!/usr/bin/env python3
"""
Application Settings Configuration
"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Application configuration settings"""
    
    def __init__(self):
        # Database settings
        self.database_url = os.getenv('DATABASE_URL', 'sqlite:///./verba_app.db')
        self.database_path = Path('./verba_app.db')
        
        # API settings
        self.api_host = os.getenv('API_HOST', '0.0.0.0')
        self.api_port = int(os.getenv('API_PORT', '8000'))
        self.debug = os.getenv('DEBUG', 'false').lower() == 'true'
        
        # AI/ML settings
        self.whisper_model = os.getenv('WHISPER_MODEL', 'base')
        self.max_audio_size = int(os.getenv('MAX_AUDIO_SIZE', '25')) * 1024 * 1024  # 25MB default
        
        # OpenRouter API (optional)
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        
        # Mode settings
        self.mode = os.getenv('MODE', 'offline')
        
        # Upload settings
        self.upload_dir = Path(os.getenv('UPLOAD_DIR', './uploads'))
        self.upload_dir.mkdir(exist_ok=True)
        
        # Logging settings
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
    @property
    def is_production(self) -> bool:
        return not self.debug
        
    @property
    def cors_origins(self) -> list:
        origins = os.getenv('CORS_ORIGINS', 'http://localhost:8080,http://localhost:3000,http://localhost:5173')
        return [origin.strip() for origin in origins.split(',')]

# Global settings instance
settings = Settings()