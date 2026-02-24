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
import re

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers for potential-duplicate scoring
# ---------------------------------------------------------------------------

_WEIGHT_SUFFIX_RE = re.compile(r'\s+[–\-]\s+\d')


def _base_name(name: str) -> str:
    """Strip weight/type suffix for pairwise duplicate scoring only.

    Examples:
        'Cheese – 1 gr Vape Cartridge'       → 'Cheese'
        'Blue Dream – 3.5 g Indoor Flower'   → 'Blue Dream'
        'Wedding Cake – 7 g Tops Indoor'     → 'Wedding Cake'

    If no suffix is found the original name is returned unchanged.  The full
    name is still used for display — this is only for computing similarity.
    """
    m = _WEIGHT_SUFFIX_RE.search(name)
    return name[: m.start()].strip() if m else name

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
    # Overrides for the matched (existing) product — lets admin clean both sides
    matched_product_name: Optional[str] = None
    matched_product_brand: Optional[str] = None


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


class MergeDuplicateRequest(BaseModel):
    """Request body for resolving a same-dispensary duplicate via flag."""
    kept_product_id: str
    notes: Optional[str] = ""


class MergeRequest(BaseModel):
    source_product_id: str
    target_product_id: str


class SplitRequest(BaseModel):
    product_name: str
    brand_id: str
    product_type: Optional[str] = "Unknown"


class CleanAndActivateRequest(BaseModel):
    """Request body for cleaning and activating a flagged product."""
    notes: Optional[str] = ""
    name: Optional[str] = None
    brand_name: Optional[str] = None
    product_type: Optional[str] = None
    thc_percentage: Optional[float] = None
    cbd_percentage: Optional[float] = None
    weight: Optional[str] = None
    price: Optional[float] = None
    issue_tags: Optional[List[str]] = None


class DeleteFlaggedProductRequest(BaseModel):
    """Request body for deleting a garbage product linked to a flag."""
    notes: Optional[str] = ""


class FlagStatsResponse(BaseModel):
    pending: int
    pending_cleanup: int = 0
    pending_review: int = 0
    auto_merged: int = 0
    approved: int
    rejected: int
    dismissed: int
    cleaned: int = 0
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
    include_auto_merged: bool = Query(False),  # When True, also returns auto_merged flags
    flag_type: Optional[str] = Query(None, pattern="^(match_review|data_cleanup)$"),
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
    if include_auto_merged:
        query = db.query(ScraperFlag).filter(
            ScraperFlag.status.in_(["pending", "auto_merged"])
        )
    else:
        query = db.query(ScraperFlag).filter(ScraperFlag.status == "pending")

    if dispensary_id:
        query = query.filter(ScraperFlag.dispensary_id == dispensary_id)

    if flag_type:
        query = query.filter(ScraperFlag.flag_type == flag_type)

    if min_confidence is not None:
        query = query.filter(ScraperFlag.confidence_score >= min_confidence)
    if max_confidence is not None:
        query = query.filter(ScraperFlag.confidence_score <= max_confidence)

    # Apply DB-level sort when no Python-level filtering is needed
    if sort_by == "confidence":
        from sqlalchemy import asc, desc as sa_desc
        order_fn = sa_desc if sort_order == "desc" else asc
        query = query.order_by(order_fn(ScraperFlag.confidence_score))
    else:
        from sqlalchemy import asc, desc as sa_desc
        order_fn = sa_desc if sort_order == "desc" else asc
        query = query.order_by(order_fn(ScraperFlag.created_at))

    # When no Python-level filters are active, paginate at DB level (fast path)
    use_db_pagination = not match_type and not data_quality
    if use_db_pagination:
        all_flags = query.offset(skip).limit(limit).all()
    else:
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
            "original_thc_content": flag.original_thc_content,
            "original_cbd_content": flag.original_cbd_content,
            "original_weight": flag.original_weight,
            "original_price": flag.original_price,
            "original_category": flag.original_category,
            "original_url": flag.original_url,
            "brand_name": flag.brand_name,
            "dispensary_id": flag.dispensary_id,
            "dispensary_name": dispensary.name if dispensary else None,
            "confidence_score": flag.confidence_score,
            "confidence_percent": f"{flag.confidence_score:.0%}",
            "matched_product_id": flag.matched_product_id,  # Needed for frontend approve button
            "matched_product": matched_product,
            "merge_reason": flag.merge_reason,
            "status": flag.status,
            "flag_type": flag.flag_type,
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

    # Apply pagination in Python (only needed when Python-level filters were active)
    if use_db_pagination:
        paginated_results = flag_data  # Already paginated at DB level
    else:
        paginated_results = flag_data[skip:skip + limit]

    # Remove internal fields
    for item in paginated_results:
        item.pop("_created_at_dt", None)

    return paginated_results


@router.get("/flags/stats", response_model=FlagStatsResponse)
async def get_flag_stats(db: Session = Depends(get_db)):
    """Get statistics on ScraperFlags."""
    pending = db.query(ScraperFlag).filter(ScraperFlag.status == "pending").count()
    pending_cleanup = db.query(ScraperFlag).filter(
        ScraperFlag.status == "pending",
        ScraperFlag.flag_type == "data_cleanup"
    ).count()
    pending_review = db.query(ScraperFlag).filter(
        ScraperFlag.status == "pending",
        ScraperFlag.flag_type == "match_review"
    ).count()
    auto_merged = db.query(ScraperFlag).filter(ScraperFlag.status == "auto_merged").count()
    approved = db.query(ScraperFlag).filter(ScraperFlag.status == "approved").count()
    rejected = db.query(ScraperFlag).filter(ScraperFlag.status == "rejected").count()
    dismissed = db.query(ScraperFlag).filter(ScraperFlag.status == "dismissed").count()
    cleaned = db.query(ScraperFlag).filter(ScraperFlag.status == "cleaned").count()

    return {
        "pending": pending,
        "pending_cleanup": pending_cleanup,
        "pending_review": pending_review,
        "auto_merged": auto_merged,
        "approved": approved,
        "rejected": rejected,
        "dismissed": dismissed,
        "cleaned": cleaned,
        "total": pending + auto_merged + approved + rejected + dismissed + cleaned,
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
            matched_product_name=request.matched_product_name,
            matched_product_brand=request.matched_product_brand,
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


@router.post("/flags/clean/{flag_id}")
async def clean_and_activate_flag(
    flag_id: str,
    request: CleanAndActivateRequest = Body(default=CleanAndActivateRequest()),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Clean up a data_cleanup flag: apply edits and activate the product."""
    try:
        product_id = ScraperFlagProcessor.clean_and_activate(
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
        return {"status": "cleaned", "product_id": product_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/flags/delete-product/{flag_id}")
async def delete_flagged_product(
    flag_id: str,
    request: DeleteFlaggedProductRequest = Body(default=DeleteFlaggedProductRequest()),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """Delete the product linked to a data_cleanup flag (garbage data)."""
    try:
        ScraperFlagProcessor.delete_flagged_product(
            db=db,
            flag_id=flag_id,
            admin_id=admin_id,
            notes=request.notes or "",
        )
        return {"status": "deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/flags/merge-duplicate/{flag_id}")
async def merge_duplicate_flag(
    flag_id: str,
    request: MergeDuplicateRequest = Body(default=MergeDuplicateRequest(kept_product_id="")),
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """
    Resolve a same-dispensary duplicate flag by merging the loser into the winner.

    Moves all Price, Review, and Watchlist records from the loser product to the
    kept_product_id (winner), then soft-deletes the loser.
    """
    try:
        result = ScraperFlagProcessor.merge_duplicate_flag(
            db=db,
            flag_id=flag_id,
            kept_product_id=request.kept_product_id,
            admin_id=admin_id,
            notes=request.notes or "",
        )
        return {"status": "merged", **result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class RejectAutoMergeRequest(BaseModel):
    """Request body for rejecting an auto-merged flag (marking it as a bad merge)."""
    notes: Optional[str] = ""


class BulkActionRequest(BaseModel):
    """Request body for bulk flag actions."""
    flag_ids: List[str]
    action: str  # "approve", "reject", "dismiss", "clean", "delete_product", or "reject_auto_merge"
    admin_notes: Optional[str] = ""


@router.post("/flags/reject-auto-merge/{flag_id}")
async def reject_auto_merge(
    flag_id: str,
    request: RejectAutoMergeRequest,
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin)
):
    """
    Mark an auto-merged flag as rejected (bad merge decision).

    This is a non-destructive operation — it marks the audit flag as rejected
    without touching price or product records (the price update may have been
    legitimate). Use this to record disagreement with an auto-merge for
    analytics and future training purposes.
    """
    flag = db.query(ScraperFlag).filter(
        ScraperFlag.id == flag_id,
        ScraperFlag.status == "auto_merged"
    ).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Auto-merged flag not found or already resolved")

    flag.status = "rejected"
    flag.admin_notes = request.notes or ""
    flag.resolved_at = datetime.utcnow()
    db.commit()
    return {"status": "rejected", "flag_id": flag_id}


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
    if request.action not in ["approve", "reject", "dismiss", "clean", "delete_product", "reject_auto_merge"]:
        raise HTTPException(
            status_code=400,
            detail="Action must be 'approve', 'reject', 'dismiss', 'clean', 'delete_product', or 'reject_auto_merge'"
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
            elif request.action == "clean":
                ScraperFlagProcessor.clean_and_activate(
                    db=db,
                    flag_id=flag_id,
                    admin_id=admin_id,
                    notes=request.admin_notes or "",
                )
            elif request.action == "delete_product":
                ScraperFlagProcessor.delete_flagged_product(
                    db=db,
                    flag_id=flag_id,
                    admin_id=admin_id,
                    notes=request.admin_notes or "",
                )
            elif request.action == "reject_auto_merge":
                flag = db.query(ScraperFlag).filter(
                    ScraperFlag.id == flag_id,
                    ScraperFlag.status == "auto_merged"
                ).first()
                if flag:
                    flag.status = "rejected"
                    flag.admin_notes = request.admin_notes or ""
                    flag.resolved_at = datetime.utcnow()
                    db.flush()
                else:
                    raise ValueError(f"Flag {flag_id} is not an auto_merged flag")
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

    # Re-parent source's child variants to target so they remain reachable
    # under the surviving master product. Without this, after demoting source
    # the variants become orphaned (master_product_id points to a non-master).
    variant_count = (
        db.query(Product)
        .filter(
            Product.master_product_id == request.source_product_id,
            Product.is_master.is_(False),
        )
        .update({Product.master_product_id: request.target_product_id})
    )

    # Move any prices directly on source to target (prices should be on variants,
    # but this is a safety net in case of legacy data).
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
        "variants_reparented": variant_count,
        "prices_moved": price_count,
    }


@router.post("/products/repair-orphaned-variants")
async def repair_orphaned_variants(
    db: Session = Depends(get_db),
    admin_id: str = Depends(verify_admin),
):
    """
    One-time repair for variants orphaned by pre-fix merges.

    Before the variant re-parenting fix was added to merge_products, merging
    product A into product B would demote A to a non-master without updating A's
    child variants — leaving those variants with master_product_id pointing to the
    now-non-master A.  The cross_dispensary_products query only follows chains that
    end at is_master=True, so those variants (and their prices) became invisible.

    This endpoint finds every such orphaned variant, walks the chain upward to the
    true root master, and re-sets master_product_id accordingly.
    Returns {"repaired": N} where N is the number of variants fixed.
    """
    from sqlalchemy.orm import aliased as sa_aliased

    ParentAlias = sa_aliased(Product)

    # Load all orphans: variants whose immediate parent is also a non-master
    orphans = (
        db.query(Product)
        .join(ParentAlias, ParentAlias.id == Product.master_product_id)
        .filter(
            Product.is_master.is_(False),
            ParentAlias.is_master.is_(False),
        )
        .all()
    )

    repaired = 0
    for orphan in orphans:
        # Walk the parent chain until we reach a true master
        current_id = orphan.master_product_id
        seen = {orphan.id}  # guard against cycles
        while current_id and current_id not in seen:
            current = db.query(Product).filter(Product.id == current_id).first()
            if not current:
                break
            if current.is_master:
                orphan.master_product_id = current.id
                repaired += 1
                break
            seen.add(current_id)
            current_id = current.master_product_id

    db.commit()
    logger.info(f"repair_orphaned_variants: fixed {repaired} orphaned variants")
    return {"repaired": repaired}


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


@router.get("/products/cross-dispensary")
async def get_cross_dispensary_products(
    db: Session = Depends(get_db),
    min_dispensaries: int = Query(2, ge=2, le=10),
    limit: int = Query(200, ge=1, le=500),
):
    """
    Get all active parent products that have prices at multiple dispensaries.

    Returns products sorted by dispensary count descending, useful for auditing
    what the ConfidenceScorer has auto-merged across dispensaries.

    Uses ORM-based queries to stay compatible with both SQLite (dev) and
    PostgreSQL (production).
    """
    from sqlalchemy import distinct as sa_distinct
    from sqlalchemy.orm import aliased
    from collections import defaultdict

    Variant = aliased(Product)

    # Query 1: parent products with >=N distinct dispensaries
    rows = (
        db.query(
            Product.id,
            Product.name,
            Product.product_type,
            Brand.name.label("brand_name"),
            func.count(sa_distinct(Price.dispensary_id)).label("disp_count"),
            func.count(sa_distinct(Variant.id)).label("variant_count"),
        )
        .outerjoin(Brand, Brand.id == Product.brand_id)
        .join(Variant, Variant.master_product_id == Product.id)
        .join(Price, Price.product_id == Variant.id)
        .filter(
            Product.is_master.is_(True),
            Product.is_active.is_(True),
            Variant.is_master.is_(False),
        )
        .group_by(Product.id, Product.name, Product.product_type, Brand.name)
        .having(func.count(sa_distinct(Price.dispensary_id)) >= min_dispensaries)
        .order_by(func.count(sa_distinct(Price.dispensary_id)).desc(), Product.name)
        .limit(limit)
        .all()
    )

    parent_ids = [r.id for r in rows]

    # Query 2: dispensary names for these parents (separate query avoids array_agg)
    disp_map: dict = defaultdict(list)
    if parent_ids:
        VariantD = aliased(Product)
        disp_rows = (
            db.query(VariantD.master_product_id, Dispensary.name)
            .join(Price, Price.product_id == VariantD.id)
            .join(Dispensary, Dispensary.id == Price.dispensary_id)
            .filter(
                VariantD.master_product_id.in_(parent_ids),
                VariantD.is_master.is_(False),
            )
            .distinct()
            .order_by(VariantD.master_product_id, Dispensary.name)
            .all()
        )
        for parent_id, disp_name in disp_rows:
            disp_map[parent_id].append(disp_name)

    products = [
        {
            "id": r.id,
            "name": r.name,
            "product_type": r.product_type,
            "brand": r.brand_name,
            "dispensary_count": r.disp_count,
            "variant_count": r.variant_count,
            "dispensaries": disp_map.get(r.id, []),
        }
        for r in rows
    ]

    return {"products": products, "total": len(products)}


@router.get("/products/dispensary-coverage")
async def get_dispensary_coverage(db: Session = Depends(get_db)):
    """
    Summary of how many active parent products are covered by how many dispensaries.

    Returns counts for: 0 dispensaries (orphans), 1, 2, 3, 4+ dispensaries.
    Useful for understanding how much cross-dispensary linking has occurred.
    """
    from sqlalchemy import text

    row = db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE disp_count = 0) AS orphans,
            COUNT(*) FILTER (WHERE disp_count = 1) AS single_dispensary,
            COUNT(*) FILTER (WHERE disp_count = 2) AS two_dispensaries,
            COUNT(*) FILTER (WHERE disp_count = 3) AS three_dispensaries,
            COUNT(*) FILTER (WHERE disp_count >= 4) AS four_plus_dispensaries,
            COUNT(*) AS total_active
        FROM (
            SELECT
                p.id,
                COUNT(DISTINCT pr.dispensary_id) AS disp_count
            FROM products p
            LEFT JOIN products v ON v.master_product_id = p.id AND v.is_master = false
            LEFT JOIN prices pr ON pr.product_id = v.id
            WHERE p.is_master = true AND p.is_active = true
            GROUP BY p.id
        ) sub
    """)).fetchone()

    return {
        "total_active": row.total_active,
        "orphans": row.orphans,
        "single_dispensary": row.single_dispensary,
        "two_dispensaries": row.two_dispensaries,
        "three_dispensaries": row.three_dispensaries,
        "four_plus_dispensaries": row.four_plus_dispensaries,
        "multi_dispensary": row.two_dispensaries + row.three_dispensaries + row.four_plus_dispensaries,
    }


@router.get("/products/potential-duplicates")
async def get_potential_duplicates(
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
):
    """
    Surface potential duplicate products by running pairwise fuzzy matching
    across all active master products within the same product_type.

    Only includes pairs where the two products are carried by at least one
    DIFFERENT dispensary — same-dispensary near-misses (e.g. two similarly
    named WholesomeCo vaporizers) are skipped as the admin doesn't need to
    review them.

    Returns pairs with 65–84% confidence sorted by confidence descending.
    Caps at `limit` pairs. This is O(n²) — ~5–15 seconds for 1,344 products.
    Only call on demand.
    """
    from collections import defaultdict
    from sqlalchemy.orm import aliased
    from services.normalization.matcher import ProductMatcher

    # Load all active master products with brands
    masters = (
        db.query(Product)
        .outerjoin(Brand, Brand.id == Product.brand_id)
        .filter(Product.is_master.is_(True), Product.is_active.is_(True))
        .all()
    )

    master_ids = [m.id for m in masters]

    # Build dispensary ID map upfront for ALL master products.
    # This lets us skip same-dispensary pairs during the pairwise loop
    # without an extra per-pair DB hit.
    VariantD = aliased(Product)
    all_disp_rows = (
        db.query(VariantD.master_product_id, Price.dispensary_id, Price.product_url)
        .join(Price, Price.product_id == VariantD.id)
        .filter(
            VariantD.master_product_id.in_(master_ids),
            VariantD.is_master.is_(False),
        )
        .all()
    )
    product_disp_ids: dict = defaultdict(set)
    # (master_product_id, dispensary_id) → first non-null product_url found
    product_disp_urls: dict = {}
    for pid, did, url in all_disp_rows:
        product_disp_ids[pid].add(did)
        if url and (pid, did) not in product_disp_urls:
            product_disp_urls[(pid, did)] = url

    # Also build a name map for display (dispensary_id → dispensary name)
    disp_name_map: dict = {}
    disp_name_rows = db.query(Dispensary.id, Dispensary.name).all()
    for did, dname in disp_name_rows:
        disp_name_map[did] = dname

    candidates = [
        {
            "id": m.id,
            "name": m.name,
            # base_name strips the weight/type format suffix (e.g. "– 1 gr Vape Cartridge")
            # so that fuzzy scoring compares only the meaningful strain/product name.
            # Full name is preserved for display; base_name is only used in score_match.
            "base_name": _base_name(m.name),
            "brand": m.brand.name if m.brand else "",
            "product_type": (m.product_type or "").lower(),
            "thc_percentage": m.thc_percentage,
            "disp_ids": product_disp_ids.get(m.id, set()),
        }
        for m in masters
    ]

    # Group candidates by product_type to minimize O(n²) comparisons
    type_groups: dict = defaultdict(list)
    for c in candidates:
        pt = c["product_type"]
        if pt and pt not in ("other", "unknown"):
            type_groups[pt].append(c)

    # Run pairwise comparison within each type group
    pairs = []
    for group in type_groups.values():
        n = len(group)
        for i in range(n):
            for j in range(i + 1, n):
                a = group[i]
                b = group[j]

                # Skip pairs from the same set of dispensaries — those are
                # same-chain near-misses the admin doesn't need to review.
                if a["disp_ids"] == b["disp_ids"]:
                    continue

                score, _ = ProductMatcher.score_match(
                    # Use base_name (suffix-stripped) so that shared weight/type
                    # strings like "– 1 gr Vape Cartridge" don't inflate the score.
                    scraped_name=a["base_name"],
                    master_name=b["base_name"],
                    scraped_brand=a["brand"],
                    master_brand=b["brand"],
                    scraped_thc=a["thc_percentage"],
                    master_thc=b["thc_percentage"],
                )
                if ProductMatcher.REVIEW_THRESHOLD <= score < ProductMatcher.AUTO_MERGE_THRESHOLD:
                    pairs.append({
                        "product_a_id": a["id"],
                        "product_a_name": a["name"],
                        "product_a_brand": a["brand"],
                        "product_a_dispensaries": sorted(
                            disp_name_map.get(did, did) for did in a["disp_ids"]
                        ),
                        "product_a_dispensary_urls": {
                            disp_name_map.get(did, str(did)): product_disp_urls[(a["id"], did)]
                            for did in a["disp_ids"]
                            if (a["id"], did) in product_disp_urls
                        },
                        "product_b_id": b["id"],
                        "product_b_name": b["name"],
                        "product_b_brand": b["brand"],
                        "product_b_dispensaries": sorted(
                            disp_name_map.get(did, did) for did in b["disp_ids"]
                        ),
                        "product_b_dispensary_urls": {
                            disp_name_map.get(did, str(did)): product_disp_urls[(b["id"], did)]
                            for did in b["disp_ids"]
                            if (b["id"], did) in product_disp_urls
                        },
                        "product_type": a["product_type"],
                        "confidence": round(score, 3),
                    })

    # Sort by confidence descending
    pairs.sort(key=lambda x: x["confidence"], reverse=True)

    # Deduplicate pairs with the same product names.
    # The 3 Curaleaf locations each create a separate master product for the same
    # item, so without this we'd get N_curaleaf × N_wholesomeco duplicate rows.
    # Keep only the highest-confidence pair (first after sort) per name-set.
    seen_name_pairs: set = set()
    deduped: list = []
    for pair in pairs:
        name_key = frozenset({
            pair["product_a_name"].lower().strip(),
            pair["product_b_name"].lower().strip(),
        })
        if name_key not in seen_name_pairs:
            seen_name_pairs.add(name_key)
            deduped.append(pair)
    pairs = deduped

    return {"pairs": pairs[:limit], "total": len(pairs)}


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
