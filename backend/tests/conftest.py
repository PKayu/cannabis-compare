"""
Pytest fixtures and configuration for backend tests
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from database import Base, get_db
from models import User
from services.auth_service import hash_password, create_access_token


# Use in-memory SQLite database for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test database engine
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test function

    Yields:
        Database session that is rolled back after test completes
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create new session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def test_app():
    """
    Create a test FastAPI app without lifespan for testing

    This avoids the scheduler startup issues that occur with the main app's lifespan
    """
    from fastapi import FastAPI
    from routers import (
        admin_flags, admin_scrapers, search, products, dispensaries, auth, users,
        scrapers, reviews, watchlist, notifications
    )
    from fastapi.middleware.cors import CORSMiddleware

    # Create test app without lifespan
    test_app_instance = FastAPI(
        title="Utah Cannabis Aggregator API (Test)",
        description="REST API for testing",
        version="0.1.0",
    )

    # Register routers
    test_app_instance.include_router(admin_flags.router)
    test_app_instance.include_router(admin_scrapers.router)
    test_app_instance.include_router(auth.router)
    test_app_instance.include_router(users.router)
    test_app_instance.include_router(reviews.router)
    test_app_instance.include_router(search.router)
    test_app_instance.include_router(products.router)
    test_app_instance.include_router(dispensaries.router)
    test_app_instance.include_router(scrapers.router)
    test_app_instance.include_router(watchlist.router)
    test_app_instance.include_router(notifications.router)

    # Configure CORS
    test_app_instance.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @test_app_instance.get("/health")
    async def health_check():
        return {"status": "healthy", "version": "0.1.0"}

    return test_app_instance


@pytest.fixture(scope="function")
def client(test_app, db_session):
    """
    Create a test client with test database dependency override

    Args:
        test_app: Test FastAPI app without lifespan
        db_session: Test database session

    Yields:
        FastAPI TestClient for making HTTP requests
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override database dependency
    test_app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(test_app) as test_client:
        yield test_client

    # Clean up
    test_app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """
    Standard test user data for registration tests

    Returns:
        Dictionary with test user credentials
    """
    return {
        "email": "testuser@example.com",
        "username": "testuser",
        "password": "SecurePassword123!",
    }


@pytest.fixture
def create_test_user(db_session):
    """
    Factory fixture to create test users in database

    Args:
        db_session: Database session

    Returns:
        Function that creates a user and returns user object
    """
    def _create_user(
        email="user@example.com",
        username="testuser",
        password="password123",
        user_id=None
    ):
        """
        Create a user in the test database

        Args:
            email: User email
            username: Username
            password: Plain text password (will be hashed)
            user_id: Optional specific user ID

        Returns:
            User object
        """
        user = User(
            id=user_id,
            email=email,
            username=username,
            hashed_password=hash_password(password),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
def authenticated_user(create_test_user, db_session):
    """
    Create a test user and return user object with auth token

    Args:
        create_test_user: User creation factory
        db_session: Database session

    Returns:
        Tuple of (user, auth_token)
    """
    user = create_test_user(
        email="auth@example.com",
        username="authuser",
        password="AuthPass123!",
    )

    token = create_access_token(
        user_id=user.id,
        email=user.email,
    )

    return user, token


@pytest.fixture
def auth_headers(authenticated_user):
    """
    Generate authorization headers for authenticated requests

    Args:
        authenticated_user: Tuple of (user, token)

    Returns:
        Dictionary with Authorization header
    """
    _, token = authenticated_user
    return {"Authorization": f"Bearer {token}"}


# Mock Supabase client for tests (avoids external API calls)
@pytest.fixture(autouse=True)
def mock_supabase(monkeypatch):
    """
    Mock Supabase client to avoid external API calls during tests

    This fixture automatically applies to all tests unless explicitly disabled.
    """
    import uuid

    class MockSupabaseClient:
        @staticmethod
        def get_client():
            """Mock get_client - returns None (not needed for mocked methods)"""
            return None

        @staticmethod
        def create_user(email: str, password: str):
            """Mock user creation - returns fake user data"""
            return {
                "id": str(uuid.uuid4()),
                "email": email,
            }

        @staticmethod
        def delete_user(user_id: str):
            """Mock user deletion"""
            return True

        @staticmethod
        def verify_session(token: str):
            """Mock session verification - returns None (forces JWT path)"""
            return None

        @staticmethod
        def get_user_by_email(email: str):
            """Mock get user by email"""
            return None

    # Replace SupabaseClient in all modules that import it
    from services import supabase_client as supa_module
    from routers import auth as auth_module

    # Mock in services.supabase_client
    monkeypatch.setattr(supa_module, "SupabaseClient", MockSupabaseClient)

    # Mock in routers.auth (if it's already imported)
    monkeypatch.setattr(auth_module, "SupabaseClient", MockSupabaseClient)
