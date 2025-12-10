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
