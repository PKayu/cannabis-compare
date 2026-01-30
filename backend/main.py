"""
Main FastAPI application entry point for Utah Cannabis Aggregator

This module:
1. Initializes the FastAPI application
2. Registers all API routers
3. Imports scrapers to trigger self-registration via decorators
4. Configures CORS middleware
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import (
    admin_flags, admin_scrapers, search, products, dispensaries, auth, users,
    scrapers, reviews, watchlist, notifications
)

# Import all scrapers to trigger self-registration via @register_scraper decorator
# These imports must happen at module level for the registry to be populated
# The imported classes are not used directly - the decorator registers them
from services.scrapers.wholesome_co_scraper import WholesomeCoScraper  # noqa: F401
from services.scrapers.iheartjane_scraper import IHeartJaneScraper  # noqa: F401
from services.scrapers.playwright_scraper import (  # noqa: F401
    PlaywrightScraper,
    WholesomeCoScraper as WholesomeCoPlaywrightScraper,
    BeehiveScraper
)

from services.scrapers.registry import ScraperRegistry

import logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Manage application lifespan events.

    On startup:
    1. Log all registered scrapers
    2. Optionally start the scheduler with auto-registered scrapers
    """
    # Log registered scrapers at startup
    scrapers = ScraperRegistry.get_all()
    logger.info(f"Registered {len(scrapers)} scrapers:")
    for scraper_id, config in scrapers.items():
        status = "enabled" if config.enabled else "disabled"
        logger.info(f"  - {config.name} ({scraper_id}): {status}")

    # Start the scraper scheduler with persistent job storage
    from services.scheduler import get_scheduler, register_all_scrapers
    from config import settings
    scheduler = get_scheduler(database_url=settings.database_url)
    register_all_scrapers(scheduler)
    await scheduler.start()
    logger.info(f"Scraper scheduler started with {scheduler.job_count} jobs")

    yield

    # Graceful shutdown - wait for running jobs to complete
    scheduler = get_scheduler()
    await scheduler.stop(wait=True)
    logger.info("Scraper scheduler stopped")

# Initialize FastAPI app
app = FastAPI(
    title="Utah Cannabis Aggregator API",
    description="REST API for cannabis price aggregation and reviews",
    version="0.1.0",
    lifespan=lifespan
)

# Register routers
app.include_router(admin_flags.router)
app.include_router(admin_scrapers.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(search.router)
app.include_router(products.router)
app.include_router(dispensaries.router)
app.include_router(scrapers.router)
app.include_router(watchlist.router)
app.include_router(notifications.router)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {"status": "healthy", "version": "0.1.0"}

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint - API information
    """
    return {
        "message": "Utah Cannabis Aggregator API",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
