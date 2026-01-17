"""
Unit tests for AuthService.
Tests password hashing, JWT token operations, and user authentication.
"""
import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from app.services.auth_service import AuthService, pwd_context


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_different_value(self):
        """Password hash should be different from original password."""
        password = "mysecretpassword123"
        hashed = AuthService.hash_password(password)
        assert hashed != password

    def test_hash_password_returns_bcrypt_hash(self):
        """Hash should be a bcrypt hash (starts with $2b$)."""
        password = "mysecretpassword123"
        hashed = AuthService.hash_password(password)
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self):
        """Verify should return True for correct password."""
        password = "mysecretpassword123"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Verify should return False for incorrect password."""
        password = "mysecretpassword123"
        wrong_password = "wrongpassword"
        hashed = AuthService.hash_password(password)
        assert AuthService.verify_password(wrong_password, hashed) is False

    def test_hash_password_unique_per_call(self):
        """Same password should produce different hashes (due to salt)."""
        password = "mysecretpassword123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        assert hash1 != hash2
        # But both should verify correctly
        assert AuthService.verify_password(password, hash1) is True
        assert AuthService.verify_password(password, hash2) is True


class TestJWTOperations:
    """Tests for JWT token creation and validation."""

    def test_create_access_token(self):
        """Should create a valid JWT token."""
        data = {"sub": "123"}
        token = AuthService.create_access_token(data)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_custom_expiry(self):
        """Should accept custom expiration delta."""
        data = {"sub": "123"}
        expires = timedelta(hours=2)
        token = AuthService.create_access_token(data, expires_delta=expires)
        assert isinstance(token, str)

    def test_decode_token_valid(self):
        """Should decode a valid token correctly."""
        data = {"sub": "123", "custom": "value"}
        token = AuthService.create_access_token(data)
        decoded = AuthService.decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == "123"
        assert decoded["custom"] == "value"
        assert "exp" in decoded

    def test_decode_token_invalid(self):
        """Should return None for invalid token."""
        decoded = AuthService.decode_token("invalid.token.here")
        assert decoded is None

    def test_decode_token_expired(self):
        """Should return None for expired token."""
        data = {"sub": "123"}
        # Create token that expires immediately (negative delta)
        token = AuthService.create_access_token(data, expires_delta=timedelta(seconds=-10))
        decoded = AuthService.decode_token(token)
        assert decoded is None


class TestUserOperations:
    """Tests for user-related operations with mocked database."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def auth_service(self, mock_db):
        """Create an AuthService with mocked database."""
        return AuthService(mock_db)

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object."""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.hashed_password = AuthService.hash_password("password123")
        user.full_name = "Test User"
        user.is_active = True
        user.deleted_at = None
        return user

    def test_get_user_by_email_found(self, auth_service, mock_db, mock_user):
        """Should return user when found by email."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.get_user_by_email("test@example.com")
        assert result == mock_user

    def test_get_user_by_email_not_found(self, auth_service, mock_db):
        """Should return None when user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = auth_service.get_user_by_email("nonexistent@example.com")
        assert result is None

    def test_get_user_by_id_found(self, auth_service, mock_db, mock_user):
        """Should return user when found by ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.get_user_by_id(1)
        assert result == mock_user

    def test_authenticate_user_success(self, auth_service, mock_db, mock_user):
        """Should return user for valid credentials."""
        # Set up the mock to return user and verify password
        mock_user.hashed_password = AuthService.hash_password("password123")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.authenticate_user("test@example.com", "password123")
        assert result == mock_user

    def test_authenticate_user_wrong_password(self, auth_service, mock_db, mock_user):
        """Should return None for wrong password."""
        mock_user.hashed_password = AuthService.hash_password("password123")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.authenticate_user("test@example.com", "wrongpassword")
        assert result is None

    def test_authenticate_user_not_found(self, auth_service, mock_db):
        """Should return None when user not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = auth_service.authenticate_user("nonexistent@example.com", "password")
        assert result is None

    def test_authenticate_user_inactive(self, auth_service, mock_db, mock_user):
        """Should return None for inactive user."""
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.authenticate_user("test@example.com", "password123")
        assert result is None

    def test_create_user_success(self, auth_service, mock_db):
        """Should create a new user successfully."""
        # Mock that no existing user is found
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Mock the add/commit/refresh operations
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = auth_service.create_user(
            email="new@example.com",
            password="password123",
            full_name="New User"
        )

        # Verify add was called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_user_email_exists(self, auth_service, mock_db, mock_user):
        """Should raise ValueError when email already exists."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(ValueError, match="Email already registered"):
            auth_service.create_user(
                email="test@example.com",
                password="password123",
                full_name="Test User"
            )

    def test_get_current_user_from_token_valid(self, auth_service, mock_db, mock_user):
        """Should return user for valid token."""
        # Create a valid token
        token = AuthService.create_access_token({"sub": "1"})

        # Mock get_user_by_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = auth_service.get_current_user_from_token(token)
        assert result == mock_user

    def test_get_current_user_from_token_invalid(self, auth_service):
        """Should return None for invalid token."""
        result = auth_service.get_current_user_from_token("invalid.token")
        assert result is None

    def test_get_current_user_from_token_no_sub(self, auth_service):
        """Should return None when token has no 'sub' claim."""
        token = AuthService.create_access_token({"other": "data"})
        result = auth_service.get_current_user_from_token(token)
        assert result is None

    def test_get_current_user_from_token_user_not_found(self, auth_service, mock_db):
        """Should return None when user from token doesn't exist."""
        token = AuthService.create_access_token({"sub": "999"})
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = auth_service.get_current_user_from_token(token)
        assert result is None
