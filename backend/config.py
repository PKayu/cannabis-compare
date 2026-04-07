"""
Configuration management for FastAPI backend
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional

_backend_dir = os.path.dirname(os.path.abspath(__file__))

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
    max_concurrent_scrapers: int = 4

    # Logging
    log_level: str = "INFO"

    # Email Notifications (SendGrid)
    sendgrid_api_key: Optional[str] = None
    notification_email_sender: str = "alerts@utahbud.com"
    alert_check_interval_hours: int = 1

    class Config:
        env_file = os.path.join(_backend_dir, ".env")
        case_sensitive = False

    def model_post_init(self, __context):
        """Resolve relative SQLite paths to the backend directory."""
        if self.database_url.startswith("sqlite:///./"):
            relative = self.database_url.replace("sqlite:///./", "")
            absolute = os.path.join(_backend_dir, relative)
            object.__setattr__(self, "database_url", f"sqlite:///{absolute}")

# Create settings instance
settings = Settings()
