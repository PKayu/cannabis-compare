"""
Main FastAPI application entry point for Utah Cannabis Aggregator
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import admin_flags, search, products, dispensaries, auth, users, scrapers

# Initialize FastAPI app
app = FastAPI(
    title="Utah Cannabis Aggregator API",
    description="REST API for cannabis price aggregation and reviews",
    version="0.1.0"
)

# Register routers
app.include_router(admin_flags.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(search.router)
app.include_router(products.router)
app.include_router(dispensaries.router)
app.include_router(scrapers.router)


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

# TODO: Add routers for:
# - Users (auth, profiles)
# - Products (catalog, search)
# - Prices (aggregation, comparison)
# - Reviews (ratings, comments)
# - Dispensaries (index, locations)
# - Scrapers (data ingestion)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
