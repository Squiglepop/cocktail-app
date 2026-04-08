"""
Tests for admin user list endpoint (Story 3-1).
"""
from datetime import datetime, timedelta

from app.models.recipe import Recipe
from app.models.user import User
from app.services.auth import hash_password


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


def _create_test_recipe(test_session, user_id, name="Test Recipe"):
    """Helper to create a recipe owned by user for recipe_count verification."""
    recipe = Recipe(
        name=name,
        user_id=user_id,
        source_type="manual",
    )
    test_session.add(recipe)
    test_session.commit()
    return recipe


# --- AC-6: Auth tests (MANDATORY) ---


def test_list_users_returns_401_without_auth(client):
    response = client.get("/api/admin/users")
    assert response.status_code == 401


def test_list_users_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- AC-1: Happy path tests ---


def test_list_users_returns_paginated_response(client, admin_auth_token, admin_user):
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


def test_list_users_includes_all_required_fields(client, admin_auth_token, admin_user):
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    user_item = data["items"][0]
    required_fields = {"id", "email", "display_name", "is_active", "is_admin", "recipe_count", "created_at", "last_login_at"}
    assert required_fields <= set(user_item.keys())


def test_list_users_includes_recipe_count(client, admin_auth_token, admin_user, test_session):
    _create_test_recipe(test_session, admin_user.id, "Recipe A")
    _create_test_recipe(test_session, admin_user.id, "Recipe B")

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    admin_item = next(u for u in data["items"] if u["id"] == admin_user.id)
    assert admin_item["recipe_count"] == 2


# --- AC-2: Pagination tests ---


def test_list_users_respects_page_and_per_page(client, admin_auth_token, admin_user, test_session):
    for i in range(5):
        _create_test_user(test_session, f"page_user_{i}@test.com", f"Page User {i}")

    response = client.get(
        "/api/admin/users?page=1&per_page=2",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["per_page"] == 2

    response2 = client.get(
        "/api/admin/users?page=2&per_page=2",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data2 = response2.json()
    assert len(data2["items"]) == 2
    assert data2["page"] == 2


def test_list_users_returns_correct_total(client, admin_auth_token, admin_user, test_session):
    # Get baseline count
    baseline = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    ).json()["total"]

    for i in range(3):
        _create_test_user(test_session, f"total_user_{i}@test.com")

    response = client.get(
        "/api/admin/users?per_page=2",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == baseline + 3
    assert len(data["items"]) == 2


# --- AC-3: Search tests ---


def test_list_users_search_by_email(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "findme@search.com", "Findme User")
    _create_test_user(test_session, "other@nope.com", "Other User")

    response = client.get(
        "/api/admin/users?search=findme",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    emails = [u["email"] for u in data["items"]]
    assert "findme@search.com" in emails
    assert "other@nope.com" not in emails


def test_list_users_search_by_display_name(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "user1@test.com", "John Smith")
    _create_test_user(test_session, "user2@test.com", "Jane Doe")

    response = client.get(
        "/api/admin/users?search=john",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    names = [u["display_name"] for u in data["items"]]
    assert "John Smith" in names
    assert "Jane Doe" not in names


def test_list_users_search_is_case_insensitive(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "CamelCase@Test.com", "CamelCase User")

    response = client.get(
        "/api/admin/users?search=camelcase",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    emails = [u["email"] for u in data["items"]]
    assert "CamelCase@Test.com" in emails


# --- AC-4, AC-5: Status filter tests ---


def test_list_users_filter_active_only(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "active@test.com", is_active=True)
    _create_test_user(test_session, "deactivated@test.com", is_active=False)

    response = client.get(
        "/api/admin/users?status=active",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(u["is_active"] for u in data["items"])
    emails = [u["email"] for u in data["items"]]
    assert "deactivated@test.com" not in emails


def test_list_users_filter_inactive_only(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "active2@test.com", is_active=True)
    _create_test_user(test_session, "inactive2@test.com", is_active=False)

    response = client.get(
        "/api/admin/users?status=inactive",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(not u["is_active"] for u in data["items"])
    emails = [u["email"] for u in data["items"]]
    assert "active2@test.com" not in emails


def test_list_users_invalid_status_returns_400(client, admin_auth_token, admin_user):
    response = client.get(
        "/api/admin/users?status=banned",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "Invalid status" in response.json()["detail"]


# --- Combined filter tests ---


def test_list_users_search_with_status_filter(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "combo_active@test.com", "Combo Active", is_active=True)
    _create_test_user(test_session, "combo_inactive@test.com", "Combo Inactive", is_active=False)

    response = client.get(
        "/api/admin/users?search=combo&status=active",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["email"] == "combo_active@test.com"


def test_list_users_default_pagination_params(client, admin_auth_token, admin_user):
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["per_page"] == 50


# --- Edge case tests ---


def test_list_users_empty_search_returns_all(client, admin_auth_token, admin_user, test_session):
    baseline = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    ).json()["total"]

    _create_test_user(test_session, "edge1@test.com")

    response = client.get(
        "/api/admin/users?search=",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == baseline + 1


def test_list_users_no_results_returns_empty_list(client, admin_auth_token, admin_user):
    response = client.get(
        "/api/admin/users?search=nonexistentuserxyz",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


# --- Recipe count accuracy ---


def test_list_users_recipe_count_reflects_actual_count(client, admin_auth_token, admin_user, test_session):
    user = _create_test_user(test_session, "recipes@test.com", "Recipe User")
    _create_test_recipe(test_session, user.id, "Recipe 1")
    _create_test_recipe(test_session, user.id, "Recipe 2")
    _create_test_recipe(test_session, user.id, "Recipe 3")

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    recipe_user = next(u for u in data["items"] if u["email"] == "recipes@test.com")
    assert recipe_user["recipe_count"] == 3
    admin_item = next(u for u in data["items"] if u["id"] == admin_user.id)
    assert admin_item["recipe_count"] == 0


# --- M1: LIKE wildcard escaping tests ---


def test_list_users_search_escapes_percent_wildcard(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "normal@test.com", "Normal User")
    _create_test_user(test_session, "percent%user@test.com", "Percent User")

    response = client.get(
        "/api/admin/users?search=%25",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    emails = [u["email"] for u in data["items"]]
    assert "percent%user@test.com" in emails
    assert "normal@test.com" not in emails


def test_list_users_search_escapes_underscore_wildcard(client, admin_auth_token, admin_user, test_session):
    _create_test_user(test_session, "a_b@test.com", "Underscore User")
    _create_test_user(test_session, "axb@test.com", "No Underscore")

    response = client.get(
        "/api/admin/users?search=a_b",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    emails = [u["email"] for u in data["items"]]
    assert "a_b@test.com" in emails
    assert "axb@test.com" not in emails


# --- M3: Sort order verification ---


def test_list_users_ordered_by_created_at_desc(client, admin_auth_token, admin_user, test_session):
    now = datetime.utcnow()
    older = _create_test_user(test_session, "older@test.com", "Older")
    older.created_at = now - timedelta(days=10)
    newer = _create_test_user(test_session, "newer@test.com", "Newer")
    newer.created_at = now + timedelta(days=1)
    test_session.commit()

    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    emails = [u["email"] for u in data["items"]]
    assert emails.index("newer@test.com") < emails.index("older@test.com")


# --- L1: Boundary validation tests ---


def test_list_users_per_page_over_100_returns_422(client, admin_auth_token, admin_user):
    response = client.get(
        "/api/admin/users?per_page=101",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422


def test_list_users_page_zero_returns_422(client, admin_auth_token, admin_user):
    response = client.get(
        "/api/admin/users?page=0",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422
