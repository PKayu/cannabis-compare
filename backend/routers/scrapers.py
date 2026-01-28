"""
Scraper Router - FastAPI endpoints for running and managing scrapers.

This router provides:
1. Dynamic endpoints that work with any registered scraper
2. Manual trigger endpoints for testing
3. Status and listing endpoints
4. Web dashboard for manual scraper execution

The endpoints use the ScraperRegistry to dynamically discover and run
any registered scraper without requiring code changes.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

from database import get_db
from services.scraper_runner import ScraperRunner
from services.scrapers.registry import ScraperRegistry
from services.scrapers.base_scraper import BaseScraper, ScrapedProduct
from models import Product, Price, Dispensary

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


# ========== Response Models ==========

class ScrapedProductResponse(BaseModel):
    """Response model for scraped product data"""
    name: str
    brand: str
    category: str
    price: float
    thc_percentage: Optional[float] = None
    cbd_percentage: Optional[float] = None
    unit_size: Optional[str] = None
    raw_data: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Gorilla Glue #4",
                "brand": "Tryke",
                "category": "Flower",
                "price": 45.0,
                "thc_percentage": 24.5,
                "cbd_percentage": 0.1,
                "unit_size": "3.5g",
                "raw_data": {"source_url": "https://www.wholesome.co/shop"}
            }
        }


class ScraperTestResponse(BaseModel):
    """Response model for scraper test endpoint"""
    scraper: str
    products_found: int
    duration: float = Field(..., description="Duration in seconds")
    products: List[ScrapedProductResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "scraper": "wholesomeco",
                "products_found": 150,
                "duration": 2.45,
                "products": [
                    {
                        "name": "Gorilla Glue #4",
                        "brand": "Tryke",
                        "category": "Flower",
                        "price": 45.0,
                        "thc_percentage": 24.5,
                        "cbd_percentage": 0.1,
                        "unit_size": "3.5g",
                        "raw_data": {}
                    }
                ]
            }
        }


class ScraperInfoResponse(BaseModel):
    """Response model for scraper information"""
    id: str
    name: str
    description: str
    enabled: bool
    dispensary_name: str
    dispensary_location: str
    schedule_minutes: int

    class Config:
        json_schema_extra = {
            "example": {
                "id": "wholesomeco",
                "name": "WholesomeCo",
                "description": "Direct scraping from WholesomeCo website",
                "enabled": True,
                "dispensary_name": "WholesomeCo",
                "dispensary_location": "Bountiful, UT",
                "schedule_minutes": 120
            }
        }


class ScraperStatusResponse(BaseModel):
    """Response model for scraper status"""
    name: str
    last_run: Optional[datetime] = None
    status: str = Field(..., description="Status: success, failed, or never_run")
    last_product_count: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "wholesomeco",
                "last_run": "2024-01-25T10:30:00",
                "status": "success",
                "last_product_count": 150,
                "error_message": None
            }
        }


class RecentProductResponse(BaseModel):
    """Response model for recently scraped products from database"""
    product_id: str
    name: str
    brand: str
    product_type: str
    thc_percentage: Optional[float]
    price: float
    dispensary: str
    in_stock: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "product_id": "prod-123",
                "name": "Gorilla Glue #4",
                "brand": "Tryke",
                "product_type": "Flower",
                "thc_percentage": 24.5,
                "price": 45.0,
                "dispensary": "WholesomeCo",
                "in_stock": True,
                "created_at": "2024-01-25T10:30:00"
            }
        }


# ========== Dashboard Endpoints ==========

@router.get("/dashboard", response_class=HTMLResponse)
async def scraper_dashboard():
    """
    Simple dashboard to trigger scrapers manually.

    Provides a web interface for running scrapers without API access.
    Useful for quick manual testing and one-off imports.
    """
    scrapers = ScraperRegistry.get_all()

    # Generate buttons for each scraper
    scraper_buttons = ""
    for scraper_id, config in scrapers.items():
        scraper_buttons += f"""
        <div class="card">
            <h2>{config.name}</h2>
            <p>{config.description or config.dispensary_name}</p>
            <button onclick="runScraper('{scraper_id}')">🚀 Run Scraper</button>
            <div id="status-{scraper_id}" class="status"></div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🕷️ Scraper Dashboard</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; background: #f9f9f9; }}
            .card {{ background: white; border: 1px solid #ddd; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 1rem; }}
            h1 {{ color: #333; }}
            h2 {{ margin-top: 0; color: #555; }}
            p {{ color: #666; }}
            button {{ background: #10b981; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; font-size: 1rem; cursor: pointer; transition: background 0.2s; }}
            button:hover {{ background: #059669; }}
            button:disabled {{ background: #ccc; cursor: not-allowed; }}
            .status {{ margin-top: 1rem; padding: 1rem; background: #f3f4f6; border-radius: 6px; display: none; }}
            pre {{ white-space: pre-wrap; word-wrap: break-word; margin: 0; }}
        </style>
    </head>
    <body>
        <h1>🕷️ Scraper Control Center</h1>
        {scraper_buttons}

        <script>
            async function runScraper(scraperId) {{
                const btn = document.querySelector(`button[onclick="runScraper('${{scraperId}}')"]`);
                const statusDiv = document.getElementById(`status-${{scraperId}}`);

                btn.disabled = true;
                btn.textContent = "Running... (Please Wait)";
                statusDiv.style.display = "block";
                statusDiv.innerHTML = "⏳ Scraping in progress... check backend logs for details.";

                try {{
                    const response = await fetch(`/scrapers/run/${{scraperId}}`, {{ method: 'POST' }});
                    const data = await response.json();
                    statusDiv.innerHTML = `<h3>${{data.status === 'success' ? '✅' : '❌'}} Result:</h3><pre>${{JSON.stringify(data, null, 2)}}</pre>`;
                }} catch (e) {{
                    statusDiv.innerHTML = `<h3>❌ Error:</h3><pre>${{e.message}}</pre>`;
                }} finally {{
                    btn.disabled = false;
                    btn.textContent = "🚀 Run Scraper";
                }}
            }}
        </script>
    </body>
    </html>
    """


# ========== Dynamic Scraper Endpoints ==========

@router.get("/list", response_model=List[ScraperInfoResponse])
async def list_scrapers():
    """
    List all registered scrapers.

    Returns information about all available scrapers including
    their IDs, names, enabled status, and schedule configuration.
    """
    scrapers = []
    for config in ScraperRegistry.get_all().values():
        scrapers.append(ScraperInfoResponse(
            id=config.id,
            name=config.name,
            description=config.description,
            enabled=config.enabled,
            dispensary_name=config.dispensary_name,
            dispensary_location=config.dispensary_location,
            schedule_minutes=config.schedule_minutes
        ))
    return scrapers


@router.post("/run/{scraper_id}")
async def run_scraper(scraper_id: str, db: Session = Depends(get_db)):
    """
    Run a specific scraper by ID and save results to database.

    This endpoint works with any registered scraper. The scraper
    is instantiated from the registry, executed, and results are
    saved to the database.

    Args:
        scraper_id: The scraper's registry ID (e.g., "wholesomeco", "beehive")
        db: Database session

    Returns:
        Result of the scrape including product count and status
    """
    runner = ScraperRunner(db)
    try:
        result = await runner.run_by_id(scraper_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraper failed: {str(e)}")


@router.post("/run/all")
async def run_all_scrapers(db: Session = Depends(get_db)):
    """
    Run all enabled scrapers and save results to database.

    Executes each enabled scraper sequentially. Results are
    returned as a mapping of scraper IDs to their results.

    Args:
        db: Database session

    Returns:
        Dict mapping scraper IDs to their scrape results
    """
    runner = ScraperRunner(db)
    return await runner.run_all()


@router.get("/test/{scraper_id}", response_model=ScraperTestResponse)
async def test_scraper(scraper_id: str):
    """
    Test a scraper without saving to database.

    This endpoint is useful for:
    - Testing scraper functionality
    - Inspecting raw scraped data
    - Debugging scraping issues
    - Verifying data extraction logic

    Returns all scraped products with complete details including raw_data field.

    Args:
        scraper_id: The scraper's registry ID

    Returns:
        ScraperTestResponse with products and duration
    """
    config = ScraperRegistry.get(scraper_id)

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Scraper '{scraper_id}' not found. "
                   f"Available: {list(ScraperRegistry.get_all().keys())}"
        )

    if not config.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Scraper '{scraper_id}' is disabled"
        )

    start_time = time.time()

    try:
        scraper = config.scraper_class(dispensary_id=scraper_id)
        products = await scraper.scrape_products()

        duration = time.time() - start_time

        # Convert ScrapedProduct to Pydantic model
        product_responses = [
            ScrapedProductResponse(
                name=p.name,
                brand=p.brand,
                category=p.category,
                price=p.price,
                thc_percentage=p.thc_percentage,
                cbd_percentage=p.cbd_percentage,
                unit_size=p.weight,
                raw_data=p.raw_data
            )
            for p in products
        ]

        return ScraperTestResponse(
            scraper=scraper_id,
            products_found=len(products),
            duration=round(duration, 2),
            products=product_responses
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scraper test failed: {str(e)}"
        )


# ========== Status Endpoints ==========

@router.get("/status", response_model=List[ScraperStatusResponse])
async def get_scraper_status(db: Session = Depends(get_db)):
    """
    Get status and metadata for all configured scrapers.

    Returns information about:
    - Last successful run time
    - Number of products found in last run
    - Current status (success/failed/never_run)
    - Error messages if any

    Useful for monitoring scraper health and scheduling.
    """
    statuses = []

    for config in ScraperRegistry.get_all().values():
        try:
            # Find dispensary in database
            dispensary = db.query(Dispensary).filter(
                Dispensary.name == config.dispensary_name
            ).first()

            if dispensary:
                # Get most recent price update as proxy for last scraper run
                latest_price = db.query(Price).filter(
                    Price.dispensary_id == dispensary.id
                ).order_by(desc(Price.last_updated)).first()

                if latest_price:
                    # Count products from this dispensary
                    product_count = db.query(Price).filter(
                        Price.dispensary_id == dispensary.id
                    ).count()

                    statuses.append(ScraperStatusResponse(
                        name=config.id,
                        last_run=latest_price.last_updated,
                        status="success",
                        last_product_count=product_count,
                        error_message=None
                    ))
                else:
                    statuses.append(ScraperStatusResponse(
                        name=config.id,
                        last_run=None,
                        status="never_run",
                        last_product_count=0,
                        error_message=None
                    ))
            else:
                statuses.append(ScraperStatusResponse(
                    name=config.id,
                    last_run=None,
                    status="never_run",
                    last_product_count=0,
                    error_message="Dispensary not found in database"
                ))
        except Exception as e:
            statuses.append(ScraperStatusResponse(
                name=config.id,
                last_run=None,
                status="failed",
                last_product_count=0,
                error_message=str(e)
            ))

    return statuses


@router.get("/products/recent/{scraper_id}", response_model=List[RecentProductResponse])
async def get_recent_products(
    scraper_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get recently scraped products from database for a specific scraper.

    This shows products that were actually saved to the database from the most recent scraper run.

    Args:
        scraper_id: ID of the scraper (e.g., "wholesomeco")
        limit: Maximum number of products to return (default: 20)
        db: Database session

    Returns:
        List of products with current prices and stock status
    """
    config = ScraperRegistry.get(scraper_id)

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Scraper '{scraper_id}' not found"
        )

    # Find dispensary
    dispensary = db.query(Dispensary).filter(
        Dispensary.name == config.dispensary_name
    ).first()

    if not dispensary:
        raise HTTPException(
            status_code=404,
            detail=f"Dispensary '{config.dispensary_name}' not found in database"
        )

    # Get recent products with prices from this dispensary
    recent_prices = db.query(Price).filter(
        Price.dispensary_id == dispensary.id
    ).order_by(desc(Price.last_updated)).limit(limit).all()

    if not recent_prices:
        return []

    # Build response with product details
    results = []
    for price in recent_prices:
        product = price.product
        brand = product.brand

        results.append(RecentProductResponse(
            product_id=product.id,
            name=product.name,
            brand=brand.name if brand else "Unknown",
            product_type=product.product_type,
            thc_percentage=product.thc_percentage,
            price=price.amount,
            dispensary=dispensary.name,
            in_stock=price.in_stock,
            created_at=product.created_at
        ))

    return results


# ========== Backwards Compatibility Endpoints ==========

@router.post("/run/wholesomeco")
async def run_wholesomeco_legacy(db: Session = Depends(get_db)):
    """
    Legacy endpoint for running WholesomeCo scraper.

    Deprecated: Use POST /run/wholesomeco instead.
    """
    runner = ScraperRunner(db)
    return await runner.run_wholesomeco()
