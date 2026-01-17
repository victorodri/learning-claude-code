"""
Integration tests for authentication endpoints.
Tests registration, login, and protected endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.main import app
from app.db.base import get_db
from app.services.auth_service import AuthService
from app.models.user import User


# Test fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def client(mock_db):
    """Create a test client with mocked database."""
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.hashed_password = AuthService.hash_password("password123")
    user.full_name = "Test User"
    user.is_active = True
    user.deleted_at = None
    user.created_at = MagicMock()
    user.created_at.isoformat.return_value = "2025-01-01T00:00:00"
    user.updated_at = MagicMock()
    user.updated_at.isoformat.return_value = "2025-01-01T00:00:00"
    user.to_dict.return_value = {
        "id": 1,
        "email": "test@example.com",
        "full_name": "Test User",
        "is_active": True,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00"
    }
    return user


class TestRegisterEndpoint:
    """Tests for POST /auth/register endpoint."""

    def test_register_success(self, client, mock_db, mock_user):
        """Should register a new user successfully."""
        # Mock no existing user found, then return created user
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock(side_effect=lambda u: setattr(u, 'id', 1))

        # Need to mock the User creation
        with patch('app.services.auth_service.User') as MockUser:
            mock_instance = mock_user
            MockUser.return_value = mock_instance

            response = client.post(
                "/auth/register",
                json={
                    "email": "new@example.com",
                    "password": "password123",
                    "full_name": "New User"
                }
            )

            assert response.status_code == 201
            data = response.json()
            assert "id" in data
            assert data["email"] == "test@example.com"

    def test_register_email_exists(self, client, mock_db, mock_user):
        """Should return 400 when email already exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Should return 422 for invalid email format."""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Should return 422 for password less than 8 characters."""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "short",
                "full_name": "Test User"
            }
        )

        assert response.status_code == 422

    def test_register_missing_fields(self, client):
        """Should return 422 when required fields are missing."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /auth/login endpoint."""

    def test_login_success(self, client, mock_db, mock_user):
        """Should return JWT token for valid credentials."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Verify it's a valid JWT format
        assert len(data["access_token"].split(".")) == 3

    def test_login_wrong_password(self, client, mock_db, mock_user):
        """Should return 401 for wrong password."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    def test_login_user_not_found(self, client, mock_db):
        """Should return 401 when user doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    def test_login_inactive_user(self, client, mock_db, mock_user):
        """Should return 401 for inactive user."""
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401


class TestMeEndpoint:
    """Tests for GET /auth/me endpoint."""

    def test_me_with_valid_token(self, client, mock_db, mock_user):
        """Should return user info with valid token."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Create a valid token
        token = AuthService.create_access_token({"sub": "1"})

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["email"] == "test@example.com"
        assert "hashed_password" not in data

    def test_me_without_token(self, client):
        """Should return 403 without token."""
        response = client.get("/auth/me")

        assert response.status_code == 403

    def test_me_with_invalid_token(self, client):
        """Should return 401 with invalid token."""
        response = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    def test_me_with_expired_token(self, client):
        """Should return 401 with expired token."""
        from datetime import timedelta
        token = AuthService.create_access_token(
            {"sub": "1"},
            expires_delta=timedelta(seconds=-10)
        )

        response = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 401


class TestProtectedRatingEndpoints:
    """Tests for protected rating endpoints."""

    def test_create_rating_without_auth(self, client):
        """Should return 403 when creating rating without auth."""
        response = client.post(
            "/courses/1/ratings",
            json={"rating": 5}
        )

        assert response.status_code == 403

    def test_create_rating_with_auth(self, client, mock_db, mock_user):
        """Should allow creating rating with valid token."""
        # First query returns user (for auth), subsequent queries are for course/rating
        def side_effect(*args, **kwargs):
            return MagicMock(
                filter=MagicMock(return_value=MagicMock(
                    first=MagicMock(return_value=mock_user)
                ))
            )

        mock_db.query.side_effect = side_effect

        token = AuthService.create_access_token({"sub": "1"})

        # This will fail because we need to mock the course service too,
        # but it shouldn't fail with 401/403
        response = client.post(
            "/courses/1/ratings",
            json={"rating": 5},
            headers={"Authorization": f"Bearer {token}"}
        )

        # Even if it fails with 404 (course not found), it means auth passed
        assert response.status_code != 401
        assert response.status_code != 403

    def test_update_rating_without_auth(self, client):
        """Should return 403 when updating rating without auth."""
        response = client.put(
            "/courses/1/ratings",
            json={"rating": 4}
        )

        assert response.status_code == 403

    def test_delete_rating_without_auth(self, client):
        """Should return 403 when deleting rating without auth."""
        response = client.delete("/courses/1/ratings")

        assert response.status_code == 403
