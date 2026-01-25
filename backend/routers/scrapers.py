from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import time

from database import get_db
from services.scraper_runner import ScraperRunner
from services.scrapers.wholesome_co_scraper import WholesomeCoScraper
from models import Product, Price, Dispensary

router = APIRouter(prefix="/scrapers", tags=["scrapers"])


# Response Models
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

@router.get("/dashboard", response_class=HTMLResponse)
async def scraper_dashboard():
    """Simple dashboard to trigger scrapers manually"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🕷️ Scraper Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 2rem auto; padding: 0 1rem; background: #f9f9f9; }
            .card { background: white; border: 1px solid #ddd; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 1rem; }
            h1 { color: #333; }
            button { background: #10b981; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
            button:hover { background: #059669; }
            button:disabled { background: #ccc; cursor: not-allowed; }
            .status { margin-top: 1rem; padding: 1rem; background: #f3f4f6; border-radius: 6px; display: none; }
            pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; }
        </style>
    </head>
    <body>
        <h1>🕷️ Scraper Control Center</h1>
        
        <div class="card">
            <h2>WholesomeCo</h2>
            <p>Scrape products directly from WholesomeCo website and save to database.</p>
            <button onclick="runScraper('wholesomeco')">🚀 Run Scraper</button>
            <div id="status-wholesomeco" class="status"></div>
        </div>

        <script>
            async function runScraper(name) {
                const btn = document.querySelector(`button[onclick="runScraper('${name}')"]`);
                const statusDiv = document.getElementById(`status-${name}`);
                
                btn.disabled = true;
                btn.textContent = "Running... (Please Wait)";
                statusDiv.style.display = "block";
                statusDiv.innerHTML = "⏳ Scraping in progress... check backend logs for details.";

                try {
                    const response = await fetch(`/scrapers/run/${name}`, { method: 'POST' });
                    const data = await response.json();
                    statusDiv.innerHTML = `<h3>✅ Result:</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
                } catch (e) {
                    statusDiv.innerHTML = `<h3>❌ Error:</h3><pre>${e.message}</pre>`;
                } finally {
                    btn.disabled = false;
                    btn.textContent = "🚀 Run Scraper";
                }
            }
        </script>
    </body>
    </html>
    """

@router.get("/test/wholesomeco", response_model=ScraperTestResponse)
async def test_wholesomeco_scraper():
    """
    Test WholesomeCo scraper and return raw scraped data WITHOUT saving to database.

    This endpoint is useful for:
    - Testing scraper functionality
    - Inspecting raw scraped data
    - Debugging scraping issues
    - Verifying data extraction logic

    Returns all scraped products with complete details including raw_data field.
    """
    start_time = time.time()

    try:
        scraper = WholesomeCoScraper()
        products = await scraper.scrape_products()

        duration = time.time() - start_time

        # Convert ScrapedProduct dataclass to Pydantic model
        product_responses = [
            ScrapedProductResponse(
                name=p.name,
                brand=p.brand,
                category=p.category,
                price=p.price,
                thc_percentage=p.thc_percentage,
                cbd_percentage=p.cbd_percentage,
                unit_size=p.unit_size,
                raw_data=p.raw_data
            )
            for p in products
        ]

        return ScraperTestResponse(
            scraper="wholesomeco",
            products_found=len(products),
            duration=round(duration, 2),
            products=product_responses
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scraper test failed: {str(e)}"
        )


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

    # WholesomeCo status
    try:
        # Find WholesomeCo dispensary
        wholesomeco_disp = db.query(Dispensary).filter(
            Dispensary.name.ilike("%wholesome%")
        ).first()

        if wholesomeco_disp:
            # Get most recent price update as proxy for last scraper run
            latest_price = db.query(Price).filter(
                Price.dispensary_id == wholesomeco_disp.id
            ).order_by(desc(Price.last_updated)).first()

            if latest_price:
                # Count products from this dispensary
                product_count = db.query(Price).filter(
                    Price.dispensary_id == wholesomeco_disp.id
                ).count()

                statuses.append(ScraperStatusResponse(
                    name="wholesomeco",
                    last_run=latest_price.last_updated,
                    status="success",
                    last_product_count=product_count,
                    error_message=None
                ))
            else:
                statuses.append(ScraperStatusResponse(
                    name="wholesomeco",
                    last_run=None,
                    status="never_run",
                    last_product_count=0,
                    error_message=None
                ))
        else:
            statuses.append(ScraperStatusResponse(
                name="wholesomeco",
                last_run=None,
                status="never_run",
                last_product_count=0,
                error_message="Dispensary not found in database"
            ))
    except Exception as e:
        statuses.append(ScraperStatusResponse(
            name="wholesomeco",
            last_run=None,
            status="failed",
            last_product_count=0,
            error_message=str(e)
        ))

    return statuses


@router.get("/products/recent/{scraper_name}", response_model=List[RecentProductResponse])
async def get_recent_products(
    scraper_name: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get recently scraped products from database for a specific scraper.

    This shows products that were actually saved to the database from the most recent scraper run.

    Args:
        scraper_name: Name of the scraper (e.g., "wholesomeco")
        limit: Maximum number of products to return (default: 20)

    Returns list of products with current prices and stock status.
    """
    # Map scraper name to dispensary
    dispensary_map = {
        "wholesomeco": "wholesome"
    }

    search_term = dispensary_map.get(scraper_name.lower())
    if not search_term:
        raise HTTPException(
            status_code=404,
            detail=f"Scraper '{scraper_name}' not found"
        )

    # Find dispensary
    dispensary = db.query(Dispensary).filter(
        Dispensary.name.ilike(f"%{search_term}%")
    ).first()

    if not dispensary:
        raise HTTPException(
            status_code=404,
            detail=f"Dispensary for scraper '{scraper_name}' not found in database"
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


@router.post("/run/wholesomeco")
async def run_wholesomeco(db: Session = Depends(get_db)):
    """Trigger the WholesomeCo scraper and save results to database"""
    runner = ScraperRunner(db)
    result = await runner.run_wholesomeco()
    return result