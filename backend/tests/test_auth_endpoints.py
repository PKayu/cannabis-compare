"""
Test suite for authentication endpoints (/api/auth/*)
"""
import pytest
from fastapi import status


@pytest.mark.auth
@pytest.mark.integration
class TestRegistration:
    """Tests for /api/auth/register endpoint"""

    def test_register_new_user_success(self, client, test_user_data):
        """Test successful user registration"""
        response = client.post("/api/auth/register", json=test_user_data)

        # Debug output
        if response.status_code != status.HTTP_200_OK:
            print(f"\nResponse status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_register_duplicate_email(self, client, create_test_user):
        """Test registration with already existing email"""
        # Create user first
        existing_user = create_test_user(email="duplicate@example.com")

        # Try to register with same email
        response = client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "username": "differentuser",
            "password": "password123",
        })

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "username": "testuser",
            "password": "password123",
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        # Missing password
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "username": "testuser",
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_empty_fields(self, client):
        """Test registration with empty field values"""
        response = client.post("/api/auth/register", json={
            "email": "",
            "username": "",
            "password": "",
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.auth
@pytest.mark.integration
class TestLogin:
    """Tests for /api/auth/login endpoint"""

    def test_login_success(self, client, create_test_user):
        """Test successful login with correct credentials"""
        # Create test user
        create_test_user(
            email="login@example.com",
            username="loginuser",
            password="LoginPass123!",
        )

        # Attempt login
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "LoginPass123!",
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "user_id" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, create_test_user):
        """Test login with incorrect password"""
        create_test_user(email="user@example.com", password="correct_password")

        response = client.post("/api/auth/login", json={
            "email": "user@example.com",
            "password": "wrong_password",
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with email that doesn't exist"""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password123",
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format"""
        response = client.post("/api/auth/login", json={
            "email": "not-an-email",
            "password": "password123",
        })

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials"""
        response = client.post("/api/auth/login", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.auth
@pytest.mark.integration
class TestGetCurrentUser:
    """Tests for /api/auth/me endpoint"""

    def test_get_current_user_authenticated(self, client, authenticated_user, auth_headers):
        """Test getting current user profile with valid token"""
        user, _ = authenticated_user

        response = client.get("/api/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify user data
        assert data["email"] == user.email
        assert data["username"] == user.username
        assert "id" in data
        assert "created_at" in data

    def test_get_current_user_no_token(self, client):
        """Test accessing /me without authorization header"""
        response = client.get("/api/auth/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "missing" in response.json()["detail"].lower()

    def test_get_current_user_invalid_token(self, client):
        """Test accessing /me with invalid token"""
        response = client.get("/api/auth/me", headers={
            "Authorization": "Bearer invalid_token_here"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_malformed_header(self, client):
        """Test accessing /me with malformed auth header"""
        # Missing 'Bearer' prefix
        response = client.get("/api/auth/me", headers={
            "Authorization": "some_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
@pytest.mark.integration
class TestTokenVerification:
    """Tests for /api/auth/verify-token endpoint"""

    def test_verify_valid_token(self, client, authenticated_user):
        """Test verifying a valid JWT token"""
        user, token = authenticated_user

        response = client.post("/api/auth/verify-token", json={
            "token": token
        })

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["valid"] is True
        assert data["email"] == user.email
        assert "user_id" in data

    def test_verify_invalid_token(self, client):
        """Test verifying an invalid token"""
        response = client.post("/api/auth/verify-token", json={
            "token": "invalid_token_string"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "invalid" in response.json()["detail"].lower()

    def test_verify_empty_token(self, client):
        """Test verifying an empty token"""
        response = client.post("/api/auth/verify-token", json={
            "token": ""
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_missing_token_field(self, client):
        """Test verify endpoint without token field"""
        response = client.post("/api/auth/verify-token", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.auth
@pytest.mark.integration
class TestTokenRefresh:
    """Tests for /api/auth/refresh endpoint"""

    def test_refresh_token_success(self, client, auth_headers):
        """Test refreshing token with valid current token"""
        response = client.post("/api/auth/refresh", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify new token returned
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_refresh_token_no_auth(self, client):
        """Test refreshing token without authorization"""
        response = client.post("/api/auth/refresh")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_invalid(self, client):
        """Test refreshing with invalid token"""
        response = client.post("/api/auth/refresh", headers={
            "Authorization": "Bearer invalid_token"
        })

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationFlow:
    """Integration tests for complete authentication flows"""

    def test_register_login_access_protected_route(self, client, test_user_data):
        """Test complete flow: register → login → access protected endpoint"""
        # 1. Register
        register_response = client.post("/api/auth/register", json=test_user_data)
        assert register_response.status_code == status.HTTP_200_OK
        register_token = register_response.json()["access_token"]

        # 2. Verify can access protected route with registration token
        me_response = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {register_token}"
        })
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.json()["email"] == test_user_data["email"]

        # 3. Login with same credentials
        login_response = client.post("/api/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        })
        assert login_response.status_code == status.HTTP_200_OK
        login_token = login_response.json()["access_token"]

        # 4. Verify can access protected route with login token
        me_response_2 = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {login_token}"
        })
        assert me_response_2.status_code == status.HTTP_200_OK
        assert me_response_2.json()["email"] == test_user_data["email"]

    def test_token_refresh_maintains_access(self, client, authenticated_user, auth_headers):
        """Test that refreshed token maintains access to protected routes"""
        user, old_token = authenticated_user

        # 1. Access protected route with original token
        response1 = client.get("/api/auth/me", headers=auth_headers)
        assert response1.status_code == status.HTTP_200_OK

        # 2. Refresh token
        refresh_response = client.post("/api/auth/refresh", headers=auth_headers)
        new_token = refresh_response.json()["access_token"]

        # 3. Access protected route with new token
        response2 = client.get("/api/auth/me", headers={
            "Authorization": f"Bearer {new_token}"
        })
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json()["email"] == user.email

    def test_multiple_users_independent_sessions(self, client):
        """Test that multiple users have independent authentication sessions"""
        # Create two users
        user1_data = {
            "email": "user1@example.com",
            "username": "user1",
            "password": "pass1",
        }
        user2_data = {
            "email": "user2@example.com",
            "username": "user2",
            "password": "pass2",
        }

        # Register both users
        response1 = client.post("/api/auth/register", json=user1_data)
        response2 = client.post("/api/auth/register", json=user2_data)

        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]

        # Each token should return its own user
        me1 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token1}"})
        me2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token2}"})

        assert me1.json()["email"] == "user1@example.com"
        assert me2.json()["email"] == "user2@example.com"
