"""
Subprocess wrapper for running scrapers in isolated processes.

This module provides a way to run Playwright-based scrapers in separate subprocesses
to avoid event loop conflicts with FastAPI/uvicorn. Each scraper runs with its own
asyncio.run() context, which works perfectly with Playwright.
"""
import sys
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def run_scraper_subprocess(scraper_id: str, timeout: int = 600) -> dict:
    """
    Run a scraper in a separate subprocess with timeout protection.

    Args:
        scraper_id: The scraper ID to run (e.g., "wholesomeco", "curaleaf-lehi")
        timeout: Maximum execution time in seconds (default: 600 = 10 minutes)

    Returns:
        dict with status and details of the scraper run

    Raises:
        subprocess.TimeoutExpired: If scraper exceeds timeout
        subprocess.CalledProcessError: If scraper process fails
    """
    # Get the path to the Python interpreter in the venv
    venv_python = Path(sys.executable)

    # Get the backend directory
    backend_dir = Path(__file__).parent.parent

    # Build the command to run the scraper script
    scraper_script = backend_dir / "run_scraper_subprocess.py"

    cmd = [
        str(venv_python),
        str(scraper_script),
        scraper_id
    ]

    logger.info(f"Starting scraper '{scraper_id}' in subprocess with {timeout}s timeout")
    logger.debug(f"Command: {' '.join(cmd)}")

    try:
        # Run the subprocess with timeout
        result = subprocess.run(
            cmd,
            cwd=str(backend_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )

        logger.info(f"Scraper '{scraper_id}' completed successfully")
        logger.debug(f"Stdout: {result.stdout}")

        if result.stderr:
            logger.warning(f"Stderr: {result.stderr}")

        return {
            "status": "success",
            "scraper_id": scraper_id,
            "message": "Scraper completed successfully"
        }

    except subprocess.TimeoutExpired as e:
        logger.error(f"Scraper '{scraper_id}' timed out after {timeout} seconds")
        logger.debug(f"Partial stdout: {e.stdout}")
        logger.debug(f"Partial stderr: {e.stderr}")

        # Mark the scraper run as timeout in the database
        # This will be done by checking the ScraperRun status
        return {
            "status": "timeout",
            "scraper_id": scraper_id,
            "message": f"Scraper timed out after {timeout} seconds"
        }

    except subprocess.CalledProcessError as e:
        logger.error(f"Scraper '{scraper_id}' failed with exit code {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")

        return {
            "status": "error",
            "scraper_id": scraper_id,
            "message": f"Scraper failed with exit code {e.returncode}",
            "error": e.stderr
        }

    except Exception as e:
        logger.error(f"Unexpected error running scraper '{scraper_id}': {e}", exc_info=True)

        return {
            "status": "error",
            "scraper_id": scraper_id,
            "message": f"Unexpected error: {str(e)}"
        }


async def run_scraper_subprocess_async(scraper_id: str, timeout: int = 600) -> dict:
    """
    Async wrapper for run_scraper_subprocess.

    Runs the subprocess in a thread pool executor to avoid blocking the event loop.

    Args:
        scraper_id: The scraper ID to run
        timeout: Maximum execution time in seconds

    Returns:
        dict with status and details of the scraper run
    """
    loop = asyncio.get_event_loop()

    # Run the blocking subprocess call in a thread pool
    result = await loop.run_in_executor(
        None,  # Use default executor
        run_scraper_subprocess,
        scraper_id,
        timeout
    )

    return result
