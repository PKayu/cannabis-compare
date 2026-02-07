"""
Admin routes for scraper monitoring, scheduling, and run history.

Provides endpoints for:
- Viewing scraper run history with filtering
- Health metrics per scraper (success rates, durations)
- Scheduler status and control (pause, resume, trigger)
- Data quality and dispensary freshness metrics
"""
import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from typing import Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel

from database import get_db, SessionLocal
from models import ScraperRun, Product, Price, Brand, Dispensary
from services.scrapers.registry import ScraperRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/scrapers", tags=["admin-scrapers"])


# === Pydantic Response Models ===

class ScraperRunResponse(BaseModel):
    id: str
    scraper_id: str
    scraper_name: str
    dispensary_id: Optional[str] = None
    started_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    status: str
    products_found: int
    products_processed: int
    flags_created: int
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    triggered_by: Optional[str] = None


class ScraperHealthResponse(BaseModel):
    scraper_id: str
    scraper_name: str
    enabled: bool
    total_runs_7d: int
    successful_runs_7d: int
    failed_runs_7d: int
    success_rate_7d: float
    avg_duration_seconds: Optional[float] = None
    last_run_at: Optional[str] = None
    last_run_status: Optional[str] = None
    total_products_last_run: int = 0


class SchedulerStatusResponse(BaseModel):
    is_running: bool
    job_count: int
    jobs: list


class QualityMetricsResponse(BaseModel):
    total_master_products: int
    missing_thc_count: int
    missing_thc_pct: float
    missing_cbd_count: int
    missing_cbd_pct: float
    missing_brand_count: int
    missing_brand_pct: float
    low_confidence_count: int
    category_distribution: dict


class DispensaryFreshnessResponse(BaseModel):
    dispensary_id: str
    dispensary_name: str
    last_successful_scrape: Optional[str] = None
    hours_since_last_scrape: Optional[float] = None
    status: str  # "fresh", "stale", "critical", "never"


# === Run History ===

@router.get("/runs", response_model=List[ScraperRunResponse])
async def get_scraper_runs(
    db: Session = Depends(get_db),
    scraper_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Get paginated scraper run history with optional filtering."""
    query = db.query(ScraperRun).order_by(desc(ScraperRun.started_at))

    if scraper_id:
        query = query.filter(ScraperRun.scraper_id == scraper_id)
    if status:
        query = query.filter(ScraperRun.status == status)

    runs = query.offset(offset).limit(limit).all()

    return [
        ScraperRunResponse(
            id=r.id,
            scraper_id=r.scraper_id,
            scraper_name=r.scraper_name,
            dispensary_id=r.dispensary_id,
            started_at=r.started_at.isoformat() if r.started_at else None,
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            duration_seconds=r.duration_seconds,
            status=r.status,
            products_found=r.products_found or 0,
            products_processed=r.products_processed or 0,
            flags_created=r.flags_created or 0,
            error_message=r.error_message,
            error_type=r.error_type,
            triggered_by=r.triggered_by,
        )
        for r in runs
    ]


# === Health Metrics ===

@router.get("/health", response_model=List[ScraperHealthResponse])
async def get_scraper_health(db: Session = Depends(get_db)):
    """Get 7-day health metrics for all registered scrapers."""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    all_scrapers = ScraperRegistry.get_all()
    results = []

    for sid, config in all_scrapers.items():
        runs = db.query(ScraperRun).filter(
            ScraperRun.scraper_id == sid,
            ScraperRun.started_at >= seven_days_ago
        ).all()

        total = len(runs)
        successful = sum(1 for r in runs if r.status == "success")
        failed = sum(1 for r in runs if r.status == "error")
        durations = [r.duration_seconds for r in runs if r.duration_seconds is not None]

        last_run = db.query(ScraperRun).filter(
            ScraperRun.scraper_id == sid
        ).order_by(desc(ScraperRun.started_at)).first()

        results.append(ScraperHealthResponse(
            scraper_id=sid,
            scraper_name=config.name,
            enabled=config.enabled,
            total_runs_7d=total,
            successful_runs_7d=successful,
            failed_runs_7d=failed,
            success_rate_7d=round(successful / total * 100, 1) if total > 0 else 0.0,
            avg_duration_seconds=round(sum(durations) / len(durations), 1) if durations else None,
            last_run_at=last_run.started_at.isoformat() if last_run else None,
            last_run_status=last_run.status if last_run else None,
            total_products_last_run=last_run.products_found if last_run else 0,
        ))

    return results


# === Scheduler Status & Control ===

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and upcoming jobs."""
    from services.scheduler import get_scheduler
    scheduler = get_scheduler()

    return SchedulerStatusResponse(
        is_running=scheduler.is_running,
        job_count=scheduler.job_count,
        jobs=scheduler.get_all_jobs()
    )


async def _run_scraper_in_background(scraper_id: str) -> None:
    """Run a scraper with its own database session (for background execution)."""
    from services.scraper_runner import ScraperRunner

    db = SessionLocal()
    try:
        runner = ScraperRunner(db, triggered_by="admin-manual")
        result = await runner.run_by_id(scraper_id)
        logger.info(f"Background scraper run complete for '{scraper_id}': {result.get('status')}")
    except Exception as e:
        logger.error(f"Background scraper run failed for '{scraper_id}': {e}", exc_info=True)
    finally:
        db.close()


@router.post("/run/{scraper_id}")
async def trigger_scraper_run(
    scraper_id: str,
    background_tasks: BackgroundTasks,
):
    """Manually trigger a scraper run in the background.

    Returns immediately with status 'started'. The scraper runs
    asynchronously -- poll /health or /runs to check progress.
    """
    config = ScraperRegistry.get(scraper_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Scraper '{scraper_id}' not found")

    if not config.enabled:
        raise HTTPException(status_code=400, detail=f"Scraper '{scraper_id}' is disabled")

    # Schedule the scraper to run in the background with its own DB session
    loop = asyncio.get_event_loop()
    loop.create_task(_run_scraper_in_background(scraper_id))

    return {
        "status": "started",
        "scraper_id": scraper_id,
        "scraper_name": config.name,
        "message": f"Scraper '{config.name}' started. Poll /health or /runs to check progress."
    }


@router.post("/scheduler/pause/{scraper_id}")
async def pause_scraper(scraper_id: str):
    """Pause scheduled runs for a scraper."""
    from services.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler.pause_scraper(scraper_id):
        return {"status": "paused", "scraper_id": scraper_id}
    raise HTTPException(status_code=404, detail="Scraper job not found in scheduler")


@router.post("/scheduler/resume/{scraper_id}")
async def resume_scraper(scraper_id: str):
    """Resume scheduled runs for a scraper."""
    from services.scheduler import get_scheduler
    scheduler = get_scheduler()
    if scheduler.resume_scraper(scraper_id):
        return {"status": "resumed", "scraper_id": scraper_id}
    raise HTTPException(status_code=404, detail="Scraper job not found in scheduler")


# === Data Quality Metrics ===

@router.get("/quality/metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics(db: Session = Depends(get_db)):
    """Get data quality metrics for master products."""
    total = db.query(Product).filter(Product.is_master == True).count()
    if total == 0:
        return QualityMetricsResponse(
            total_master_products=0,
            missing_thc_count=0, missing_thc_pct=0.0,
            missing_cbd_count=0, missing_cbd_pct=0.0,
            missing_brand_count=0, missing_brand_pct=0.0,
            low_confidence_count=0,
            category_distribution={}
        )

    missing_thc = db.query(Product).filter(
        Product.is_master == True, Product.thc_percentage == None
    ).count()
    missing_cbd = db.query(Product).filter(
        Product.is_master == True, Product.cbd_percentage == None
    ).count()
    missing_brand = db.query(Product).filter(
        Product.is_master == True, Product.brand_id == None
    ).count()
    low_confidence = db.query(Product).filter(
        Product.is_master == True, Product.normalization_confidence < 0.9
    ).count()

    # Category distribution
    categories = db.query(
        Product.product_type, func.count(Product.id)
    ).filter(
        Product.is_master == True
    ).group_by(Product.product_type).all()

    return QualityMetricsResponse(
        total_master_products=total,
        missing_thc_count=missing_thc,
        missing_thc_pct=round(missing_thc / total * 100, 1),
        missing_cbd_count=missing_cbd,
        missing_cbd_pct=round(missing_cbd / total * 100, 1),
        missing_brand_count=missing_brand,
        missing_brand_pct=round(missing_brand / total * 100, 1),
        low_confidence_count=low_confidence,
        category_distribution={cat: count for cat, count in categories}
    )


# === Dispensary Freshness ===

@router.get("/dispensaries/freshness", response_model=List[DispensaryFreshnessResponse])
async def get_dispensary_freshness(db: Session = Depends(get_db)):
    """Get last successful scrape time per dispensary."""
    dispensaries = db.query(Dispensary).all()
    now = datetime.utcnow()
    results = []

    for disp in dispensaries:
        last_success = db.query(ScraperRun).filter(
            ScraperRun.dispensary_id == disp.id,
            ScraperRun.status == "success"
        ).order_by(desc(ScraperRun.started_at)).first()

        if last_success:
            hours_ago = (now - last_success.started_at).total_seconds() / 3600
            if hours_ago < 24:
                status = "fresh"
            elif hours_ago < 48:
                status = "stale"
            else:
                status = "critical"
        else:
            hours_ago = None
            status = "never"

        results.append(DispensaryFreshnessResponse(
            dispensary_id=disp.id,
            dispensary_name=disp.name,
            last_successful_scrape=last_success.started_at.isoformat() if last_success else None,
            hours_since_last_scrape=round(hours_ago, 1) if hours_ago is not None else None,
            status=status,
        ))

    return results
