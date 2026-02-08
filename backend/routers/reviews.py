"""
Review endpoints for submitting, viewing, and managing product reviews
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from database import get_db
from models import Review, Product, User
from model_enums.enums import validate_intention, ALL_INTENTIONS
from routers.auth import get_current_user

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


# Request/Response Models
class ReviewCreate(BaseModel):
    """Request model for creating a review"""
    product_id: str
    effects_rating: int = Field(..., ge=1, le=5, description="Effects rating 1-5")
    taste_rating: int = Field(..., ge=1, le=5, description="Taste rating 1-5")
    value_rating: int = Field(..., ge=1, le=5, description="Value rating 1-5")
    intention_type: str = Field(..., description="Either 'medical' or 'mood'")
    intention_tag: str = Field(..., description="Specific intention like 'pain' or 'socializing'")
    batch_number: Optional[str] = None
    cultivation_date: Optional[str] = None  # ISO date string
    comment: Optional[str] = Field(None, max_length=1000)

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod-001",
                "effects_rating": 5,
                "taste_rating": 4,
                "value_rating": 4,
                "intention_type": "medical",
                "intention_tag": "pain",
                "batch_number": "BATCH-2024-001",
                "cultivation_date": "2024-01-15",
                "comment": "Really helped with my chronic pain. Great taste too!"
            }
        }


class ReviewUpdate(BaseModel):
    """Request model for updating a review"""
    effects_rating: Optional[int] = Field(None, ge=1, le=5)
    taste_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    intention_type: Optional[str] = None
    intention_tag: Optional[str] = None
    batch_number: Optional[str] = None
    cultivation_date: Optional[str] = None
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    """Response model for review data"""
    id: str
    rating: int
    effects_rating: Optional[int]
    taste_rating: Optional[int]
    value_rating: Optional[int]
    intention_type: Optional[str]
    intention_tag: Optional[str]
    batch_number: Optional[str]
    cultivation_date: Optional[datetime]
    comment: Optional[str]
    upvotes: int
    user_id: str
    username: str
    product_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Helper functions
def compute_overall_rating(effects: int, taste: int, value: int) -> int:
    """Compute overall rating from component ratings"""
    return round((effects + taste + value) / 3)


# Endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Submit a new product review

    Requires authentication. Users can only have one review per product.

    Args:
        review_data: Review details including ratings, intention tags, and comment
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Review ID and success message
    """
    # Validate product exists
    product = db.query(Product).filter(Product.id == review_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Resolve variant to parent - reviews always attach to parent product
    if not product.is_master and product.master_product_id:
        parent = db.query(Product).filter(Product.id == product.master_product_id).first()
        if parent:
            product = parent
            review_data.product_id = product.id

    # Check if user already reviewed this product
    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.product_id == review_data.product_id
    ).first()

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product. Use PUT to update your review."
        )

    # Validate intention tags
    if not validate_intention(review_data.intention_type, review_data.intention_tag):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid intention. Valid options for '{review_data.intention_type}': {ALL_INTENTIONS.get(review_data.intention_type, [])}"
        )

    # Compute overall rating
    overall_rating = compute_overall_rating(
        review_data.effects_rating,
        review_data.taste_rating,
        review_data.value_rating
    )

    # Parse cultivation date if provided
    cultivation_date_parsed = None
    if review_data.cultivation_date:
        try:
            cultivation_date_parsed = datetime.fromisoformat(review_data.cultivation_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cultivation date format. Use ISO format (YYYY-MM-DD)"
            )

    # Create review
    review = Review(
        user_id=current_user.id,
        product_id=review_data.product_id,
        rating=overall_rating,
        effects_rating=review_data.effects_rating,
        taste_rating=review_data.taste_rating,
        value_rating=review_data.value_rating,
        intention_type=review_data.intention_type,
        intention_tag=review_data.intention_tag,
        batch_number=review_data.batch_number,
        cultivation_date=cultivation_date_parsed,
        comment=review_data.comment
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return {
        "id": review.id,
        "status": "created",
        "message": "Review submitted successfully"
    }


@router.get("/product/{product_id}")
async def get_product_reviews(
    product_id: str,
    intention_type: Optional[str] = None,
    intention_tag: Optional[str] = None,
    sort_by: str = "recent",
    db: Session = Depends(get_db)
) -> list[ReviewResponse]:
    """
    Get reviews for a specific product

    Args:
        product_id: Product ID
        intention_type: Filter by intention type ("medical" or "mood")
        intention_tag: Filter by specific intention tag
        sort_by: Sort order - "recent", "helpful" (upvotes), or "rating_high"
        db: Database session

    Returns:
        List of reviews with user information
    """
    # Resolve variant to parent for review lookup
    product = db.query(Product).filter(Product.id == product_id).first()
    if product and not product.is_master and product.master_product_id:
        product_id = product.master_product_id

    # Build base query
    query = db.query(Review).filter(Review.product_id == product_id)

    # Apply filters
    if intention_type:
        query = query.filter(Review.intention_type == intention_type)

    if intention_tag:
        query = query.filter(Review.intention_tag == intention_tag)

    # Apply sorting
    if sort_by == "recent":
        query = query.order_by(desc(Review.created_at))
    elif sort_by == "helpful":
        query = query.order_by(desc(Review.upvotes), desc(Review.created_at))
    elif sort_by == "rating_high":
        query = query.order_by(desc(Review.rating), desc(Review.created_at))
    else:
        # Default to recent
        query = query.order_by(desc(Review.created_at))

    reviews = query.all()

    # Format response with user information
    return [
        ReviewResponse(
            id=r.id,
            rating=r.rating,
            effects_rating=r.effects_rating,
            taste_rating=r.taste_rating,
            value_rating=r.value_rating,
            intention_type=r.intention_type,
            intention_tag=r.intention_tag,
            batch_number=r.batch_number,
            cultivation_date=r.cultivation_date,
            comment=r.comment,
            upvotes=r.upvotes,
            user_id=r.user_id,
            username=r.user.username if r.user else "Unknown",
            product_id=r.product_id,
            created_at=r.created_at,
            updated_at=r.updated_at
        )
        for r in reviews
    ]


@router.put("/{review_id}")
async def update_review(
    review_id: str,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Update an existing review

    Only the review author can update their review.

    Args:
        review_id: Review ID
        review_data: Fields to update
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Success message
    """
    # Find review
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # Check ownership
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own reviews"
        )

    # Update fields if provided
    update_data = review_data.dict(exclude_unset=True)

    # Validate intention if being updated
    if "intention_type" in update_data or "intention_tag" in update_data:
        intention_type = update_data.get("intention_type", review.intention_type)
        intention_tag = update_data.get("intention_tag", review.intention_tag)

        if not validate_intention(intention_type, intention_tag):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid intention combination"
            )

    # Parse cultivation date if provided
    if "cultivation_date" in update_data and update_data["cultivation_date"]:
        try:
            update_data["cultivation_date"] = datetime.fromisoformat(update_data["cultivation_date"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cultivation date format. Use ISO format (YYYY-MM-DD)"
            )

    # Update review fields
    for field, value in update_data.items():
        setattr(review, field, value)

    # Recalculate overall rating if any component rating changed
    if any(field in update_data for field in ["effects_rating", "taste_rating", "value_rating"]):
        review.rating = compute_overall_rating(
            review.effects_rating,
            review.taste_rating,
            review.value_rating
        )

    review.updated_at = datetime.utcnow()
    db.commit()

    return {
        "id": review.id,
        "status": "updated",
        "message": "Review updated successfully"
    }


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a review

    Only the review author can delete their review.

    Args:
        review_id: Review ID
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        No content (204)
    """
    # Find review
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # Check ownership (or admin - future enhancement)
    if review.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews"
        )

    db.delete(review)
    db.commit()

    return None


@router.post("/{review_id}/upvote")
async def upvote_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Upvote a helpful review

    Requires authentication. Currently allows multiple upvotes from same user.
    Future enhancement: Track who upvoted to prevent duplicates.

    Args:
        review_id: Review ID
        current_user: Authenticated user from JWT token
        db: Database session

    Returns:
        Updated upvote count
    """
    # Find review
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    # Increment upvotes
    review.upvotes += 1
    db.commit()
    db.refresh(review)

    return {
        "review_id": review.id,
        "upvotes": review.upvotes,
        "message": "Review upvoted successfully"
    }
