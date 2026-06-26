"""
Database connection and session management
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config import settings

# Create database engine with conditional SSL config
# PostgreSQL (Supabase) requires SSL, but local PostgreSQL doesn't
is_postgres = settings.database_url.startswith("postgresql://")
is_sqlite = settings.database_url.startswith("sqlite")
is_supabase = "supabase" in settings.database_url.lower()

if is_supabase:
    connect_args = {"sslmode": "require"}
elif is_sqlite:
    # busy_timeout (ms): wait up to 30s for a write lock instead of
    # immediately raising "database is locked" when another process holds it.
    connect_args = {"timeout": 30}
else:
    connect_args = {}

engine_kwargs = dict(
    echo=settings.debug,
    future=True,
)

if is_sqlite:
    # SQLite doesn't benefit from connection pooling; use NullPool-like
    # settings and avoid pool_size/max_overflow which cause warnings.
    engine_kwargs["pool_pre_ping"] = True
else:
    engine_kwargs.update(
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

# Enable WAL mode for SQLite — allows concurrent reads during writes and
# dramatically reduces "database is locked" errors from scraper subprocesses.
if is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()

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
