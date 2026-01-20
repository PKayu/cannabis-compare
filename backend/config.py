"""
Configuration management for FastAPI backend
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database
    database_url: str = "postgresql://localhost/cannabis_aggregator"

    # Supabase (optional)
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None

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
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()
