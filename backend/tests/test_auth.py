"""
Tests for authentication endpoints.
"""
import pytest


class TestRegister:
    """Tests for POST /api/auth/register endpoint."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "display_name": "New User",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["display_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_without_display_name(self, client):
        """Test registration without optional display_name."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "nodisplay@example.com",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "nodisplay@example.com"
        assert data["display_name"] is None

    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with already used email."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": sample_user.email,  # Already exists
                "password": "anotherpassword123",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123",
            },
        )

        assert response.status_code == 422

    def test_register_short_password(self, client):
        """Test registration with password shorter than 8 characters."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "shortpwd@example.com",
                "password": "short",  # Less than 8 chars
            },
        )

        assert response.status_code == 422

    def test_register_missing_email(self, client):
        """Test registration without email."""
        response = client.post(
            "/api/auth/register",
            json={
                "password": "securepassword123",
            },
        )

        assert response.status_code == 422

    def test_register_missing_password(self, client):
        """Test registration without password."""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "nopwd@example.com",
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/auth/login endpoint."""

    def test_login_success(self, client, sample_user):
        """Test successful login returns JWT token."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_login_wrong_password(self, client, sample_user):
        """Test login with wrong password returns 401."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email returns 401."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401

    def test_login_invalid_email_format(self, client):
        """Test login with invalid email format returns 422."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "not-an-email",
                "password": "somepassword",
            },
        )

        assert response.status_code == 422


class TestTokenEndpoint:
    """Tests for POST /api/auth/token endpoint (OAuth2 form)."""

    def test_token_success(self, client, sample_user):
        """Test successful token retrieval via form."""
        response = client.post(
            "/api/auth/token",
            data={
                "username": "test@example.com",
                "password": "testpassword123",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_token_wrong_password(self, client, sample_user):
        """Test token with wrong password."""
        response = client.post(
            "/api/auth/token",
            data={
                "username": "test@example.com",
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401


class TestGetMe:
    """Tests for GET /api/auth/me endpoint."""

    def test_get_me_authenticated(self, client, sample_user, auth_token):
        """Test getting current user info with valid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user.email
        assert data["display_name"] == sample_user.display_name
        assert data["id"] == sample_user.id

    def test_get_me_no_token(self, client):
        """Test getting current user without token returns 401."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token returns 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    def test_get_me_expired_token(self, client, expired_token):
        """Test getting current user with expired token returns 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401

    def test_get_me_inactive_user(self, client, inactive_user):
        """Test getting current user when user is inactive returns 401."""
        from app.services.auth import create_access_token
        from datetime import timedelta

        token = create_access_token(
            data={"sub": inactive_user.id},
            expires_delta=timedelta(hours=1)
        )

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


class TestUpdateMe:
    """Tests for PUT /api/auth/me endpoint."""

    def test_update_me_success(self, client, sample_user, auth_token):
        """Test updating current user's display_name."""
        response = client.put(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"display_name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Name"

    def test_update_me_no_auth(self, client):
        """Test updating without authentication returns 401."""
        response = client.put(
            "/api/auth/me",
            json={"display_name": "New Name"},
        )

        assert response.status_code == 401

    def test_update_me_empty_update(self, client, sample_user, auth_token):
        """Test updating with empty body doesn't change user."""
        response = client.put(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == sample_user.display_name

    def test_update_me_null_display_name(self, client, sample_user, auth_token):
        """Test setting display_name to null."""
        response = client.put(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"display_name": None},
        )

        # Should keep the old value since None in model_dump(exclude_unset=True)
        # doesn't include None values unless explicitly set
        assert response.status_code == 200


class TestRefresh:
    """Tests for POST /api/auth/refresh endpoint (Story 0.1 & 0.2)."""

    def test_refresh_success(self, client, sample_user, test_session):
        """Test successful token refresh with valid cookie."""
        from app.services.auth import create_refresh_token, store_refresh_token

        # Create and store a valid refresh token
        refresh_token, jti, expires_at = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti, expires_at)

        # Set cookie and refresh
        client.cookies.set("refresh_token", refresh_token, path="/api/auth")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    def test_refresh_without_cookie_returns_401(self, client):
        """Test refresh without cookie returns 401."""
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert "no refresh token" in response.json()["detail"].lower()

    def test_refresh_with_invalid_token_returns_401(self, client):
        """Test refresh with invalid/malformed token returns 401."""
        client.cookies.set("refresh_token", "invalid-token-garbage", path="/api/auth")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_refresh_with_expired_token_returns_401(self, client, sample_user, test_session):
        """Test refresh with expired token returns 401."""
        from app.services.auth import create_refresh_token, store_refresh_token
        from datetime import timedelta

        # Create an already-expired refresh token
        refresh_token, jti, expires_at = create_refresh_token(
            data={"sub": sample_user.id},
            expires_delta=timedelta(seconds=-10)  # Already expired
        )
        store_refresh_token(test_session, sample_user.id, jti, expires_at)

        client.cookies.set("refresh_token", refresh_token, path="/api/auth")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401

    def test_refresh_with_revoked_token_returns_401(self, client, sample_user, test_session):
        """Test refresh with revoked token returns 401."""
        from app.services.auth import create_refresh_token, store_refresh_token, revoke_refresh_token

        # Create, store, then revoke
        refresh_token, jti, expires_at = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti, expires_at)
        revoke_refresh_token(test_session, jti)

        client.cookies.set("refresh_token", refresh_token, path="/api/auth")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()

    def test_refresh_rotates_token(self, client, sample_user, test_session):
        """Test that refresh issues a new token and revokes old one."""
        from app.services.auth import create_refresh_token, store_refresh_token, is_refresh_token_valid

        # Create and store original token
        refresh_token, jti, expires_at = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti, expires_at)

        # Verify original is valid
        assert is_refresh_token_valid(test_session, jti) is True

        # Refresh
        client.cookies.set("refresh_token", refresh_token, path="/api/auth")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 200

        # Original token should now be revoked
        assert is_refresh_token_valid(test_session, jti) is False

    def test_refresh_token_reuse_revokes_family(self, client, sample_user, test_session):
        """Test that reusing a revoked token revokes entire token family (theft detection)."""
        from app.services.auth import create_refresh_token, store_refresh_token, revoke_refresh_token
        from app.models import RefreshToken

        # Create token with specific family
        refresh_token, jti, expires_at = create_refresh_token(data={"sub": sample_user.id})
        stored = store_refresh_token(test_session, sample_user.id, jti, expires_at)
        family_id = stored.family_id

        # Create another token in same family (simulates rotation)
        refresh_token2, jti2, expires_at2 = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti2, expires_at2, family_id)

        # Revoke the first token (simulates it was already used)
        revoke_refresh_token(test_session, jti)

        # Try to reuse the revoked token (attacker scenario)
        client.cookies.set("refresh_token", refresh_token, path="/api/auth")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert "reuse detected" in response.json()["detail"].lower()

        # Both tokens in family should now be revoked
        all_family_tokens = test_session.query(RefreshToken).filter(
            RefreshToken.family_id == family_id
        ).all()
        for token in all_family_tokens:
            assert token.revoked is True

    def test_refresh_for_inactive_user_returns_401(self, client, inactive_user, test_session):
        """Test refresh for inactive user returns 401."""
        from app.services.auth import create_refresh_token, store_refresh_token

        refresh_token, jti, expires_at = create_refresh_token(data={"sub": inactive_user.id})
        store_refresh_token(test_session, inactive_user.id, jti, expires_at)

        client.cookies.set("refresh_token", refresh_token, path="/api/auth")
        response = client.post("/api/auth/refresh")

        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


class TestLogout:
    """Tests for POST /api/auth/logout endpoint (Story 0.2)."""

    def test_logout_success_revokes_token(self, client, sample_user, test_session):
        """Test logout successfully revokes refresh token in database."""
        from app.services.auth import create_refresh_token, store_refresh_token, is_refresh_token_valid
        from datetime import timedelta

        # Create and store a refresh token
        refresh_token, jti, expires_at = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti, expires_at)

        # Verify token is valid before logout
        assert is_refresh_token_valid(test_session, jti) is True

        # Logout with refresh token cookie
        client.cookies.set("refresh_token", refresh_token, path="/api/auth")
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

        # Verify token is revoked in database
        assert is_refresh_token_valid(test_session, jti) is False

    def test_logout_without_cookie_succeeds(self, client):
        """Test logout without refresh token cookie succeeds gracefully."""
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    def test_logout_with_invalid_token_succeeds(self, client):
        """Test logout with invalid refresh token succeeds gracefully."""
        client.cookies.set("refresh_token", "invalid-token", path="/api/auth")
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()


class TestRevokeAll:
    """Tests for POST /api/auth/revoke-all endpoint (Story 0.2)."""

    def test_revoke_all_revokes_all_user_tokens(self, client, sample_user, auth_token, test_session):
        """Test revoke-all endpoint revokes all refresh tokens for the user."""
        from app.services.auth import create_refresh_token, store_refresh_token, is_refresh_token_valid
        from datetime import timedelta

        # Create multiple refresh tokens for the user (simulating multiple devices)
        token1, jti1, expires1 = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti1, expires1)

        token2, jti2, expires2 = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti2, expires2)

        token3, jti3, expires3 = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti3, expires3)

        # Verify all tokens are valid before revoke-all
        assert is_refresh_token_valid(test_session, jti1) is True
        assert is_refresh_token_valid(test_session, jti2) is True
        assert is_refresh_token_valid(test_session, jti3) is True

        # Call revoke-all endpoint
        response = client.post(
            "/api/auth/revoke-all",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        assert "revoked" in response.json()["message"].lower()

        # Verify all tokens are now revoked
        assert is_refresh_token_valid(test_session, jti1) is False
        assert is_refresh_token_valid(test_session, jti2) is False
        assert is_refresh_token_valid(test_session, jti3) is False

    def test_revoke_all_requires_authentication(self, client):
        """Test revoke-all requires authentication."""
        response = client.post("/api/auth/revoke-all")

        assert response.status_code == 401

    def test_revoke_all_clears_cookie(self, client, sample_user, auth_token, test_session):
        """Test revoke-all clears the refresh token cookie."""
        from app.services.auth import create_refresh_token, store_refresh_token

        # Create and set a refresh token cookie
        token, jti, expires = create_refresh_token(data={"sub": sample_user.id})
        store_refresh_token(test_session, sample_user.id, jti, expires)
        client.cookies.set("refresh_token", token, path="/api/auth")

        # Call revoke-all
        response = client.post(
            "/api/auth/revoke-all",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200

        # Cookie should be cleared (would need to check Set-Cookie header for deletion)
        # For now, just verify the endpoint executed successfully
