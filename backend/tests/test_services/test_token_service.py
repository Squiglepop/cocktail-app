"""
Unit tests for refresh token service functions (Story 0.2).
"""
import pytest
from datetime import datetime, timedelta

from app.models import RefreshToken
from app.services.auth import (
    store_refresh_token,
    is_refresh_token_valid,
    revoke_refresh_token,
    revoke_all_user_tokens,
    revoke_token_family,
)


class TestStoreRefreshToken:
    """Tests for store_refresh_token function."""

    def test_store_refresh_token_creates_record(self, test_session, sample_user):
        """Test storing a refresh token creates database record."""
        jti = "test-jti-123"
        expires_at = datetime.utcnow() + timedelta(days=7)
        family_id = "family-123"

        token = store_refresh_token(
            test_session,
            sample_user.id,
            jti,
            expires_at,
            family_id
        )

        assert token is not None
        assert token.jti == jti
        assert token.user_id == sample_user.id
        assert token.expires_at == expires_at
        assert token.family_id == family_id
        assert token.revoked is False

    def test_store_refresh_token_without_family_id(self, test_session, sample_user):
        """Test storing token without family_id generates one."""
        jti = "test-jti-456"
        expires_at = datetime.utcnow() + timedelta(days=7)

        token = store_refresh_token(
            test_session,
            sample_user.id,
            jti,
            expires_at
        )

        assert token is not None
        assert token.family_id is not None
        assert len(token.family_id) == 36  # UUID format


class TestIsRefreshTokenValid:
    """Tests for is_refresh_token_valid function."""

    def test_is_refresh_token_valid_returns_true(self, test_session, sample_user):
        """Test valid token returns True."""
        jti = "valid-token"
        expires_at = datetime.utcnow() + timedelta(days=7)
        store_refresh_token(test_session, sample_user.id, jti, expires_at)

        result = is_refresh_token_valid(test_session, jti)

        assert result is True

    def test_is_refresh_token_valid_revoked_returns_false(self, test_session, sample_user):
        """Test revoked token returns False."""
        jti = "revoked-token"
        expires_at = datetime.utcnow() + timedelta(days=7)
        token = store_refresh_token(test_session, sample_user.id, jti, expires_at)

        # Revoke the token
        token.revoked = True
        test_session.commit()

        result = is_refresh_token_valid(test_session, jti)

        assert result is False

    def test_is_refresh_token_valid_expired_returns_false(self, test_session, sample_user):
        """Test expired token returns False."""
        jti = "expired-token"
        expires_at = datetime.utcnow() - timedelta(days=1)  # Already expired
        store_refresh_token(test_session, sample_user.id, jti, expires_at)

        result = is_refresh_token_valid(test_session, jti)

        assert result is False

    def test_is_refresh_token_valid_nonexistent_returns_false(self, test_session):
        """Test nonexistent token returns False."""
        result = is_refresh_token_valid(test_session, "nonexistent-jti")

        assert result is False


class TestRevokeRefreshToken:
    """Tests for revoke_refresh_token function."""

    def test_revoke_refresh_token_marks_revoked(self, test_session, sample_user):
        """Test revoking a token marks it as revoked."""
        jti = "token-to-revoke"
        expires_at = datetime.utcnow() + timedelta(days=7)
        store_refresh_token(test_session, sample_user.id, jti, expires_at)

        result = revoke_refresh_token(test_session, jti)

        assert result is True

        # Verify token is revoked
        token = test_session.query(RefreshToken).filter(RefreshToken.jti == jti).first()
        assert token.revoked is True
        assert token.revoked_at is not None

    def test_revoke_refresh_token_nonexistent_returns_false(self, test_session):
        """Test revoking nonexistent token returns False."""
        result = revoke_refresh_token(test_session, "nonexistent-jti")

        assert result is False


class TestRevokeAllUserTokens:
    """Tests for revoke_all_user_tokens function."""

    def test_revoke_all_user_tokens_revokes_all(self, test_session, sample_user):
        """Test revoking all tokens for a user."""
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Create multiple tokens for user
        store_refresh_token(test_session, sample_user.id, "jti-1", expires_at)
        store_refresh_token(test_session, sample_user.id, "jti-2", expires_at)
        store_refresh_token(test_session, sample_user.id, "jti-3", expires_at)

        count = revoke_all_user_tokens(test_session, sample_user.id)

        assert count == 3

        # Verify all tokens are revoked
        tokens = test_session.query(RefreshToken).filter(
            RefreshToken.user_id == sample_user.id
        ).all()
        assert all(token.revoked for token in tokens)

    def test_revoke_all_user_tokens_only_unrevoked(self, test_session, sample_user):
        """Test only unrevoked tokens are counted."""
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Create tokens, revoke one manually
        store_refresh_token(test_session, sample_user.id, "jti-1", expires_at)
        token2 = store_refresh_token(test_session, sample_user.id, "jti-2", expires_at)
        token2.revoked = True
        test_session.commit()
        store_refresh_token(test_session, sample_user.id, "jti-3", expires_at)

        count = revoke_all_user_tokens(test_session, sample_user.id)

        # Should only revoke 2 (jti-1 and jti-3)
        assert count == 2


class TestRevokeTokenFamily:
    """Tests for revoke_token_family function."""

    def test_revoke_token_family_revokes_all_in_family(self, test_session, sample_user):
        """Test revoking entire token family."""
        family_id = "family-123"
        expires_at = datetime.utcnow() + timedelta(days=7)

        # Create multiple tokens in same family
        store_refresh_token(test_session, sample_user.id, "jti-1", expires_at, family_id)
        store_refresh_token(test_session, sample_user.id, "jti-2", expires_at, family_id)
        store_refresh_token(test_session, sample_user.id, "jti-3", expires_at, family_id)

        # Create token in different family
        store_refresh_token(test_session, sample_user.id, "jti-other", expires_at, "other-family")

        count = revoke_token_family(test_session, family_id)

        assert count == 3

        # Verify only family tokens are revoked
        family_tokens = test_session.query(RefreshToken).filter(
            RefreshToken.family_id == family_id
        ).all()
        assert all(token.revoked for token in family_tokens)

        other_token = test_session.query(RefreshToken).filter(
            RefreshToken.jti == "jti-other"
        ).first()
        assert other_token.revoked is False
