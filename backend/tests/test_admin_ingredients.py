"""
Tests for admin ingredient CRUD endpoints (Story 2-1).
"""
import pytest
from unittest.mock import patch
from sqlalchemy.exc import IntegrityError
from app.models.recipe import Ingredient


# --- Auth Tests (AC-8) ---


def test_list_ingredients_returns_401_without_auth(client):
    response = client.get("/api/admin/ingredients")
    assert response.status_code == 401


def test_list_ingredients_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        "/api/admin/ingredients",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


def test_create_ingredient_returns_401_without_auth(client):
    response = client.post("/api/admin/ingredients", json={"name": "Vodka", "type": "spirit"})
    assert response.status_code == 401


def test_create_ingredient_returns_403_for_regular_user(client, auth_token):
    response = client.post(
        "/api/admin/ingredients",
        json={"name": "Vodka", "type": "spirit"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


def test_update_ingredient_returns_401_without_auth(client):
    response = client.put("/api/admin/ingredients/fake-id", json={"name": "Updated"})
    assert response.status_code == 401


def test_update_ingredient_returns_403_for_regular_user(client, auth_token):
    response = client.put(
        "/api/admin/ingredients/fake-id",
        json={"name": "Updated"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


def test_delete_ingredient_returns_401_without_auth(client):
    response = client.delete("/api/admin/ingredients/fake-id")
    assert response.status_code == 401


def test_delete_ingredient_returns_403_for_regular_user(client, auth_token):
    response = client.delete(
        "/api/admin/ingredients/fake-id",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- GET /admin/ingredients (List) Tests (AC-1, AC-2) ---


def test_list_ingredients_returns_paginated_results(client, admin_auth_token, sample_ingredient):
    response = client.get(
        "/api/admin/ingredients",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["per_page"] == 50
    assert len(data["items"]) >= 1
    item = next(i for i in data["items"] if i["id"] == sample_ingredient.id)
    assert item["name"] == "Tequila"
    assert item["type"] == "spirit"
    assert item["spirit_category"] == "tequila"


def test_list_ingredients_search_by_name(client, admin_auth_token, sample_ingredient):
    response = client.get(
        "/api/admin/ingredients?search=tequ",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(i["name"] == "Tequila" for i in data["items"])


def test_list_ingredients_filter_by_type(client, admin_auth_token, sample_ingredient):
    response = client.get(
        "/api/admin/ingredients?type=spirit",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(i["type"] == "spirit" for i in data["items"])


def test_list_ingredients_pagination_metadata(client, admin_auth_token, sample_ingredient):
    response = client.get(
        "/api/admin/ingredients?page=1&per_page=1",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["per_page"] == 1
    assert len(data["items"]) <= 1


def test_list_ingredients_invalid_type_returns_400(client, admin_auth_token):
    response = client.get(
        "/api/admin/ingredients?type=banana_hammock",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "Invalid ingredient type" in response.json()["detail"]


def test_list_ingredients_search_escapes_wildcards(client, admin_auth_token, test_session):
    ingredient = Ingredient(name="100% Agave Tequila", type="spirit")
    test_session.add(ingredient)
    test_session.commit()

    response = client.get(
        "/api/admin/ingredients?search=%25",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    names = [i["name"] for i in data["items"]]
    assert "100% Agave Tequila" in names
    # Should only match ingredients with literal %, not everything
    assert data["total"] == 1


def test_list_ingredients_empty_search_returns_all(client, admin_auth_token, sample_ingredient):
    response = client.get(
        "/api/admin/ingredients?search=",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_list_ingredients_search_and_type_combined(client, admin_auth_token, test_session):
    spirit = Ingredient(name="Dark Rum", type="spirit", spirit_category="rum")
    juice = Ingredient(name="Rum Raisin Syrup", type="syrup")
    test_session.add_all([spirit, juice])
    test_session.commit()

    response = client.get(
        "/api/admin/ingredients?search=rum&type=spirit",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert all(i["type"] == "spirit" for i in data["items"])
    assert any(i["name"] == "Dark Rum" for i in data["items"])
    assert not any(i["name"] == "Rum Raisin Syrup" for i in data["items"])


# --- Auth Tests for GET /admin/ingredients/{id} (AC-8) ---


def test_get_ingredient_returns_401_without_auth(client):
    response = client.get("/api/admin/ingredients/fake-id")
    assert response.status_code == 401


def test_get_ingredient_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        "/api/admin/ingredients/fake-id",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- GET /admin/ingredients/{id} (Single) Tests (AC-6.5) ---


def test_get_ingredient_by_id(client, admin_auth_token, sample_ingredient):
    response = client.get(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_ingredient.id
    assert data["name"] == "Tequila"
    assert data["type"] == "spirit"
    assert data["spirit_category"] == "tequila"
    assert data["description"] == "A distilled spirit made from blue agave"


def test_get_nonexistent_ingredient_returns_404(client, admin_auth_token):
    response = client.get(
        "/api/admin/ingredients/nonexistent-id",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Ingredient not found"


# --- POST /admin/ingredients (Create) Tests (AC-3, AC-4) ---


def test_create_ingredient_returns_201(client, admin_auth_token):
    response = client.post(
        "/api/admin/ingredients",
        json={"name": "Fresh Lime Juice", "type": "juice"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Fresh Lime Juice"
    assert data["type"] == "juice"
    assert "id" in data


def test_create_ingredient_with_all_fields(client, admin_auth_token):
    response = client.post(
        "/api/admin/ingredients",
        json={
            "name": "Bourbon",
            "type": "spirit",
            "spirit_category": "bourbon",
            "description": "American whiskey aged in charred oak barrels",
            "common_brands": "Maker's Mark, Woodford Reserve, Buffalo Trace",
        },
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Bourbon"
    assert data["type"] == "spirit"
    assert data["spirit_category"] == "bourbon"
    assert data["description"] == "American whiskey aged in charred oak barrels"
    assert data["common_brands"] == "Maker's Mark, Woodford Reserve, Buffalo Trace"


def test_create_duplicate_name_returns_409(client, admin_auth_token, sample_ingredient):
    response = client.post(
        "/api/admin/ingredients",
        json={"name": "Tequila", "type": "spirit"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 409


def test_create_duplicate_name_case_insensitive_returns_409(client, admin_auth_token, sample_ingredient):
    response = client.post(
        "/api/admin/ingredients",
        json={"name": "tEqUiLa", "type": "spirit"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 409


def test_create_ingredient_with_invalid_type_returns_422(client, admin_auth_token):
    response = client.post(
        "/api/admin/ingredients",
        json={"name": "Something", "type": "invalid_type"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422


# --- PUT /admin/ingredients/{id} (Update) Tests (AC-5) ---


def test_update_ingredient_name(client, admin_auth_token, sample_ingredient):
    response = client.put(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        json={"name": "Blanco Tequila"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Blanco Tequila"
    assert data["type"] == "spirit"


def test_update_ingredient_type(client, admin_auth_token, sample_ingredient):
    response = client.put(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        json={"type": "liqueur"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["type"] == "liqueur"


def test_update_nonexistent_returns_404(client, admin_auth_token):
    response = client.put(
        "/api/admin/ingredients/nonexistent-id",
        json={"name": "Whatever"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404


def test_update_to_duplicate_name_returns_409(client, admin_auth_token, test_session, sample_ingredient):
    other = Ingredient(name="Vodka", type="spirit")
    test_session.add(other)
    test_session.commit()
    test_session.refresh(other)

    response = client.put(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        json={"name": "vodka"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 409


def test_update_ingredient_partial_fields(client, admin_auth_token, sample_ingredient):
    response = client.put(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        json={"description": "Updated description only"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == "Updated description only"
    assert data["name"] == "Tequila"
    assert data["type"] == "spirit"
    assert data["spirit_category"] == "tequila"


# --- DELETE /admin/ingredients/{id} Tests (AC-6, AC-7) ---


def test_delete_unused_ingredient_succeeds(client, admin_auth_token, test_session):
    ingredient = Ingredient(name="Unused Herb", type="garnish")
    test_session.add(ingredient)
    test_session.commit()
    test_session.refresh(ingredient)

    response = client.delete(
        f"/api/admin/ingredients/{ingredient.id}",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "deleted" in data["message"].lower() or "Unused Herb" in data["message"]
    assert data["recipe_count"] == 0


def test_delete_used_ingredient_returns_409_with_count(client, admin_auth_token, sample_recipe, sample_ingredient):
    response = client.delete(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["recipe_count"] >= 1


def test_delete_nonexistent_returns_404(client, admin_auth_token):
    response = client.delete(
        "/api/admin/ingredients/nonexistent-id",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404


# --- IntegrityError Race Condition Fallback Tests ---


def test_create_ingredient_integrity_error_fallback_returns_409(
    client, admin_auth_token, test_session,
):
    """Race condition: duplicate check passes but commit hits unique constraint."""
    original_commit = test_session.commit

    call_count = 0

    def commit_that_fails_once():
        nonlocal call_count
        call_count += 1
        # Let fixture commits through; fail on the create commit
        if call_count >= 1:
            # First, sneakily insert the duplicate so the constraint fires
            test_session.rollback()
            raise IntegrityError("duplicate", {}, None)
        original_commit()

    with patch.object(test_session, "commit", side_effect=commit_that_fails_once):
        response = client.post(
            "/api/admin/ingredients",
            json={"name": "Race Condition Spirit", "type": "spirit"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
    assert response.status_code == 409


def test_update_ingredient_integrity_error_fallback_returns_409(
    client, admin_auth_token, test_session, sample_ingredient,
):
    """Race condition: name uniqueness check passes but commit hits constraint."""
    def commit_that_fails():
        test_session.rollback()
        raise IntegrityError("duplicate", {}, None)

    # Create another ingredient to update
    other = Ingredient(name="Gin", type="spirit")
    test_session.add(other)
    test_session.commit()

    with patch.object(test_session, "commit", side_effect=commit_that_fails):
        response = client.put(
            f"/api/admin/ingredients/{other.id}",
            json={"name": "Unique But Races"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
    assert response.status_code == 409


def test_delete_ingredient_integrity_error_returns_409(
    client, admin_auth_token, test_session,
):
    """Race condition: usage count is 0 but a recipe links before commit."""
    ingredient = Ingredient(name="Soon Used", type="garnish")
    test_session.add(ingredient)
    test_session.commit()
    test_session.refresh(ingredient)

    def commit_that_fails():
        test_session.rollback()
        raise IntegrityError("fk constraint", {}, None)

    with patch.object(test_session, "commit", side_effect=commit_that_fails):
        response = client.delete(
            f"/api/admin/ingredients/{ingredient.id}",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
    assert response.status_code == 409


# --- H1 Fix: Null required field rejection tests ---


def test_update_ingredient_with_null_name_returns_422(client, admin_auth_token, sample_ingredient):
    """Sending name=null should be rejected by schema validation, not hit the DB."""
    response = client.put(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        json={"name": None},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422


def test_update_ingredient_with_null_type_returns_422(client, admin_auth_token, sample_ingredient):
    """Sending type=null should be rejected by schema validation."""
    response = client.put(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        json={"type": None},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422


# --- L2: Empty update body no-op test ---


def test_update_ingredient_empty_body_returns_unchanged(client, admin_auth_token, sample_ingredient):
    """Sending {} should return 200 with the ingredient unchanged."""
    response = client.put(
        f"/api/admin/ingredients/{sample_ingredient.id}",
        json={},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tequila"
    assert data["type"] == "spirit"
    assert data["spirit_category"] == "tequila"
