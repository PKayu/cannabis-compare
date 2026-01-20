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

class FlagResponse(BaseModel):
    id: str
    original_name: str
    original_thc: Optional[float]
    original_cbd: Optional[float]
    brand_name: str
    dispensary_id: str
    dispensary_name: Optional[str]
    matched_product_id: Optional[str]
    matched_product_name: Optional[str]
    confidence_score: float
    confidence_percent: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


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

async def verify_admin(
    # In production: user_id: str = Depends(get_current_user)
) -> str:
    """
    Verify user has admin privileges.

    TODO: Implement proper admin verification with JWT/Supabase.
    For now, returns a placeholder admin ID.
    """
    # Placeholder - in production, verify from JWT token
    return "admin-placeholder"


# === Flag CRUD Endpoints ===

@router.get("/flags/pending", response_model=List[dict])
async def get_pending_flags(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    dispensary_id: Optional[str] = None
):
    """
    Get pending ScraperFlags for admin review.

    Returns flags sorted by creation date (newest first).
    """
    return ScraperFlagProcessor.get_pending_flags(
        db=db,
        limit=limit,
        offset=skip,
        dispensary_id=dispensary_id
    )


@router.get("/flags/{flag_id}")
async def get_flag_detail(
    flag_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific flag"""
    flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()

    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")

    # Get related data
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
                "cbd_percentage": product.cbd_percentage,
                "product_type": product.product_type
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
        "confidence_percent": f"{flag.confidence_score:.0%}",
        "matched_product": matched_product,
        "status": flag.status,
        "merge_reason": flag.merge_reason,
        "admin_notes": flag.admin_notes,
        "resolved_by": flag.resolved_by,
        "resolved_at": flag.resolved_at.isoformat() if flag.resolved_at else None,
        "created_at": flag.created_at.isoformat()
    }


@router.post("/flags/approve/{flag_id}")
async def approve_flag(
    flag_id: str,
    request: FlagActionRequest = Body(default=FlagActionRequest()),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """
    Approve merging flagged product to matched product.

    The flagged product will be linked to the existing master product.
    """
    try:
        product_id = ScraperFlagProcessor.approve_flag(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            notes=request.notes or ""
        )
        return {
            "status": "approved",
            "product_id": product_id,
            "message": "Flag approved successfully"
        }
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
    """
    Reject flag and create new master product.

    A new product will be created from the flagged data.
    """
    try:
        new_product_id = ScraperFlagProcessor.reject_flag(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            product_type=product_type,
            notes=request.notes or ""
        )
        return {
            "status": "rejected",
            "new_product_id": new_product_id,
            "message": "Flag rejected, new product created"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/flags/bulk-approve")
async def bulk_approve_flags(
    flag_ids: List[str] = Body(...),
    notes: str = Body("Bulk approved"),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Approve multiple flags at once"""
    results = ScraperFlagProcessor.bulk_approve(
        db=db,
        flag_ids=flag_ids,
        admin_id=admin_id,
        notes=notes
    )
    return results


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


@router.get("/flags/recent")
async def get_recent_resolutions(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100)
):
    """Get recently resolved flags for audit trail"""
    return ScraperFlagProcessor.get_recent_resolutions(db=db, limit=limit)


# === Product Merge/Split Endpoints ===

@router.post("/products/merge")
async def merge_products(
    request: MergeRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """
    Merge source product into target product.

    All prices from source will be reassigned to target.
    Source product will be marked as non-master.
    """
    source = db.query(Product).filter(Product.id == request.source_product_id).first()
    target = db.query(Product).filter(Product.id == request.target_product_id).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source product not found")
    if not target:
        raise HTTPException(status_code=404, detail="Target product not found")
    if source.id == target.id:
        raise HTTPException(status_code=400, detail="Cannot merge product with itself")

    # Update all prices from source to target
    price_count = (
        db.query(Price)
        .filter(Price.product_id == request.source_product_id)
        .update({Price.product_id: request.target_product_id})
    )

    # Mark source as duplicate pointing to target
    source.is_master = False
    source.master_product_id = request.target_product_id

    db.commit()

    return {
        "status": "merged",
        "source_id": request.source_product_id,
        "target_id": request.target_product_id,
        "prices_moved": price_count,
        "message": f"Merged {source.name} into {target.name}"
    }


@router.post("/products/{product_id}/split")
async def split_product(
    product_id: str,
    request: SplitRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """
    Create a new product by splitting from existing.

    Use when a product entry actually represents multiple distinct products.
    """
    source = db.query(Product).filter(Product.id == product_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify brand exists
    brand = db.query(Brand).filter(Brand.id == request.brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    # Create new master product
    new_product = Product(
        name=request.product_name,
        product_type=request.product_type or source.product_type,
        brand_id=request.brand_id,
        thc_percentage=source.thc_percentage,
        cbd_percentage=source.cbd_percentage,
        is_master=True,
        normalization_confidence=1.0  # Admin-verified
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return {
        "status": "split",
        "source_id": product_id,
        "new_product_id": new_product.id,
        "new_product_name": new_product.name,
        "message": f"Created new product: {new_product.name}"
    }


@router.get("/products/merge-preview")
async def merge_preview(
    source_id: str = Query(...),
    target_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Preview what a merge would do.

    Shows affected prices and products before committing.
    """
    source = db.query(Product).filter(Product.id == source_id).first()
    target = db.query(Product).filter(Product.id == target_id).first()

    if not source or not target:
        raise HTTPException(status_code=404, detail="Product not found")

    source_prices = db.query(Price).filter(Price.product_id == source_id).all()

    return {
        "source": {
            "id": source.id,
            "name": source.name,
            "brand": source.brand.name if source.brand else None,
            "price_count": len(source_prices)
        },
        "target": {
            "id": target.id,
            "name": target.name,
            "brand": target.brand.name if target.brand else None
        },
        "action": f"Will move {len(source_prices)} price(s) from '{source.name}' to '{target.name}'",
        "reversible": False
    }


# === Outlier Detection Endpoints ===

@router.get("/outliers")
async def get_price_outliers(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get price outliers across all products.

    Returns prices that deviate significantly from state averages.
    """
    outliers = OutlierDetector.get_all_outliers(db=db, limit=limit)
    return {
        "count": len(outliers),
        "outliers": outliers
    }


@router.get("/outliers/product/{product_id}")
async def get_product_outliers(
    product_id: str,
    db: Session = Depends(get_db)
):
    """Get outlier analysis for a specific product"""
    # Get price statistics
    stats = OutlierDetector.get_product_price_range(db=db, product_id=product_id)

    # Get all prices for this product
    prices = (
        db.query(Price)
        .filter(Price.product_id == product_id)
        .filter(Price.in_stock == True)
        .all()
    )

    # Detect outliers
    outliers = OutlierDetector.detect_price_outliers(prices)

    # Get product info
    product = db.query(Product).filter(Product.id == product_id).first()

    return {
        "product": {
            "id": product.id,
            "name": product.name
        } if product else None,
        "statistics": stats,
        "outliers": outliers
    }


# === Dashboard Endpoints ===

@router.get("/dashboard")
async def get_admin_dashboard(db: Session = Depends(get_db)):
    """
    Get admin dashboard summary.

    Returns key metrics for monitoring data quality.
    """
    # Flag stats
    pending_flags = ScraperFlagProcessor.get_flag_count(db, "pending")

    # Product stats
    total_products = db.query(Product).filter(Product.is_master == True).count()
    total_prices = db.query(Price).count()

    # Outlier count
    outliers = OutlierDetector.get_all_outliers(db, limit=100)
    high_severity = len([o for o in outliers if o["severity"] == "high"])

    # Recent activity
    recent_resolutions = ScraperFlagProcessor.get_recent_resolutions(db, limit=5)

    return {
        "flags": {
            "pending": pending_flags,
            "requires_attention": pending_flags > 20
        },
        "products": {
            "total_master": total_products,
            "total_prices": total_prices
        },
        "quality": {
            "outliers_total": len(outliers),
            "outliers_high_severity": high_severity,
            "requires_attention": high_severity > 0
        },
        "recent_activity": recent_resolutions
    }
