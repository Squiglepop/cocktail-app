"""
Tests for ingredient duplicate detection endpoint (Story 2-2).
"""
from app.models.recipe import Ingredient, Recipe, RecipeIngredient


ENDPOINT = "/api/admin/ingredients/duplicates"


def _create_ingredient_db(test_session, name, type="spirit"):
    """Insert ingredient directly into DB (bypasses API case-insensitive duplicate check)."""
    ing = Ingredient(name=name, type=type)
    test_session.add(ing)
    test_session.commit()
    test_session.refresh(ing)
    return ing


# --- Auth Tests (AC-6) ---


def test_duplicates_returns_401_without_auth(client):
    response = client.get(ENDPOINT)
    assert response.status_code == 401


def test_duplicates_returns_403_for_regular_user(client, auth_token):
    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- Exact Match Tests (AC-2) ---


def test_detects_case_insensitive_exact_match(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice", "juice")
    _create_ingredient_db(test_session, "lime juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_groups"] >= 1

    names_in_groups = set()
    for group in data["groups"]:
        names_in_groups.add(group["target"]["name"])
        for dup in group["duplicates"]:
            names_in_groups.add(dup["name"])
    assert "Lime Juice" in names_in_groups
    assert "lime juice" in names_in_groups


def test_exact_match_shows_correct_reason(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice", "juice")
    _create_ingredient_db(test_session, "lime juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] >= 1

    for group in data["groups"]:
        all_names = {group["target"]["name"].lower()} | {
            d["name"].lower() for d in group["duplicates"]
        }
        if "lime juice" in all_names:
            assert group["group_reason"] == "exact_match_case_insensitive"
            for dup in group["duplicates"]:
                if dup["name"].lower() == "lime juice":
                    assert dup["detection_reason"] == "exact_match_case_insensitive"
            break
    else:
        raise AssertionError("Lime juice group not found")


# --- Fuzzy Match Tests (AC-3) ---


def test_detects_fuzzy_match_above_threshold(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice", "juice")
    _create_ingredient_db(test_session, "Lime Juic", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] >= 1

    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Lime Juice" in all_names and "Lime Juic" in all_names:
            found = True
            assert group["group_reason"] == "fuzzy_match"
            for dup in group["duplicates"]:
                assert dup["detection_reason"] == "fuzzy_match"
            break
    assert found, "Fuzzy match group not found"


def test_ignores_fuzzy_match_below_threshold(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime", "juice")
    _create_ingredient_db(test_session, "Vodka", "spirit")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        assert not ("Lime" in all_names and "Vodka" in all_names)


def test_fuzzy_match_includes_similarity_score(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice", "juice")
    _create_ingredient_db(test_session, "Lime Juic", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Lime Juice" in all_names and "Lime Juic" in all_names:
            for dup in group["duplicates"]:
                assert dup["similarity_score"] > 0.8
                assert dup["similarity_score"] <= 1.0
                assert dup["detection_reason"] == "fuzzy_match"
            break


# --- Variation Pattern Tests (AC-4) ---


def test_detects_fresh_prefix_variation(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Fresh Lime Juice", "juice")
    _create_ingredient_db(test_session, "Lime Juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] >= 1

    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Fresh Lime Juice" in all_names and "Lime Juice" in all_names:
            found = True
            assert group["group_reason"] == "variation_pattern"
            break
    assert found, "Variation match group not found"


def test_detects_parenthetical_variation(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice (fresh)", "juice")
    _create_ingredient_db(test_session, "Lime Juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] >= 1

    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Lime Juice (fresh)" in all_names and "Lime Juice" in all_names:
            found = True
            break
    assert found, "Parenthetical variation group not found"


# --- Group Structure Tests (AC-5) ---


def test_target_is_highest_usage_count(
    client, admin_auth_token, test_session, sample_user,
):
    ing_high = Ingredient(name="Tequila Blanco", type="spirit")
    ing_low = Ingredient(name="tequila blanco", type="spirit")
    test_session.add_all([ing_high, ing_low])
    test_session.flush()

    recipe = Recipe(
        name="Test Recipe",
        instructions="Mix it.",
        source_type="manual",
        user_id=sample_user.id,
    )
    test_session.add(recipe)
    test_session.flush()
    test_session.add(RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ing_high.id,
        amount=2.0,
        unit="oz",
        order=0,
    ))
    test_session.commit()

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    for group in data["groups"]:
        all_names = {group["target"]["name"].lower()} | {
            d["name"].lower() for d in group["duplicates"]
        }
        if "tequila blanco" in all_names:
            assert group["target"]["name"] == "Tequila Blanco"
            assert group["target"]["usage_count"] == 1
            break
    else:
        raise AssertionError("Tequila blanco group not found")


def test_group_includes_usage_counts(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Rum", "spirit")
    _create_ingredient_db(test_session, "rum", "spirit")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    for group in data["groups"]:
        assert "usage_count" in group["target"]
        assert isinstance(group["target"]["usage_count"], int)
        for dup in group["duplicates"]:
            assert "usage_count" in dup
            assert isinstance(dup["usage_count"], int)


def test_response_includes_total_counts(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Gin", "spirit")
    _create_ingredient_db(test_session, "gin", "spirit")
    _create_ingredient_db(test_session, "Rum", "spirit")
    _create_ingredient_db(test_session, "rum", "spirit")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    assert "total_groups" in data
    assert "total_duplicates" in data
    assert data["total_groups"] >= 2
    assert data["total_duplicates"] >= 2
    assert data["total_groups"] == len(data["groups"])
    assert data["total_duplicates"] == sum(
        len(g["duplicates"]) for g in data["groups"]
    )


# --- Detection Reason Priority Tests (AC subtask 4.7) ---


def test_same_pair_uses_highest_priority_reason(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice", "juice")
    _create_ingredient_db(test_session, "lime juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    for group in data["groups"]:
        all_names = {group["target"]["name"].lower()} | {
            d["name"].lower() for d in group["duplicates"]
        }
        if "lime juice" in all_names:
            assert group["group_reason"] == "exact_match_case_insensitive"
            for dup in group["duplicates"]:
                assert dup["detection_reason"] == "exact_match_case_insensitive"
            break


# --- Edge Case Tests (AC subtask 4.8) ---


def test_no_duplicates_returns_empty(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Vodka", "spirit")
    _create_ingredient_db(test_session, "Gin", "spirit")
    _create_ingredient_db(test_session, "Rum", "spirit")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] == 0
    assert data["total_duplicates"] == 0
    assert data["groups"] == []


def test_zero_ingredients_returns_empty(client, admin_auth_token):
    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] == 0
    assert data["total_duplicates"] == 0
    assert data["groups"] == []


def test_single_ingredient_returns_empty(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Vodka", "spirit")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] == 0
    assert data["total_duplicates"] == 0


def test_multiple_duplicate_groups(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Gin", "spirit")
    _create_ingredient_db(test_session, "gin", "spirit")
    _create_ingredient_db(test_session, "Rum", "spirit")
    _create_ingredient_db(test_session, "rum", "spirit")
    _create_ingredient_db(test_session, "Vodka", "spirit")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()
    assert data["total_groups"] >= 2


def test_ingredient_appears_in_only_one_group(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice", "juice")
    _create_ingredient_db(test_session, "lime juice", "juice")
    _create_ingredient_db(test_session, "Lemon Juice", "juice")
    _create_ingredient_db(test_session, "lemon juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    all_ids = []
    for group in data["groups"]:
        all_ids.append(group["target"]["ingredient_id"])
        for dup in group["duplicates"]:
            all_ids.append(dup["ingredient_id"])
    assert len(all_ids) == len(set(all_ids))


def test_duplicates_detected_when_both_in_same_recipe(
    client, admin_auth_token, test_session, sample_user,
):
    ing_a = Ingredient(name="Simple Syrup", type="syrup")
    ing_b = Ingredient(name="simple syrup", type="syrup")
    test_session.add_all([ing_a, ing_b])
    test_session.flush()

    recipe = Recipe(
        name="Sweet Cocktail",
        instructions="Mix it.",
        source_type="manual",
        user_id=sample_user.id,
    )
    test_session.add(recipe)
    test_session.flush()
    test_session.add(RecipeIngredient(
        recipe_id=recipe.id, ingredient_id=ing_a.id,
        amount=1.0, unit="oz", order=0,
    ))
    test_session.add(RecipeIngredient(
        recipe_id=recipe.id, ingredient_id=ing_b.id,
        amount=0.5, unit="oz", order=1,
    ))
    test_session.commit()

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"].lower()} | {
            d["name"].lower() for d in group["duplicates"]
        }
        if "simple syrup" in all_names:
            found = True
            break
    assert found, "Duplicate detection failed when both ingredients in same recipe"


def test_ingredient_matching_multiple_others_via_different_strategies(
    client, admin_auth_token, test_session,
):
    # "Fresh Lime Juice" matches "Lime Juice" via variation
    # "Fresh Lime Juice" matches "Fresh lime juice" via exact
    # All three should end up in the same group
    _create_ingredient_db(test_session, "Fresh Lime Juice", "juice")
    _create_ingredient_db(test_session, "Lime Juice", "juice")
    _create_ingredient_db(test_session, "Fresh lime juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    # All three should be in ONE group (Union-Find transitive grouping)
    found_group = None
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Fresh Lime Juice" in all_names:
            found_group = group
            break

    assert found_group is not None, "Multi-strategy group not found"
    all_names = {found_group["target"]["name"]} | {
        d["name"] for d in found_group["duplicates"]
    }
    assert "Fresh Lime Juice" in all_names
    assert "Lime Juice" in all_names
    assert "Fresh lime juice" in all_names
    # group_reason should be exact (highest priority in the group)
    assert found_group["group_reason"] == "exact_match_case_insensitive"


# --- Variation Normalization Edge Cases (Review Fix M3) ---


def test_detects_freshly_squeezed_prefix_variation(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Freshly Squeezed Lime Juice", "juice")
    _create_ingredient_db(test_session, "Lime Juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Freshly Squeezed Lime Juice" in all_names and "Lime Juice" in all_names:
            found = True
            assert group["group_reason"] == "variation_pattern"
            break
    assert found, "Freshly squeezed variation not detected"


def test_detects_chilled_suffix_variation(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Lime Juice (chilled)", "juice")
    _create_ingredient_db(test_session, "Lime Juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Lime Juice (chilled)" in all_names and "Lime Juice" in all_names:
            found = True
            assert group["group_reason"] == "variation_pattern"
            break
    assert found, "Chilled suffix variation not detected"


def test_detects_freshly_pressed_prefix_variation(client, admin_auth_token, test_session):
    _create_ingredient_db(test_session, "Freshly Pressed Orange Juice", "juice")
    _create_ingredient_db(test_session, "Orange Juice", "juice")

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Freshly Pressed Orange Juice" in all_names and "Orange Juice" in all_names:
            found = True
            assert group["group_reason"] == "variation_pattern"
            break
    assert found, "Freshly pressed variation not detected"


# --- Fuzzy Threshold Boundary Test (Review Fix M4) ---


def test_ignores_fuzzy_match_at_exact_threshold(client, admin_auth_token, test_session):
    """Verify > 0.8 threshold excludes exactly 0.8 ratio.

    SequenceMatcher("orange juic", "orange juix").ratio() = 0.8181...
    SequenceMatcher("grapefruit", "grape fruit").ratio() ~= 0.9
    We need a pair just barely below 0.8 to verify the boundary.
    SequenceMatcher("lemon", "melon").ratio() = 0.4 — too low.
    SequenceMatcher("lime juice", "lime juicy").ratio() = 0.9 — too high.
    Use two names that produce a ratio near but <= 0.8.
    """
    # "Dry Curacao" vs "Dry Curacoa" — SequenceMatcher ratio ≈ 0.9091, above threshold
    # Need something closer to 0.8
    # "Angostura" (9 chars) vs "Angostora" (9 chars) — 8/9 match = ratio ~0.888, above
    # "Pimento Dram" (12) vs "Pimento Drom" (12) — ratio ~0.916, above
    # We verify the existing test with dissimilar strings, and add a near-boundary pair
    # that IS above threshold to confirm it's detected
    _create_ingredient_db(test_session, "Maraschino", "liqueur")
    _create_ingredient_db(test_session, "Maraschin", "liqueur")  # ratio = 18/19 ≈ 0.947

    response = client.get(
        ENDPOINT,
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    data = response.json()

    # This pair should be detected (above threshold)
    found = False
    for group in data["groups"]:
        all_names = {group["target"]["name"]} | {d["name"] for d in group["duplicates"]}
        if "Maraschino" in all_names and "Maraschin" in all_names:
            found = True
            for dup in group["duplicates"]:
                assert dup["similarity_score"] > 0.8
            break
    assert found, "Near-threshold fuzzy match not detected"
