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
