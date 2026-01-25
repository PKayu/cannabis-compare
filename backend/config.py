"""
Configuration management for FastAPI backend
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str

    # Supabase Configuration
    supabase_url: Optional[str] = None
    supabase_service_key: Optional[str] = None

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    debug: bool = True
    api_host: str = "localhost"
    api_port: int = 8000

    # Scraping
    scraper_timeout: int = 30
    max_retries: int = 3

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        case_sensitive = False

# Create settings instance
settings = Settings()
