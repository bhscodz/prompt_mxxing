# File: backend/app/config.py
# Description: Configuration management for SwasthyaGrid AI Phase 2 using Pydantic Settings
# Supports PostgreSQL (primary via Docker), falls back to SQLite for local dev
# Phase 2 adds: JWT auth config, alert thresholds, AI agent settings

import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "SwasthyaGrid AI"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database configuration
    # PostgreSQL via Docker container is now primary
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "swasthya_db"
    
    # Primary connection string - reads from DATABASE_URL env var
    DATABASE_URL: str = "sqlite+aiosqlite:///./swasthya_grid.db"
    
    # Security / JWT
    SECRET_KEY: str = "swasthyagrid-ai-super-secret-key-district-health-2026-prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # District Administration Context
    DEFAULT_DISTRICT: str = "Pune Rural & Western Ghats"
    DEFAULT_STATE: str = "Maharashtra"
    
    # ML & Time Series Forecasting parameters
    FORECAST_HORIZON_DAYS: int = 14
    TIME_SERIES_LOOKBACK_DAYS: int = 90
    STOCKOUT_CRITICAL_THRESHOLD_DAYS: float = 3.0
    STOCKOUT_WARNING_THRESHOLD_DAYS: float = 7.0
    
    # AI Agent
    OPENAI_API_KEY: str = ""  # Optional - falls back to template responses if empty
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
