"""
Admin routes for ScraperFlag management and product normalization.

Provides endpoints for:
- Viewing pending flags in the cleanup queue
- Approving/rejecting/dismissing flag merges
- Merging and splitting products
- Viewing outlier price alerts
- Scraper correction analytics
- Statistics and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

from database import get_db
from models import ScraperFlag, Product, Price, Brand, Dispensary
from services.normalization.flag_processor import ScraperFlagProcessor
from services.quality.outlier_detection import OutlierDetector
from services.admin.flag_analyzer import (
    compute_match_type,
    compute_data_quality,
    get_matched_product_dispensary_ids,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# === Pydantic Schemas ===

class FlagActionRequest(BaseModel):
    """Legacy schema kept for backward compatibility."""
    notes: Optional[str] = ""


class ApproveWithEditsRequest(BaseModel):
    """Request body for approving a flag with optional field overrides."""
    notes: Optional[str] = ""
    # Parent-level overrides (applied to matched parent product)
    name: Optional[str] = None
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    # Variant-level overrides (applied to the new variant)
    thc_percentage: Optional[float] = None
    cbd_percentage: Optional[float] = None
    weight: Optional[str] = None
    price: Optional[float] = None
    # Issue tags for analytics
    issue_tags: Optional[List[str]] = None


class RejectWithEditsRequest(BaseModel):
    """Request body for rejecting a flag with optional field overrides."""
    notes: Optional[str] = ""
    name: Optional[str] = None
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    thc_percentage: Optional[float] = None
    cbd_percentage: Optional[float] = None
    weight: Optional[str] = None
    price: Optional[float] = None
    issue_tags: Optional[List[str]] = None


class DismissRequest(BaseModel):
    """Request body for dismissing a flag without creating any product."""
    notes: Optional[str] = ""
    issue_tags: Optional[List[str]] = None


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
    dismissed: int
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
    dispensary_id: Optional[str] = None,
    match_type: Optional[str] = Query(None, pattern="^(cross_dispensary|same_dispensary)$"),
    data_quality: Optional[str] = None,  # Comma-separated: "good", "fair", "poor"
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    max_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    sort_by: Optional[str] = Query("created_at", pattern="^(confidence|created_at)$"),
    sort_order: Optional[str] = Query("desc", pattern="^(asc|desc)$"),
):
    """
    Get pending ScraperFlags for admin review with advanced filtering and sorting.

    New filtering capabilities:
    - match_type: Filter by cross-dispensary vs same-dispensary matches
    - data_quality: Filter by quality score (good, fair, poor)
    - min_confidence/max_confidence: Filter by confidence score range
    - sort_by: Sort by confidence score or creation date
    - sort_order: Ascending or descending
    """
    # Build base query with DB-level filters
    query = db.query(ScraperFlag).filter(ScraperFlag.status == "pending")

    if dispensary_id:
        query = query.filter(ScraperFlag.dispensary_id == dispensary_id)

    if min_confidence is not None:
        query = query.filter(ScraperFlag.confidence_score >= min_confidence)
    if max_confidence is not None:
        query = query.filter(ScraperFlag.confidence_score <= max_confidence)

    # Fetch all matching flags (we'll filter/sort/paginate in Python)
    # This is acceptable since cleanup queues rarely exceed 1000 pending flags
    all_flags = query.all()

    # Build full response list with computed fields, then filter
    flag_data = []
    for flag in all_flags:
        # Compute match type and quality
        match_type_computed = compute_match_type(flag, db)
        quality_computed = compute_data_quality(flag)

        # Apply Python-level filters
        if match_type and match_type_computed != match_type:
            continue

        if data_quality:
            quality_filters = [q.strip() for q in data_quality.split(",")]
            if quality_computed not in quality_filters:
                continue

        # Get dispensary name
        dispensary = db.query(Dispensary).filter(
            Dispensary.id == flag.dispensary_id
        ).first()

        # Get matched product if exists
        matched_product = None
        matched_product_dispensary_ids = []
        if flag.matched_product_id:
            matched_product_dispensary_ids = get_matched_product_dispensary_ids(
                flag.matched_product_id, db
            )

            product = db.query(Product).filter(
                Product.id == flag.matched_product_id
            ).first()
            if product:
                matched_product = {
                    "id": product.id,
                    "name": product.name,
                    "product_type": product.product_type,
                    "brand": product.brand.name if product.brand else None,
                    "brand_id": product.brand_id,
                    "thc_percentage": product.thc_percentage,
                    "cbd_percentage": product.cbd_percentage,
                }

        flag_data.append({
            "id": flag.id,
            "original_name": flag.original_name,
            "original_thc": flag.original_thc,
            "original_cbd": flag.original_cbd,
            "original_weight": flag.original_weight,
            "original_price": flag.original_price,
            "original_category": flag.original_category,
            "original_url": flag.original_url,
            "brand_name": flag.brand_name,
            "dispensary_id": flag.dispensary_id,
            "dispensary_name": dispensary.name if dispensary else None,
            "confidence_score": flag.confidence_score,
            "confidence_percent": f"{flag.confidence_score:.0%}",
            "matched_product": matched_product,
            "merge_reason": flag.merge_reason,
            "issue_tags": flag.issue_tags,
            "created_at": flag.created_at.isoformat(),
            # NEW computed fields
            "match_type": match_type_computed,
            "data_quality": quality_computed,
            "matched_product_dispensary_ids": matched_product_dispensary_ids,
            # Keep datetime for sorting
            "_created_at_dt": flag.created_at,
        })

    # Apply sorting in Python
    if sort_by == "confidence":
        flag_data.sort(
            key=lambda x: x["confidence_score"],
            reverse=(sort_order == "desc")
        )
    else:  # sort_by == "created_at"
        flag_data.sort(
            key=lambda x: x["_created_at_dt"],
            reverse=(sort_order == "desc")
        )

    # Apply pagination in Python
    paginated_results = flag_data[skip:skip + limit]

    # Remove internal fields
    for item in paginated_results:
        item.pop("_created_at_dt", None)

    return paginated_results


@router.get("/flags/stats", response_model=FlagStatsResponse)
async def get_flag_stats(db: Session = Depends(get_db)):
    """Get statistics on ScraperFlags."""
    pending = db.query(ScraperFlag).filter(ScraperFlag.status == "pending").count()
    approved = db.query(ScraperFlag).filter(ScraperFlag.status == "approved").count()
    rejected = db.query(ScraperFlag).filter(ScraperFlag.status == "rejected").count()
    dismissed = db.query(ScraperFlag).filter(ScraperFlag.status == "dismissed").count()

    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "dismissed": dismissed,
        "total": pending + approved + rejected + dismissed,
    }


@router.get("/flags/{flag_id}")
async def get_flag_detail(
    flag_id: str,
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific flag."""
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
                "product_type": product.product_type,
                "brand": product.brand.name if product.brand else None,
                "brand_id": product.brand_id,
                "thc_percentage": product.thc_percentage,
                "cbd_percentage": product.cbd_percentage,
            }

    return {
        "id": flag.id,
        "original_name": flag.original_name,
        "original_thc": flag.original_thc,
        "original_cbd": flag.original_cbd,
        "original_url": flag.original_url,
        "brand_name": flag.brand_name,
        "dispensary_id": flag.dispensary_id,
        "dispensary_name": dispensary.name if dispensary else None,
        "confidence_score": flag.confidence_score,
        "matched_product": matched_product,
        "status": flag.status,
        "created_at": flag.created_at.isoformat(),
    }


@router.post("/flags/approve/{flag_id}")
async def approve_flag(
    flag_id: str,
    request: ApproveWithEditsRequest = Body(default=ApproveWithEditsRequest()),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Approve merging flagged product to matched product, with optional field edits."""
    try:
        product_id = ScraperFlagProcessor.approve_flag(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            notes=request.notes or "",
            name=request.name,
            brand_name=request.brand_name,
            product_type=request.product_type,
            thc_percentage=request.thc_percentage,
            cbd_percentage=request.cbd_percentage,
            weight=request.weight,
            price=request.price,
            issue_tags=request.issue_tags,
        )
        return {"status": "approved", "product_id": product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/flags/reject/{flag_id}")
async def reject_flag(
    flag_id: str,
    request: RejectWithEditsRequest = Body(default=RejectWithEditsRequest()),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Reject flag and create new product, with optional field edits."""
    try:
        new_product_id = ScraperFlagProcessor.reject_flag(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            notes=request.notes or "",
            name=request.name,
            brand_name=request.brand_name,
            product_type=request.product_type,
            thc_percentage=request.thc_percentage,
            cbd_percentage=request.cbd_percentage,
            weight=request.weight,
            price=request.price,
            issue_tags=request.issue_tags,
        )
        return {"status": "rejected", "new_product_id": new_product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/flags/dismiss/{flag_id}")
async def dismiss_flag(
    flag_id: str,
    request: DismissRequest = Body(default=DismissRequest()),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Dismiss flag without creating any product. Kept for audit/analytics."""
    try:
        ScraperFlagProcessor.dismiss_flag(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            notes=request.notes or "",
            issue_tags=request.issue_tags,
        )
        return {"status": "dismissed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class BulkActionRequest(BaseModel):
    """Request body for bulk flag actions."""
    flag_ids: List[str]
    action: str  # "approve", "reject", or "dismiss"
    admin_notes: Optional[str] = ""


@router.post("/flags/bulk-action")
async def bulk_action_flags(
    request: BulkActionRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """
    Approve, reject, or dismiss multiple flags at once.

    Useful for batch processing obvious duplicates or dismissing
    bad scraper runs. Note: Bulk operations do not support per-flag
    field edits; use individual endpoints for complex corrections.
    """
    if request.action not in ["approve", "reject", "dismiss"]:
        raise HTTPException(
            status_code=400,
            detail="Action must be 'approve', 'reject', or 'dismiss'"
        )

    if not request.flag_ids:
        raise HTTPException(status_code=400, detail="No flag IDs provided")

    success_count = 0
    failed_count = 0
    errors = []

    for flag_id in request.flag_ids:
        try:
            if request.action == "approve":
                ScraperFlagProcessor.approve_flag(
                    db=db,
                    flag_id=flag_id,
                    admin_id=admin_id,
                    notes=request.admin_notes or "",
                )
            elif request.action == "reject":
                ScraperFlagProcessor.reject_flag(
                    db=db,
                    flag_id=flag_id,
                    admin_id=admin_id,
                    notes=request.admin_notes or "",
                )
            elif request.action == "dismiss":
                ScraperFlagProcessor.dismiss_flag(
                    db=db,
                    flag_id=flag_id,
                    admin_id=admin_id,
                    notes=request.admin_notes or "",
                )
            success_count += 1
        except Exception as e:
            failed_count += 1
            errors.append({
                "flag_id": flag_id,
                "error": str(e)
            })
            logger.error(f"Bulk action failed for flag {flag_id}: {str(e)}")

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total_requested": len(request.flag_ids),
        "errors": errors
    }


# === Flag Analytics Endpoint ===

@router.get("/flags/analytics")
async def get_flag_analytics(
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
):
    """
    Get per-dispensary analytics on flag resolution patterns.

    Helps identify which scrapers produce bad data by showing
    dismiss rates, correction rates, and common correction patterns.
    """
    since = datetime.utcnow() - timedelta(days=days)

    # Get all resolved flags in the time range
    flags = (
        db.query(ScraperFlag)
        .filter(
            ScraperFlag.status.in_(["approved", "rejected", "dismissed"]),
            ScraperFlag.resolved_at >= since,
        )
        .all()
    )

    # Group by dispensary
    by_dispensary = {}
    for flag in flags:
        disp_id = flag.dispensary_id
        if disp_id not in by_dispensary:
            dispensary = db.query(Dispensary).filter(
                Dispensary.id == disp_id
            ).first()
            by_dispensary[disp_id] = {
                "dispensary_id": disp_id,
                "dispensary_name": dispensary.name if dispensary else "Unknown",
                "total_flags": 0,
                "approved": 0,
                "rejected": 0,
                "dismissed": 0,
                "corrected": 0,
                "correction_details": {},
            }

        entry = by_dispensary[disp_id]
        entry["total_flags"] += 1
        entry[flag.status] = entry.get(flag.status, 0) + 1

        # Aggregate corrections
        if flag.corrections:
            entry["corrected"] += 1
            for field_name, change in flag.corrections.items():
                if field_name not in entry["correction_details"]:
                    entry["correction_details"][field_name] = {
                        "count": 0,
                        "patterns": {},
                    }
                detail = entry["correction_details"][field_name]
                detail["count"] += 1
                # Track from→to patterns
                pattern_key = f"{change.get('from', '')} -> {change.get('to', '')}"
                detail["patterns"][pattern_key] = detail["patterns"].get(pattern_key, 0) + 1

    # Format response
    result = []
    for disp_id, entry in by_dispensary.items():
        total = entry["total_flags"]
        correction_rate = entry["corrected"] / total if total > 0 else 0

        # Find top corrections
        top_corrections = []
        for field_name, detail in entry["correction_details"].items():
            # Find most common pattern for this field
            common_pattern = None
            if detail["patterns"]:
                most_common = max(detail["patterns"], key=detail["patterns"].get)
                parts = most_common.split(" -> ", 1)
                common_pattern = {
                    "from": parts[0] if parts[0] else None,
                    "to": parts[1] if len(parts) > 1 else None,
                }
            top_corrections.append({
                "field": field_name,
                "count": detail["count"],
                "common_pattern": common_pattern,
            })

        top_corrections.sort(key=lambda x: x["count"], reverse=True)

        result.append({
            "dispensary_id": entry["dispensary_id"],
            "dispensary_name": entry["dispensary_name"],
            "total_flags": total,
            "approved": entry["approved"],
            "rejected": entry["rejected"],
            "dismissed": entry["dismissed"],
            "correction_rate": round(correction_rate, 3),
            "top_corrections": top_corrections[:5],
        })

    result.sort(key=lambda x: x["total_flags"], reverse=True)
    return {"days": days, "by_dispensary": result}


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
        "prices_moved": price_count,
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
        normalization_confidence=1.0,
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
    total_products = db.query(Product).filter(Product.is_master.is_(True)).count()
    total_prices = db.query(Price).count()
    outliers = OutlierDetector.get_all_outliers(db, limit=100)
    high_severity = len([o for o in outliers if o["severity"] == "high"])

    return {
        "flags": {"pending": pending_flags},
        "products": {"total_master": total_products, "total_prices": total_prices},
        "quality": {"outliers_total": len(outliers), "outliers_high_severity": high_severity},
    }
