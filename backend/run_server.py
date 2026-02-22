"""
Uvicorn server entrypoint with Windows event loop policy fix.

This script ensures the ProactorEventLoop is set before uvicorn
starts, which is required for Playwright subprocess support on Windows
with Python 3.13+.
"""
import sys
import asyncio
import os

# CRITICAL: Set event loop policy BEFORE any imports that might create an event loop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

if __name__ == "__main__":
    import subprocess
    import uvicorn

    backend_dir = os.path.dirname(os.path.abspath(__file__))

    # Auto-migrate database on startup — ensures schema is always current,
    # even on a fresh SQLite file (worktree, new clone, CI, etc.)
    print("Running database migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        capture_output=True, text=True,
        cwd=backend_dir,
    )
    if result.returncode != 0:
        # Migrations written for PostgreSQL may fail on SQLite due to DDL
        # differences. Fall back to creating tables from models + stamp.
        from config import settings
        if settings.database_url.startswith("sqlite"):
            print("Alembic migrations failed on SQLite — falling back to create_all()...")
            from database import engine
            from models import Base
            Base.metadata.create_all(bind=engine)
            stamp = subprocess.run(
                [sys.executable, "-m", "alembic", "stamp", "head"],
                capture_output=True, text=True,
                cwd=backend_dir,
            )
            if stamp.returncode == 0:
                print("Schema created from models and stamped to head.")
            else:
                print(f"ERROR: alembic stamp failed: {stamp.stderr.strip()}")
                sys.exit(1)
        else:
            print(f"ERROR: Database migration failed!\n{result.stderr.strip() or result.stdout.strip()}")
            sys.exit(1)
    elif result.stderr and "Running upgrade" in result.stderr:
        print(result.stderr.strip())
    else:
        print("Database schema up to date.")

    # Use environment variables for configuration (Docker compatibility)
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_env = os.getenv("RELOAD", "true").lower() in ("true", "1", "yes")

    # Windows + Python 3.13 fix: reload mode has issues with ProactorEventLoop
    # The reloader spawns a subprocess that creates its event loop before
    # the policy is set. Disable reload on Windows + Python 3.13.
    if sys.platform == "win32" and sys.version_info >= (3, 13):
        if reload_env:
            print("\n" + "="*70)
            print("WARNING: Auto-reload disabled on Windows with Python 3.13+")
            print("This is required for Playwright subprocess support.")
            print("Please restart the server manually after code changes.")
            print("="*70 + "\n")
        reload = False
    else:
        reload = reload_env

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
