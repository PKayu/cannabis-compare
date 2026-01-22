"""
User profile and review history endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import User, Review, Product, Dispensary, Brand
from routers.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


# Response Models
class ReviewResponse(BaseModel):
    """Review response model for user review history"""
    id: str
    product_id: str
    product_name: str
    rating: int
    effects_rating: int
    taste_rating: int
    value_rating: int
    comment: str
    upvotes: int
    created_at: str

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """User profile response model"""
    id: str
    email: str
    username: str
    created_at: str
    review_count: int

    class Config:
        from_attributes = True


class UserProfileUpdateRequest(BaseModel):
    """User profile update request"""
    username: str | None = None


# Endpoints
@router.get("/me", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get current authenticated user's profile

    Includes user information and review count

    Args:
        current_user: Current authenticated user from JWT token
        db: Database session

    Returns:
        User profile with statistics
    """
    review_count = db.query(Review).filter(Review.user_id == current_user.id).count()

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat(),
        "review_count": review_count,
    }


@router.patch("/me", response_model=UserProfileResponse)
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Update current user's profile

    Currently supports username updates. Can be extended for other profile fields.

    Args:
        request: Profile update request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: If username already exists
    """
    if request.username:
        # Check if username is already taken
        existing = db.query(User).filter(
            User.username == request.username,
            User.id != current_user.id,
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        current_user.username = request.username

    db.commit()
    db.refresh(current_user)

    review_count = db.query(Review).filter(Review.user_id == current_user.id).count()

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "username": current_user.username,
        "created_at": current_user.created_at.isoformat(),
        "review_count": review_count,
    }


@router.get("/me/reviews", response_model=list[ReviewResponse])
async def get_user_reviews(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    skip: int = 0,
) -> list:
    """
    Get user's review history

    Returns user's submitted reviews in reverse chronological order
    (most recent first)

    Args:
        current_user: Current authenticated user
        db: Database session
        limit: Maximum number of reviews to return (default 50)
        skip: Number of reviews to skip (for pagination)

    Returns:
        List of user's reviews with product details
    """
    reviews = (
        db.query(Review)
        .join(Product, Review.product_id == Product.id)
        .filter(Review.user_id == current_user.id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for review in reviews:
        result.append({
            "id": str(review.id),
            "product_id": str(review.product_id),
            "product_name": review.product.name,
            "rating": review.rating,
            "effects_rating": review.effects_rating,
            "taste_rating": review.taste_rating,
            "value_rating": review.value_rating,
            "comment": review.comment,
            "upvotes": review.upvotes,
            "created_at": review.created_at.isoformat(),
        })

    return result


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_public_user_profile(
    user_id: str,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get public user profile information

    For displaying user info on reviews, but with limited details

    Args:
        user_id: The user's ID
        db: Database session

    Returns:
        Public user profile information

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    review_count = db.query(Review).filter(Review.user_id == user_id).count()

    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "created_at": user.created_at.isoformat(),
        "review_count": review_count,
    }


@router.get("/{user_id}/reviews", response_model=list[ReviewResponse])
async def get_public_user_reviews(
    user_id: str,
    db: Session = Depends(get_db),
    limit: int = 50,
    skip: int = 0,
) -> list:
    """
    Get public review history for a user

    Returns user's submitted reviews in reverse chronological order

    Args:
        user_id: The user's ID
        db: Database session
        limit: Maximum number of reviews to return
        skip: Number of reviews to skip

    Returns:
        List of user's public reviews

    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    reviews = (
        db.query(Review)
        .join(Product, Review.product_id == Product.id)
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for review in reviews:
        result.append({
            "id": str(review.id),
            "product_id": str(review.product_id),
            "product_name": review.product.name,
            "rating": review.rating,
            "effects_rating": review.effects_rating,
            "taste_rating": review.taste_rating,
            "value_rating": review.value_rating,
            "comment": review.comment,
            "upvotes": review.upvotes,
            "created_at": review.created_at.isoformat(),
        })

    return result
