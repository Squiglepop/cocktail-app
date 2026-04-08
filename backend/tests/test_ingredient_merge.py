"""
Tests for ingredient merge endpoint (Story 2-3).
"""
from unittest.mock import patch

from app.models.recipe import Ingredient, Recipe, RecipeIngredient


MERGE_URL = "/api/admin/ingredients/merge"


def _create_ingredient(client, admin_auth_token, name, type="spirit"):
    """Helper to create an ingredient via API."""
    resp = client.post(
        "/api/admin/ingredients",
        json={"name": name, "type": type},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert resp.status_code == 201
    return resp.json()


def _link_ingredient_to_recipe(test_session, recipe_id, ingredient_id, amount=1.0, unit="oz"):
    """Helper to create a RecipeIngredient directly in DB."""
    ri = RecipeIngredient(
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
        amount=amount,
        unit=unit,
        order=0,
    )
    test_session.add(ri)
    test_session.commit()
    return ri


def _create_recipe(test_session, user, name="Test Cocktail"):
    """Helper to create a minimal recipe."""
    recipe = Recipe(
        name=name,
        instructions="Shake and strain.",
        source_type="manual",
        user_id=user.id,
    )
    test_session.add(recipe)
    test_session.commit()
    test_session.refresh(recipe)
    return recipe


# --- Auth Tests (AC-7) ---


def test_merge_returns_401_without_auth(client):
    response = client.post(MERGE_URL, json={
        "source_ids": ["fake-id"],
        "target_id": "fake-target",
    })
    assert response.status_code == 401


def test_merge_returns_403_for_regular_user(client, auth_token):
    response = client.post(
        MERGE_URL,
        json={"source_ids": ["fake-id"], "target_id": "fake-target"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- Validation Tests (AC-5, AC-6, AC-8, AC-9) ---


def test_merge_returns_422_with_empty_source_ids(client, admin_auth_token):
    response = client.post(
        MERGE_URL,
        json={"source_ids": [], "target_id": "fake-target"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422


def test_merge_returns_404_when_target_not_found(client, admin_auth_token):
    response = client.post(
        MERGE_URL,
        json={"source_ids": ["fake-source"], "target_id": "nonexistent-target"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_merge_returns_400_when_source_contains_target(client, admin_auth_token):
    target = _create_ingredient(client, admin_auth_token, "Merge Target Vodka")
    target_id = target["id"]
    response = client.post(
        MERGE_URL,
        json={"source_ids": [target_id], "target_id": target_id},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "cannot merge" in response.json()["detail"].lower()


def test_merge_returns_404_when_source_id_not_found(client, admin_auth_token):
    target = _create_ingredient(client, admin_auth_token, "Merge Target Gin")
    response = client.post(
        MERGE_URL,
        json={"source_ids": ["nonexistent-source-1", "nonexistent-source-2"], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert "nonexistent-source-1" in detail
    assert "nonexistent-source-2" in detail


# --- Happy Path Tests (AC-1, AC-2) ---


def test_merge_updates_recipe_ingredients_to_target(
    client, admin_auth_token, test_session, sample_user,
):
    target = _create_ingredient(client, admin_auth_token, "Target Rum")
    source = _create_ingredient(client, admin_auth_token, "Source Rum")
    recipe = _create_recipe(test_session, sample_user, "Daiquiri")
    _link_ingredient_to_recipe(test_session, recipe.id, source["id"])

    response = client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200

    # Verify the recipe now references the target
    ri = test_session.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe.id,
        RecipeIngredient.ingredient_id == target["id"],
    ).first()
    assert ri is not None


def test_merge_deletes_source_ingredients(
    client, admin_auth_token, test_session, sample_user,
):
    target = _create_ingredient(client, admin_auth_token, "Target Whiskey")
    source = _create_ingredient(client, admin_auth_token, "Source Whiskey")

    response = client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200

    # Source should be gone
    deleted = test_session.query(Ingredient).filter(Ingredient.id == source["id"]).first()
    assert deleted is None


def test_merge_returns_correct_recipes_affected_count(
    client, admin_auth_token, test_session, sample_user,
):
    target = _create_ingredient(client, admin_auth_token, "Target Tequila")
    source = _create_ingredient(client, admin_auth_token, "Source Tequila")
    r1 = _create_recipe(test_session, sample_user, "Margarita 2")
    r2 = _create_recipe(test_session, sample_user, "Paloma 2")
    _link_ingredient_to_recipe(test_session, r1.id, source["id"])
    _link_ingredient_to_recipe(test_session, r2.id, source["id"])

    response = client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recipes_affected"] == 2


def test_merge_returns_correct_sources_removed_count(
    client, admin_auth_token, test_session,
):
    target = _create_ingredient(client, admin_auth_token, "Target Brandy")
    s1 = _create_ingredient(client, admin_auth_token, "Source Brandy 1")
    s2 = _create_ingredient(client, admin_auth_token, "Source Brandy 2")

    response = client.post(
        MERGE_URL,
        json={"source_ids": [s1["id"], s2["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["sources_removed"] == 2


# --- Same-Recipe Edge Case Tests (AC-3) ---


def test_merge_handles_same_recipe_with_source_and_target(
    client, admin_auth_token, test_session, sample_user,
):
    target = _create_ingredient(client, admin_auth_token, "Target Lime Juice")
    source = _create_ingredient(client, admin_auth_token, "Source Lime Juice")
    recipe = _create_recipe(test_session, sample_user, "Gimlet Overlap")

    # Recipe has BOTH target and source
    _link_ingredient_to_recipe(test_session, recipe.id, target["id"])
    _link_ingredient_to_recipe(test_session, recipe.id, source["id"])

    response = client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200

    # Should NOT have duplicate rows — source row deleted, target row remains
    ri_rows = test_session.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe.id,
        RecipeIngredient.ingredient_id == target["id"],
    ).all()
    assert len(ri_rows) == 1


def test_merge_recipe_retains_target_after_overlap_merge(
    client, admin_auth_token, test_session, sample_user,
):
    target = _create_ingredient(client, admin_auth_token, "Target Simple Syrup")
    source = _create_ingredient(client, admin_auth_token, "Source Simple Syrup")
    recipe = _create_recipe(test_session, sample_user, "Daiquiri Overlap")

    _link_ingredient_to_recipe(test_session, recipe.id, target["id"])
    _link_ingredient_to_recipe(test_session, recipe.id, source["id"])

    client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    # Target ingredient still linked to recipe
    ri = test_session.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe.id,
        RecipeIngredient.ingredient_id == target["id"],
    ).first()
    assert ri is not None


# --- Multi-Source Tests ---


def test_merge_multiple_sources_into_target(
    client, admin_auth_token, test_session, sample_user,
):
    target = _create_ingredient(client, admin_auth_token, "Target Bitters")
    s1 = _create_ingredient(client, admin_auth_token, "Source Bitters A")
    s2 = _create_ingredient(client, admin_auth_token, "Source Bitters B")
    r1 = _create_recipe(test_session, sample_user, "Old Fashioned Multi")
    r2 = _create_recipe(test_session, sample_user, "Manhattan Multi")

    _link_ingredient_to_recipe(test_session, r1.id, s1["id"])
    _link_ingredient_to_recipe(test_session, r2.id, s2["id"])

    response = client.post(
        MERGE_URL,
        json={"source_ids": [s1["id"], s2["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recipes_affected"] == 2
    assert data["sources_removed"] == 2

    # Both sources gone
    assert test_session.query(Ingredient).filter(Ingredient.id == s1["id"]).first() is None
    assert test_session.query(Ingredient).filter(Ingredient.id == s2["id"]).first() is None

    # Both recipes now point to target
    for r in [r1, r2]:
        ri = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == r.id,
            RecipeIngredient.ingredient_id == target["id"],
        ).first()
        assert ri is not None


def test_merge_sources_with_no_recipe_usage(
    client, admin_auth_token, test_session,
):
    target = _create_ingredient(client, admin_auth_token, "Target Absinthe")
    source = _create_ingredient(client, admin_auth_token, "Source Absinthe")

    response = client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recipes_affected"] == 0
    assert data["sources_removed"] == 1

    # Source still deleted
    assert test_session.query(Ingredient).filter(Ingredient.id == source["id"]).first() is None


# --- Data Integrity Tests (AC-2) ---


def test_merge_preserves_unrelated_recipe_ingredients(
    client, admin_auth_token, test_session, sample_user,
):
    target = _create_ingredient(client, admin_auth_token, "Target Vodka DI")
    source = _create_ingredient(client, admin_auth_token, "Source Vodka DI")
    unrelated = _create_ingredient(client, admin_auth_token, "Unrelated Garnish", type="garnish")

    recipe = _create_recipe(test_session, sample_user, "Cosmopolitan DI")
    _link_ingredient_to_recipe(test_session, recipe.id, source["id"])
    _link_ingredient_to_recipe(test_session, recipe.id, unrelated["id"])

    client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    # Unrelated ingredient still there
    ri = test_session.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe.id,
        RecipeIngredient.ingredient_id == unrelated["id"],
    ).first()
    assert ri is not None


def test_target_ingredient_unchanged_after_merge(
    client, admin_auth_token, test_session,
):
    target = _create_ingredient(client, admin_auth_token, "Target Mezcal")
    source = _create_ingredient(client, admin_auth_token, "Source Mezcal")

    client.post(
        MERGE_URL,
        json={"source_ids": [source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )

    # Target still exists with original attributes
    t = test_session.query(Ingredient).filter(Ingredient.id == target["id"]).first()
    assert t is not None
    assert t.name == "Target Mezcal"
    assert t.type == "spirit"


# --- Transaction Rollback Test (AC-4) ---


def test_merge_rolls_back_on_failure(
    client, admin_auth_token, test_session, sample_user,
):
    """Verify entire merge rolls back if commit fails — no data modified."""
    target = _create_ingredient(client, admin_auth_token, "Target Rollback Rum")
    source = _create_ingredient(client, admin_auth_token, "Source Rollback Rum")
    recipe = _create_recipe(test_session, sample_user, "Rollback Daiquiri")
    _link_ingredient_to_recipe(test_session, recipe.id, source["id"])

    original_commit = test_session.commit

    call_count = 0

    def commit_that_fails_on_merge():
        nonlocal call_count
        call_count += 1
        # Let setup commits through; fail on the merge's commit
        # The merge commit is the one that happens after flush + deletes
        if call_count > 0:
            # Check if we're inside the merge (source RI rows already flushed)
            pending_deletes = [
                obj for obj in test_session.deleted
                if isinstance(obj, Ingredient) and obj.id == source["id"]
            ]
            if pending_deletes:
                test_session.rollback()
                raise RuntimeError("simulated DB failure")
        original_commit()

    with patch.object(test_session, "commit", side_effect=commit_that_fails_on_merge):
        try:
            client.post(
                MERGE_URL,
                json={"source_ids": [source["id"]], "target_id": target["id"]},
                headers={"Authorization": f"Bearer {admin_auth_token}"},
            )
        except RuntimeError:
            pass  # Expected — TestClient re-raises unhandled exceptions

    # Expire cached state so we read fresh from DB
    test_session.expire_all()

    # Source ingredient still exists (not deleted)
    source_ing = test_session.query(Ingredient).filter(
        Ingredient.id == source["id"]
    ).first()
    assert source_ing is not None

    # RecipeIngredient still points to source (not updated)
    ri = test_session.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe.id,
        RecipeIngredient.ingredient_id == source["id"],
    ).first()
    assert ri is not None


# --- Duplicate Source ID Deduplication Test ---


def test_merge_deduplicates_source_ids(
    client, admin_auth_token, test_session,
):
    """Verify duplicate source_ids are deduplicated by schema validation."""
    target = _create_ingredient(client, admin_auth_token, "Target Dedup Gin")
    source = _create_ingredient(client, admin_auth_token, "Source Dedup Gin")

    response = client.post(
        MERGE_URL,
        json={"source_ids": [source["id"], source["id"]], "target_id": target["id"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["sources_removed"] == 1
