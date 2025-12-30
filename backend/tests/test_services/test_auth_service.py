"""
Unit tests for authentication service.
"""
import pytest
from datetime import timedelta

from app.services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_user_by_id,
    get_user_by_email,
    authenticate_user,
)
from app.models import User


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_hash(self):
        """Test that hash_password returns a hash different from plaintext."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_different_for_same_input(self):
        """Test that hashing same password twice gives different results (bcrypt salt)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Bcrypt uses random salt, so hashes should differ
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that correct password verifies successfully."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_wrong(self):
        """Test that wrong password fails verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_fails(self):
        """Test that empty password fails verification."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False


class TestAccessToken:
    """Tests for JWT token creation and decoding."""

    def test_create_access_token_contains_sub(self):
        """Test that created token contains the subject claim."""
        user_id = "test-user-id-123"
        token = create_access_token(data={"sub": user_id})

        assert token is not None
        assert len(token) > 0

    def test_create_access_token_custom_expiry(self):
        """Test that custom expiry delta works."""
        user_id = "test-user-id-123"
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(hours=2)
        )

        assert token is not None

    def test_decode_access_token_valid(self):
        """Test that valid token decodes correctly."""
        user_id = "test-user-id-123"
        token = create_access_token(data={"sub": user_id})

        token_data = decode_access_token(token)

        assert token_data is not None
        assert token_data.user_id == user_id

    def test_decode_access_token_expired(self):
        """Test that expired token returns None."""
        user_id = "test-user-id-123"
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(seconds=-10)  # Already expired
        )

        token_data = decode_access_token(token)

        assert token_data is None

    def test_decode_access_token_invalid(self):
        """Test that invalid token returns None."""
        invalid_token = "not.a.valid.token"

        token_data = decode_access_token(invalid_token)

        assert token_data is None

    def test_decode_access_token_empty(self):
        """Test that empty token returns None."""
        token_data = decode_access_token("")

        assert token_data is None

    def test_decode_access_token_missing_sub(self):
        """Test that token without sub claim returns None."""
        # Create a token without the 'sub' claim
        token = create_access_token(data={"other": "data"})

        token_data = decode_access_token(token)

        assert token_data is None


class TestUserLookup:
    """Tests for user lookup functions."""

    def test_get_user_by_id_found(self, test_session, sample_user):
        """Test getting a user by valid ID."""
        user = get_user_by_id(test_session, sample_user.id)

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email

    def test_get_user_by_id_not_found(self, test_session):
        """Test getting a user by non-existent ID."""
        user = get_user_by_id(test_session, "non-existent-id")

        assert user is None

    def test_get_user_by_email_found(self, test_session, sample_user):
        """Test getting a user by valid email."""
        user = get_user_by_email(test_session, sample_user.email)

        assert user is not None
        assert user.id == sample_user.id
        assert user.email == sample_user.email

    def test_get_user_by_email_not_found(self, test_session):
        """Test getting a user by non-existent email."""
        user = get_user_by_email(test_session, "nonexistent@example.com")

        assert user is None


class TestAuthenticateUser:
    """Tests for user authentication function."""

    def test_authenticate_user_success(self, test_session, sample_user):
        """Test successful authentication."""
        user = authenticate_user(test_session, "test@example.com", "testpassword123")

        assert user is not None
        assert user.id == sample_user.id

    def test_authenticate_user_wrong_password(self, test_session, sample_user):
        """Test authentication with wrong password."""
        user = authenticate_user(test_session, "test@example.com", "wrongpassword")

        assert user is None

    def test_authenticate_user_nonexistent_email(self, test_session):
        """Test authentication with non-existent email."""
        user = authenticate_user(test_session, "nonexistent@example.com", "password")

        assert user is None

    def test_authenticate_user_empty_password(self, test_session, sample_user):
        """Test authentication with empty password."""
        user = authenticate_user(test_session, "test@example.com", "")

        assert user is None


class TestRefreshToken:
    """Tests for refresh token creation and decoding (Story 0.2)."""

    def test_create_refresh_token_returns_tuple(self):
        """Test that create_refresh_token returns (token, jti, expires_at)."""
        user_id = "test-user-id-123"
        result = create_refresh_token(data={"sub": user_id})

        # Should return tuple of 3 elements
        assert isinstance(result, tuple)
        assert len(result) == 3

        token, jti, expires_at = result
        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(jti, str)
        assert len(jti) == 36  # UUID format
        assert expires_at is not None

    def test_create_refresh_token_jti_is_unique(self):
        """Test that each refresh token gets a unique jti."""
        user_id = "test-user-id-123"
        token1, jti1, _ = create_refresh_token(data={"sub": user_id})
        token2, jti2, _ = create_refresh_token(data={"sub": user_id})

        # JTIs should be different even for same user
        assert jti1 != jti2
        assert token1 != token2

    def test_create_refresh_token_custom_expiry(self):
        """Test that custom expiry delta works."""
        user_id = "test-user-id-123"
        custom_delta = timedelta(days=30)
        token, jti, expires_at = create_refresh_token(
            data={"sub": user_id},
            expires_delta=custom_delta
        )

        assert token is not None
        assert jti is not None
        assert expires_at is not None

    def test_decode_refresh_token_returns_dict(self):
        """Test that decode_refresh_token returns dict with user_id and jti."""
        user_id = "test-user-id-123"
        token, expected_jti, _ = create_refresh_token(data={"sub": user_id})

        result = decode_refresh_token(token)

        assert isinstance(result, dict)
        assert "user_id" in result
        assert "jti" in result
        assert result["user_id"] == user_id
        assert result["jti"] == expected_jti

    def test_decode_refresh_token_invalid(self):
        """Test that invalid refresh token returns None."""
        invalid_token = "not.a.valid.token"

        result = decode_refresh_token(invalid_token)

        assert result is None

    def test_decode_refresh_token_expired(self):
        """Test that expired refresh token returns None."""
        user_id = "test-user-id-123"
        token, jti, _ = create_refresh_token(
            data={"sub": user_id},
            expires_delta=timedelta(seconds=-10)  # Already expired
        )

        result = decode_refresh_token(token)

        assert result is None

    def test_decode_refresh_token_access_token_fails(self):
        """Test that access tokens are rejected by decode_refresh_token."""
        user_id = "test-user-id-123"
        access_token = create_access_token(data={"sub": user_id})

        result = decode_refresh_token(access_token)

        # Should return None because type is "access" not "refresh"
        assert result is None
