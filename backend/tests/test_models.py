"""
Tests for database models.
"""
from datetime import datetime, timedelta
import pytest
from sqlalchemy.exc import IntegrityError

from app.models import User, RefreshToken


class TestRefreshTokenModel:
    """Tests for RefreshToken model (Story 0.2)."""

    def test_refresh_token_creation(self, test_session, sample_user):
        """Test creating a refresh token record."""
        expires_at = datetime.utcnow() + timedelta(days=7)

        token = RefreshToken(
            jti="test-jti-12345",
            user_id=sample_user.id,
            expires_at=expires_at,
            revoked=False,
        )
        test_session.add(token)
        test_session.commit()

        # Verify saved
        assert token.id is not None
        assert token.jti == "test-jti-12345"
        assert token.user_id == sample_user.id
        assert token.expires_at == expires_at
        assert token.revoked is False
        assert token.revoked_at is None
        assert token.created_at is not None

    def test_refresh_token_fields_exist(self, test_session, sample_user):
        """Test that RefreshToken has all required fields."""
        token = RefreshToken(
            jti="jti-test",
            user_id=sample_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )

        # Check all required fields exist
        assert hasattr(token, 'id')
        assert hasattr(token, 'jti')
        assert hasattr(token, 'user_id')
        assert hasattr(token, 'expires_at')
        assert hasattr(token, 'revoked')
        assert hasattr(token, 'revoked_at')
        assert hasattr(token, 'created_at')
        assert hasattr(token, 'family_id')
        assert hasattr(token, 'user')

    def test_refresh_token_unique_jti(self, test_session, sample_user):
        """Test that jti must be unique."""
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Create first token
        token1 = RefreshToken(
            jti="duplicate-jti",
            user_id=sample_user.id,
            expires_at=expires_at,
        )
        test_session.add(token1)
        test_session.commit()

        # Try to create second token with same jti - should fail
        token2 = RefreshToken(
            jti="duplicate-jti",
            user_id=sample_user.id,
            expires_at=expires_at,
        )
        test_session.add(token2)

        with pytest.raises(IntegrityError):
            test_session.commit()

    def test_refresh_token_user_relationship(self, test_session, sample_user):
        """Test relationship between RefreshToken and User."""
        token = RefreshToken(
            jti="relationship-test",
            user_id=sample_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        test_session.add(token)
        test_session.commit()

        # Verify relationship works both ways
        assert token.user.id == sample_user.id
        assert token.user.email == sample_user.email

        # Verify user has refresh_tokens relationship
        test_session.refresh(sample_user)
        user_tokens = list(sample_user.refresh_tokens)
        assert len(user_tokens) == 1
        assert user_tokens[0].jti == "relationship-test"

    def test_refresh_token_revocation(self, test_session, sample_user):
        """Test revoking a refresh token."""
        token = RefreshToken(
            jti="revoke-test",
            user_id=sample_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False,
        )
        test_session.add(token)
        test_session.commit()

        # Revoke the token
        token.revoked = True
        token.revoked_at = datetime.utcnow()
        test_session.commit()

        # Verify revocation
        assert token.revoked is True
        assert token.revoked_at is not None

    def test_refresh_token_family_tracking(self, test_session, sample_user):
        """Test token family tracking for rotation."""
        family_id = "family-123"

        # Create two tokens in the same family
        token1 = RefreshToken(
            jti="jti-1",
            user_id=sample_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            family_id=family_id,
        )
        token2 = RefreshToken(
            jti="jti-2",
            user_id=sample_user.id,
            expires_at=datetime.utcnow() + timedelta(days=7),
            family_id=family_id,
        )

        test_session.add_all([token1, token2])
        test_session.commit()

        # Verify both tokens share family_id
        assert token1.family_id == family_id
        assert token2.family_id == family_id
