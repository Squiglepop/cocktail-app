"""
Tests for admin user status management endpoint (Story 3-2).
"""
from app.models.user import User
from app.services.auth import hash_password, create_refresh_token, store_refresh_token


def _create_test_user(test_session, email, display_name=None, is_active=True, is_admin=False):
    """Helper to create a test user directly in DB."""
    user = User(
        email=email,
        hashed_password=hash_password("testpass123"),
        display_name=display_name,
        is_active=is_active,
        is_admin=is_admin,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


# --- AC-8: Auth tests (MANDATORY) ---


def test_patch_user_returns_401_without_auth(client, test_session):
    user = _create_test_user(test_session, "target@test.com")
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": False},
    )
    assert response.status_code == 401


def test_patch_user_returns_403_for_regular_user(client, auth_token, test_session):
    user = _create_test_user(test_session, "target2@test.com")
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- AC-1: Deactivation tests ---


def test_deactivate_user_sets_is_active_false(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "deactivate@test.com", is_active=True)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert "deactivated" in data["message"]


def test_deactivate_user_revokes_refresh_tokens(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "revoke@test.com", is_active=True)
    token, jti, expires = create_refresh_token(data={"sub": user.id})
    store_refresh_token(test_session, user.id, jti, expires)

    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200

    from app.models.refresh_token import RefreshToken
    token_record = test_session.query(RefreshToken).filter_by(jti=jti).first()
    assert token_record.revoked is True


# --- AC-2: Reactivation tests ---


def test_reactivate_user_sets_is_active_true(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "reactivate@test.com", is_active=False)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert "activated" in data["message"]


# --- AC-3, AC-6: Self-protection tests ---


def test_cannot_deactivate_own_account(client, admin_auth_token, admin_user):
    response = client.patch(
        f"/api/admin/users/{admin_user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "Cannot deactivate your own account" in response.json()["detail"]


def test_cannot_remove_own_admin_status(client, admin_auth_token, admin_user):
    response = client.patch(
        f"/api/admin/users/{admin_user.id}",
        json={"is_admin": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "Cannot remove your own admin status" in response.json()["detail"]


# --- AC-4, AC-5: Admin privilege tests ---


def test_grant_admin_to_regular_user(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "promote@test.com", is_admin=False)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_admin": True},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_admin"] is True
    assert "granted admin" in data["message"]


def test_revoke_admin_from_admin_user(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "demote@test.com", is_admin=True)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_admin": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_admin"] is False
    assert "revoked admin" in data["message"]


# --- AC-7: Login block tests ---


def test_deactivated_user_cannot_login(client, inactive_user):
    response = client.post(
        "/api/auth/login",
        json={"email": "inactive@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401
    assert "deactivated" in response.json()["detail"].lower()


def test_deactivated_user_cannot_get_token(client, inactive_user):
    response = client.post(
        "/api/auth/token",
        data={"username": "inactive@example.com", "password": "testpassword123"},
    )
    assert response.status_code == 401
    assert "deactivated" in response.json()["detail"].lower()


def test_reactivated_user_can_login_again(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "comeback@test.com", is_active=False)
    # Reactivate
    client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    # Try login
    response = client.post(
        "/api/auth/login",
        json={"email": "comeback@test.com", "password": "testpass123"},
    )
    assert response.status_code == 200


# --- Edge case tests ---


def test_patch_nonexistent_user_returns_404(client, admin_auth_token):
    response = client.patch(
        "/api/admin/users/nonexistent-id",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404


def test_patch_with_empty_body_returns_422(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "empty@test.com")
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422


def test_deactivate_already_inactive_user_succeeds(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "already_inactive@test.com", is_active=False)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200


def test_grant_admin_to_already_admin_succeeds(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "already_admin@test.com", is_admin=True)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_admin": True},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200


def test_partial_update_only_is_active(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "partial_active@test.com", is_active=True, is_admin=False)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
    assert data["is_admin"] is False  # unchanged


def test_partial_update_only_is_admin(client, admin_auth_token, test_session):
    user = _create_test_user(test_session, "partial_admin@test.com", is_active=True, is_admin=False)
    response = client.patch(
        f"/api/admin/users/{user.id}",
        json={"is_admin": True},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_admin"] is True
    assert data["is_active"] is True  # unchanged


def test_combined_update_with_self_protection_blocks_entirely(client, admin_auth_token, admin_user):
    response = client.patch(
        f"/api/admin/users/{admin_user.id}",
        json={"is_active": False, "is_admin": True},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
