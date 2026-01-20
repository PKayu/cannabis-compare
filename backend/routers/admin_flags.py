"""
Admin routes for ScraperFlag management and product normalization.

Provides endpoints for:
- Viewing pending flags in the cleanup queue
- Approving/rejecting flag merges
- Merging and splitting products
- Viewing outlier price alerts
- Statistics and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database import get_db
from models import ScraperFlag, Product, Price, Brand, Dispensary
from services.normalization.flag_processor import ScraperFlagProcessor
from services.quality.outlier_detection import OutlierDetector

router = APIRouter(prefix="/api/admin", tags=["admin"])


# === Pydantic Schemas ===

class FlagActionRequest(BaseModel):
    notes: Optional[str] = ""


class MergeRequest(BaseModel):
    source_product_id: str
    target_product_id: str


class SplitRequest(BaseModel):
    product_name: str
    brand_id: str
    product_type: Optional[str] = "Unknown"


class FlagStatsResponse(BaseModel):
    pending: int
    approved: int
    rejected: int
    total: int


# === Admin Verification (Placeholder) ===

async def get_current_user():
    """Placeholder for user authentication"""
    return "admin-user-id"


async def verify_admin(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """
    Verify user has admin privileges.
    TODO: Implement proper admin verification with JWT/Supabase.
    """
    if user_id not in ["admin-user-id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return user_id


# === Flag CRUD Endpoints ===

@router.get("/flags/pending")
async def get_pending_flags(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    dispensary_id: Optional[str] = None
):
    """Get pending ScraperFlags for admin review."""
    return ScraperFlagProcessor.get_pending_flags(
        db=db,
        limit=limit,
        offset=skip,
        dispensary_id=dispensary_id
    )


@router.get("/flags/stats", response_model=FlagStatsResponse)
async def get_flag_stats(db: Session = Depends(get_db)):
    """Get statistics on ScraperFlags"""
    pending = db.query(ScraperFlag).filter(ScraperFlag.status == "pending").count()
    approved = db.query(ScraperFlag).filter(ScraperFlag.status == "approved").count()
    rejected = db.query(ScraperFlag).filter(ScraperFlag.status == "rejected").count()

    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total": pending + approved + rejected
    }


@router.get("/flags/{flag_id}")
async def get_flag_detail(
    flag_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific flag"""
    flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    dispensary = db.query(Dispensary).filter(
        Dispensary.id == flag.dispensary_id
    ).first()

    matched_product = None
    if flag.matched_product_id:
        product = db.query(Product).filter(
            Product.id == flag.matched_product_id
        ).first()
        if product:
            matched_product = {
                "id": product.id,
                "name": product.name,
                "brand": product.brand.name if product.brand else None,
                "thc_percentage": product.thc_percentage,
                "cbd_percentage": product.cbd_percentage
            }

    return {
        "id": flag.id,
        "original_name": flag.original_name,
        "original_thc": flag.original_thc,
        "original_cbd": flag.original_cbd,
        "brand_name": flag.brand_name,
        "dispensary_id": flag.dispensary_id,
        "dispensary_name": dispensary.name if dispensary else None,
        "confidence_score": flag.confidence_score,
        "matched_product": matched_product,
        "status": flag.status,
        "created_at": flag.created_at.isoformat()
    }


@router.post("/flags/approve/{flag_id}")
async def approve_flag(
    flag_id: str,
    request: FlagActionRequest = Body(default=FlagActionRequest()),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Approve merging flagged product to matched product."""
    try:
        product_id = ScraperFlagProcessor.approve_flag(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            notes=request.notes or ""
        )
        return {"status": "approved", "product_id": product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/flags/reject/{flag_id}")
async def reject_flag(
    flag_id: str,
    request: FlagActionRequest = Body(default=FlagActionRequest()),
    product_type: str = Query("Unknown"),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Reject flag and create new master product."""
    try:
        new_product_id = ScraperFlagProcessor.reject_flag(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            product_type=product_type,
            notes=request.notes or ""
        )
        return {"status": "rejected", "new_product_id": new_product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# === Product Merge/Split Endpoints ===

@router.post("/products/merge")
async def merge_products(
    request: MergeRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Merge source product into target product."""
    source = db.query(Product).filter(Product.id == request.source_product_id).first()
    target = db.query(Product).filter(Product.id == request.target_product_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source product not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target product not found")

    # Update all prices from source to target
    price_count = (
        db.query(Price)
        .filter(Price.product_id == request.source_product_id)
        .update({Price.product_id: request.target_product_id})
    )

    source.is_master = False
    source.master_product_id = request.target_product_id

    db.commit()

    return {
        "status": "merged",
        "target_id": request.target_product_id,
        "prices_moved": price_count
    }


@router.post("/products/{product_id}/split")
async def split_product(
    product_id: str,
    request: SplitRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Create a new product by splitting from existing."""
    source = db.query(Product).filter(Product.id == product_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Product not found")

    brand = db.query(Brand).filter(Brand.id == request.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    new_product = Product(
        name=request.product_name,
        product_type=request.product_type or source.product_type,
        brand_id=request.brand_id,
        thc_percentage=source.thc_percentage,
        cbd_percentage=source.cbd_percentage,
        is_master=True,
        normalization_confidence=1.0
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {"status": "split", "new_product_id": new_product.id}


# === Outlier Detection Endpoints ===

@router.get("/outliers")
async def get_price_outliers(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100)
):
    """Get price outliers across all products."""
    outliers = OutlierDetector.get_all_outliers(db=db, limit=limit)
    return {"count": len(outliers), "outliers": outliers}


@router.get("/dashboard")
async def get_admin_dashboard(db: Session = Depends(get_db)):
    """Get admin dashboard summary."""
    pending_flags = ScraperFlagProcessor.get_flag_count(db, "pending")
    total_products = db.query(Product).filter(Product.is_master == True).count()
    total_prices = db.query(Price).count()
    outliers = OutlierDetector.get_all_outliers(db, limit=100)
    high_severity = len([o for o in outliers if o["severity"] == "high"])

    return {
        "flags": {"pending": pending_flags},
        "products": {"total_master": total_products, "total_prices": total_prices},
        "quality": {"outliers_total": len(outliers), "outliers_high_severity": high_severity}
    }
