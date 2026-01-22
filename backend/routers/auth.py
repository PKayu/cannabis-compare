"""
Authentication endpoints using Supabase and JWT tokens
"""
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from database import get_db
from models import User
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    extract_token_from_header,
    TokenResponse,
)
from services.supabase_client import SupabaseClient
from config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


# Request/Response Models
class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str
    username: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
                "username": "john_doe",
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }


class TokenVerifyRequest(BaseModel):
    """Token verification request"""
    token: str


class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    username: str
    created_at: str

    class Config:
        from_attributes = True


# Dependency to get current user from JWT token
async def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and verify JWT token from Authorization header

    Args:
        authorization: Authorization header value
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is missing, invalid, or user not found
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# Endpoints
@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Register a new user

    Creates a new user in both Supabase Auth and local database.
    Returns a JWT token for immediate login.

    Args:
        request: Registration request with email, password, username
        db: Database session

    Returns:
        TokenResponse with access_token and user info

    Raises:
        HTTPException: If email already exists or registration fails
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user in Supabase Auth
    supabase_user = SupabaseClient.create_user(request.email, request.password)
    if not supabase_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user. Email may already be in use.",
        )

    # Create user in local database
    db_user = User(
        id=supabase_user["id"],
        email=request.email,
        username=request.username,
        hashed_password=hash_password(request.password),
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        # Clean up Supabase user if DB save fails
        SupabaseClient.delete_user(supabase_user["id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save user profile",
        )

    # Generate JWT token
    access_token = create_access_token(
        user_id=db_user.id,
        email=db_user.email,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(db_user.id),
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
) -> dict:
    """
    Authenticate user with email and password

    Verifies credentials against local password hash and returns JWT token.

    Args:
        request: Login request with email and password
        db: Database session

    Returns:
        TokenResponse with access_token and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Generate JWT token
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
    }


@router.post("/verify-token", response_model=dict)
async def verify_token_endpoint(
    request: TokenVerifyRequest,
) -> dict:
    """
    Verify a JWT token without requiring database session

    Args:
        request: Token verification request

    Returns:
        Token validity and user info if valid

    Raises:
        HTTPException: If token is invalid
    """
    token_data = verify_token(request.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return {
        "valid": True,
        "user_id": token_data.user_id,
        "email": token_data.email,
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current authenticated user's profile

    Args:
        current_user: Injected current user from JWT token

    Returns:
        User profile information
    """
    return current_user


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
) -> TokenResponse:
    """
    Refresh the access token using the current valid token

    Args:
        current_user: Current authenticated user

    Returns:
        New access token
    """
    access_token = create_access_token(
        user_id=current_user.id,
        email=current_user.email,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(current_user.id),
    }
