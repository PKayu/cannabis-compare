"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config import settings

# Create database engine with conditional SSL config
# PostgreSQL (Supabase) requires SSL, but SQLite doesn't support it
is_postgres = settings.database_url.startswith("postgresql://")
connect_args = {"sslmode": "require"} if is_postgres else {}

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,  # Auto-reconnect if connection drops
    connect_args=connect_args
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

# Base class for SQLAlchemy models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """Dependency for getting database session in FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
