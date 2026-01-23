"""
Test suite for user profile endpoints (/api/users/*)
"""
import pytest
from fastapi import status
from models import Product, Review, Brand


@pytest.mark.integration
class TestGetUserProfile:
    """Tests for GET /api/users/me endpoint"""

    def test_get_profile_authenticated(self, client, authenticated_user, auth_headers):
        """Test getting own profile when authenticated"""
        user, _ = authenticated_user

        response = client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["email"] == user.email
        assert data["username"] == user.username
        assert data["review_count"] == 0  # New user, no reviews
        assert "id" in data
        assert "created_at" in data

    def test_get_profile_unauthenticated(self, client):
        """Test accessing profile without authentication"""
        response = client.get("/api/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_profile_with_reviews(self, client, authenticated_user, auth_headers, db_session):
        """Test profile shows correct review count"""
        user, _ = authenticated_user

        # Create a test brand and product
        brand = Brand(id="test-brand-id", name="Test Brand")
        product = Product(
            id="test-product-id",
            name="Test Product",
            brand_id="test-brand-id",
            thc_percentage=20.0,
            product_type="flower",
        )
        db_session.add(brand)
        db_session.add(product)
        db_session.commit()

        # Create a couple of reviews
        review1 = Review(
            user_id=user.id,
            product_id="test-product-id",
            rating=5,
            effects_rating=5,
            taste_rating=4,
            value_rating=5,
            comment="Great product!",
        )
        review2 = Review(
            user_id=user.id,
            product_id="test-product-id",
            rating=4,
            effects_rating=4,
            taste_rating=4,
            value_rating=4,
            comment="Pretty good!",
        )
        db_session.add(review1)
        db_session.add(review2)
        db_session.commit()

        # Get profile
        response = client.get("/api/users/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["review_count"] == 2


@pytest.mark.integration
class TestUpdateUserProfile:
    """Tests for PATCH /api/users/me endpoint"""

    def test_update_username_success(self, client, auth_headers):
        """Test successfully updating username"""
        response = client.patch("/api/users/me", json={
            "username": "newusername"
        }, headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["username"] == "newusername"

    def test_update_username_already_taken(self, client, auth_headers, create_test_user):
        """Test updating to a username that already exists"""
        # Create another user with the target username
        create_test_user(username="taken_username", email="other@example.com")

        # Try to update to that username
        response = client.patch("/api/users/me", json={
            "username": "taken_username"
        }, headers=auth_headers)

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already taken" in response.json()["detail"].lower()

    def test_update_username_empty_request(self, client, auth_headers):
        """Test update with empty request body"""
        response = client.patch("/api/users/me", json={}, headers=auth_headers)

        # Should succeed but not change anything
        assert response.status_code == status.HTTP_200_OK

    def test_update_unauthenticated(self, client):
        """Test updating profile without authentication"""
        response = client.patch("/api/users/me", json={
            "username": "hacker"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestGetUserReviews:
    """Tests for GET /api/users/me/reviews endpoint"""

    def test_get_reviews_empty(self, client, auth_headers):
        """Test getting reviews when user has none"""
        response = client.get("/api/users/me/reviews", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_reviews_with_data(self, client, authenticated_user, auth_headers, db_session):
        """Test getting reviews when user has some"""
        user, _ = authenticated_user

        # Create test data
        brand = Brand(id="brand-1", name="Brand")
        product = Product(
            id="product-1",
            name="Test Product",
            brand_id="brand-1",
            thc_percentage=20.0,
            product_type="flower",
        )
        db_session.add(brand)
        db_session.add(product)
        db_session.commit()

        # Create reviews
        review = Review(
            user_id=user.id,
            product_id="product-1",
            rating=5,
            effects_rating=5,
            taste_rating=4,
            value_rating=5,
            comment="Amazing!",
        )
        db_session.add(review)
        db_session.commit()

        # Get reviews
        response = client.get("/api/users/me/reviews", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        assert data[0]["product_name"] == "Test Product"
        assert data[0]["rating"] == 5
        assert data[0]["comment"] == "Amazing!"

    def test_get_reviews_pagination(self, client, authenticated_user, auth_headers, db_session):
        """Test pagination of review results"""
        user, _ = authenticated_user

        # Create test product
        brand = Brand(id="brand-1", name="Brand")
        product = Product(
            id="product-1",
            name="Product",
            brand_id="brand-1",
            thc_percentage=20.0,
            product_type="flower",
        )
        db_session.add(brand)
        db_session.add(product)

        # Create multiple reviews
        for i in range(10):
            review = Review(
                user_id=user.id,
                product_id="product-1",
                rating=5,
                effects_rating=5,
                taste_rating=5,
                value_rating=5,
                comment=f"Review {i}",
            )
            db_session.add(review)
        db_session.commit()

        # Test limit
        response = client.get("/api/users/me/reviews?limit=5", headers=auth_headers)
        assert len(response.json()) == 5

        # Test skip
        response = client.get("/api/users/me/reviews?skip=5", headers=auth_headers)
        assert len(response.json()) == 5

    def test_get_reviews_unauthenticated(self, client):
        """Test accessing reviews without authentication"""
        response = client.get("/api/users/me/reviews")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
class TestGetPublicUserProfile:
    """Tests for GET /api/users/{user_id} endpoint"""

    def test_get_public_profile_exists(self, client, create_test_user):
        """Test getting public profile for existing user"""
        user = create_test_user(email="public@example.com", username="publicuser")

        response = client.get(f"/api/users/{user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["username"] == "publicuser"
        assert data["email"] == "public@example.com"
        assert data["review_count"] == 0

    def test_get_public_profile_not_found(self, client):
        """Test getting profile for non-existent user"""
        response = client.get("/api/users/nonexistent-id")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    def test_get_public_profile_no_auth_required(self, client, create_test_user):
        """Test that public profile doesn't require authentication"""
        user = create_test_user()

        # Access without auth headers
        response = client.get(f"/api/users/{user.id}")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
class TestGetPublicUserReviews:
    """Tests for GET /api/users/{user_id}/reviews endpoint"""

    def test_get_public_reviews_exists(self, client, create_test_user, db_session):
        """Test getting public reviews for existing user"""
        user = create_test_user()

        # Create test data
        brand = Brand(id="brand-1", name="Brand")
        product = Product(
            id="product-1",
            name="Product",
            brand_id="brand-1",
            thc_percentage=20.0,
            product_type="flower",
        )
        db_session.add(brand)
        db_session.add(product)

        review = Review(
            user_id=user.id,
            product_id="product-1",
            rating=4,
            effects_rating=4,
            taste_rating=4,
            value_rating=4,
            comment="Good stuff",
        )
        db_session.add(review)
        db_session.commit()

        # Get public reviews
        response = client.get(f"/api/users/{user.id}/reviews")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data) == 1
        assert data[0]["comment"] == "Good stuff"

    def test_get_public_reviews_user_not_found(self, client):
        """Test getting reviews for non-existent user"""
        response = client.get("/api/users/nonexistent-id/reviews")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_public_reviews_no_auth_required(self, client, create_test_user):
        """Test that public reviews don't require authentication"""
        user = create_test_user()

        # Access without auth headers
        response = client.get(f"/api/users/{user.id}/reviews")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []  # No reviews
