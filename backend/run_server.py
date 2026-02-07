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
    import uvicorn

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
