"""
Tests for admin authentication and authorization (Story 1.1).

Tests cover:
- AC-1: User model has is_admin and last_login_at fields
- AC-2: First user is admin after migration (tested via registration)
- AC-3: require_admin returns 403 for non-admin
- AC-4: require_admin allows admin user
- AC-5: Login updates last_login_at
- AC-6: First registration becomes admin when no admin exists
"""
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.models import User


class TestUserModelFields:
    """Test that User model has the required fields (AC-1)."""

    def test_user_model_has_is_admin_field(self, test_session):
        """Verify User model has is_admin boolean field with default False."""
        user = User(
            email="test_admin_field@example.com",
            hashed_password="hashedpassword",
            display_name="Test User",
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        assert hasattr(user, "is_admin")
        assert user.is_admin is False  # Default should be False

    def test_user_model_has_last_login_at_field(self, test_session):
        """Verify User model has last_login_at nullable datetime field."""
        user = User(
            email="test_login_field@example.com",
            hashed_password="hashedpassword",
            display_name="Test User",
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        assert hasattr(user, "last_login_at")
        assert user.last_login_at is None  # Should be None initially

    def test_user_model_is_admin_can_be_set_true(self, test_session):
        """Verify is_admin field can be explicitly set to True."""
        user = User(
            email="explicit_admin@example.com",
            hashed_password="hashedpassword",
            display_name="Admin User",
            is_admin=True,
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        assert user.is_admin is True


class TestRequireAdminDependency:
    """Test the require_admin dependency (AC-3, AC-4).

    These tests call the actual require_admin function directly.
    FastAPI's Depends() is resolved at runtime, but in tests we can
    pass the user directly to the function.
    """

    def test_require_admin_raises_403_for_non_admin_user(self, sample_user):
        """Verify require_admin raises 403 when user is not an admin (AC-3)."""
        from app.dependencies import require_admin
        import asyncio

        # Precondition: sample_user is not admin
        assert sample_user.is_admin is False

        # Call the actual require_admin function with non-admin user
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                require_admin(current_user=sample_user)
            )

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Admin access required"

    def test_require_admin_returns_user_for_admin(self, admin_user):
        """Verify require_admin returns the user when they are an admin (AC-4)."""
        from app.dependencies import require_admin
        import asyncio

        # Precondition: admin_user has admin privileges
        assert admin_user.is_admin is True

        # Call the actual require_admin function with admin user
        result = asyncio.get_event_loop().run_until_complete(
            require_admin(current_user=admin_user)
        )

        # Should return the same user object
        assert result is admin_user
        assert result.is_admin is True

    def test_require_admin_checks_is_admin_attribute(self, test_session):
        """Verify require_admin specifically checks the is_admin attribute."""
        from app.dependencies import require_admin
        from app.services.auth import hash_password
        import asyncio

        # Create user with is_admin=False explicitly
        non_admin = User(
            email="explicit_non_admin@test.com",
            hashed_password=hash_password("password123"),
            display_name="Non Admin",
            is_active=True,
            is_admin=False,
        )
        test_session.add(non_admin)
        test_session.commit()
        test_session.refresh(non_admin)

        # Should raise 403
        with pytest.raises(HTTPException) as exc_info:
            asyncio.get_event_loop().run_until_complete(
                require_admin(current_user=non_admin)
            )

        assert exc_info.value.status_code == 403

        # Now set is_admin=True and verify it passes
        non_admin.is_admin = True
        test_session.commit()
        test_session.refresh(non_admin)

        result = asyncio.get_event_loop().run_until_complete(
            require_admin(current_user=non_admin)
        )
        assert result.is_admin is True


class TestLoginUpdatesLastLoginAt:
    """Test that login updates last_login_at timestamp (AC-5)."""

    def test_login_updates_last_login_at(self, client, test_session):
        """Verify successful login updates the user's last_login_at timestamp."""
        from app.services.auth import hash_password

        # Create a user directly
        user = User(
            email="login_test@example.com",
            hashed_password=hash_password("testpassword123"),
            display_name="Login Test User",
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Verify last_login_at is None before login
        assert user.last_login_at is None

        # Perform login
        response = client.post(
            "/api/auth/login",
            json={"email": "login_test@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200

        # Refresh user from database
        test_session.refresh(user)

        # Verify last_login_at is now set
        assert user.last_login_at is not None
        assert isinstance(user.last_login_at, datetime)

    def test_login_for_access_token_updates_last_login_at(self, client, test_session):
        """Verify OAuth2 token endpoint also updates last_login_at."""
        from app.services.auth import hash_password

        # Create a user directly
        user = User(
            email="oauth_login@example.com",
            hashed_password=hash_password("testpassword123"),
            display_name="OAuth Login Test",
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()
        test_session.refresh(user)

        # Verify last_login_at is None before login
        assert user.last_login_at is None

        # Perform OAuth2 login
        response = client.post(
            "/api/auth/token",
            data={"username": "oauth_login@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200

        # Refresh user from database
        test_session.refresh(user)

        # Verify last_login_at is now set
        assert user.last_login_at is not None


class TestFirstRegistrationBecomesAdmin:
    """Test that first registration becomes admin when no admin exists (AC-6)."""

    def test_first_registration_becomes_admin_when_no_admin_exists(self, client, test_session):
        """Verify the first user to register becomes admin when no admin exists."""
        # Verify no users exist
        user_count = test_session.query(User).count()
        assert user_count == 0

        # Register first user
        response = client.post(
            "/api/auth/register",
            json={
                "email": "first_user@example.com",
                "password": "testpassword123",
                "display_name": "First User",
            },
        )
        assert response.status_code == 201
        data = response.json()

        # First user should be admin
        assert data["is_admin"] is True

        # Verify in database
        user = test_session.query(User).filter(User.email == "first_user@example.com").first()
        assert user is not None
        assert user.is_admin is True

    def test_second_registration_is_not_admin(self, client, test_session):
        """Verify the second user to register is NOT admin."""
        # Register first user (becomes admin)
        response1 = client.post(
            "/api/auth/register",
            json={
                "email": "admin_user@example.com",
                "password": "testpassword123",
                "display_name": "Admin User",
            },
        )
        assert response1.status_code == 201
        assert response1.json()["is_admin"] is True

        # Register second user
        response2 = client.post(
            "/api/auth/register",
            json={
                "email": "second_user@example.com",
                "password": "testpassword123",
                "display_name": "Second User",
            },
        )
        assert response2.status_code == 201
        data = response2.json()

        # Second user should NOT be admin
        assert data["is_admin"] is False

        # Verify in database
        user = test_session.query(User).filter(User.email == "second_user@example.com").first()
        assert user is not None
        assert user.is_admin is False

    def test_registration_not_admin_when_admin_already_exists(self, client, admin_user, test_session):
        """Verify registration creates non-admin when an admin already exists."""
        # admin_user fixture creates an admin
        assert admin_user.is_admin is True

        # Register new user
        response = client.post(
            "/api/auth/register",
            json={
                "email": "new_user@example.com",
                "password": "testpassword123",
                "display_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()

        # New user should NOT be admin
        assert data["is_admin"] is False


class TestUserResponseSchema:
    """Test that UserResponse includes new fields (AC-1 verification via API)."""

    def test_user_response_includes_is_admin_field(self, client, sample_user, auth_token):
        """Verify /me endpoint returns is_admin field."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "is_admin" in data
        assert data["is_admin"] is False  # sample_user is not admin

    def test_user_response_includes_last_login_at_field(self, client, test_session):
        """Verify /me endpoint returns last_login_at field after login."""
        from app.services.auth import hash_password

        # Create user and login to set last_login_at
        user = User(
            email="schema_test@example.com",
            hashed_password=hash_password("testpassword123"),
            display_name="Schema Test",
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()

        # Login to get token and set last_login_at
        login_response = client.post(
            "/api/auth/login",
            json={"email": "schema_test@example.com", "password": "testpassword123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        # Get user info
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "last_login_at" in data
        assert data["last_login_at"] is not None

    def test_user_response_includes_is_active_field(self, client, sample_user, auth_token):
        """Verify /me endpoint returns is_active field."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "is_active" in data
        assert data["is_active"] is True  # sample_user is active

    def test_admin_user_response_shows_is_admin_true(self, client, admin_user, admin_auth_token):
        """Verify admin user's /me endpoint shows is_admin=true."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert data["is_admin"] is True
