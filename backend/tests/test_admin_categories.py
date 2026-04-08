"""
Tests for admin category management endpoints (Story 1.6).
"""
from app.models import CategoryTemplate, CategorySpirit, CategoryGlassware


# --- Auth Tests (AC-8) ---


def test_admin_categories_returns_401_without_auth(client, seeded_categories):
    response = client.get("/api/admin/categories/templates")
    assert response.status_code == 401


def test_admin_categories_returns_403_for_regular_user(client, auth_token, seeded_categories):
    response = client.get(
        "/api/admin/categories/templates",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


def test_create_category_returns_401_without_auth(client, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "test", "label": "Test"},
    )
    assert response.status_code == 401


def test_create_category_returns_403_for_regular_user(client, auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "test", "label": "Test"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


def test_update_category_returns_401_without_auth(client, seeded_categories):
    response = client.put(
        "/api/admin/categories/templates/some-id",
        json={"label": "Test"},
    )
    assert response.status_code == 401


def test_update_category_returns_403_for_regular_user(client, auth_token, seeded_categories):
    response = client.put(
        "/api/admin/categories/templates/some-id",
        json={"label": "Test"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


def test_delete_category_returns_401_without_auth(client, seeded_categories):
    response = client.delete("/api/admin/categories/templates/some-id")
    assert response.status_code == 401


def test_delete_category_returns_403_for_regular_user(client, auth_token, seeded_categories):
    response = client.delete(
        "/api/admin/categories/templates/some-id",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


def test_reorder_categories_returns_401_without_auth(client, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates/reorder",
        json={"ids": ["a", "b"]},
    )
    assert response.status_code == 401


def test_reorder_categories_returns_403_for_regular_user(client, auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates/reorder",
        json={"ids": ["a", "b"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 403


# --- GET Tests (AC-1) ---


def test_get_all_templates_includes_inactive(client, admin_auth_token, seeded_categories):
    # Deactivate one template
    db = seeded_categories
    template = db.query(CategoryTemplate).first()
    template.is_active = False
    db.commit()

    response = client.get(
        "/api/admin/categories/templates",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    inactive = [c for c in data if not c["is_active"]]
    assert len(inactive) >= 1


def test_get_all_templates_ordered_by_sort_order(client, admin_auth_token, seeded_categories):
    response = client.get(
        "/api/admin/categories/templates",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    sort_orders = [c["sort_order"] for c in data]
    assert sort_orders == sorted(sort_orders)


def test_get_invalid_type_returns_400(client, admin_auth_token, seeded_categories):
    response = client.get(
        "/api/admin/categories/bogus",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "Invalid category type" in response.json()["detail"]


# --- POST (Create) Tests (AC-2, AC-3) ---


def test_create_template_returns_201(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "new_template", "label": "New Template"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == "new_template"
    assert data["label"] == "New Template"
    assert data["is_active"] is True
    assert len(data["id"]) == 36


def test_create_template_auto_assigns_sort_order(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    max_order = max(t.sort_order for t in db.query(CategoryTemplate).all())

    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "auto_order_test", "label": "Auto Order"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    assert response.json()["sort_order"] == max_order + 1


def test_create_duplicate_value_returns_409(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    existing = db.query(CategoryTemplate).first()

    response = client.post(
        "/api/admin/categories/templates",
        json={"value": existing.value, "label": "Duplicate"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_template_with_description(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "desc_test", "label": "With Desc", "description": "A test description"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    assert response.json()["description"] == "A test description"


def test_create_spirit_without_description(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/spirits",
        json={"value": "absinthe", "label": "Absinthe", "description": "Should be ignored"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_glassware_defaults_category_to_specialty(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/glassware",
        json={"value": "custom_glass", "label": "Custom Glass"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    assert response.json()["category"] == "specialty"


def test_create_glassware_with_explicit_category(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/glassware",
        json={"value": "tall_glass", "label": "Tall Glass", "category": "tall"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 201
    assert response.json()["category"] == "tall"


def test_create_category_rejects_non_snake_case_value(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates",
        json={"value": "Invalid Value!", "label": "Bad"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 422
    assert "snake_case" in response.json()["detail"][0]["msg"]


# --- PUT (Update) Tests (AC-4) ---


def test_update_template_label(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    template = db.query(CategoryTemplate).first()

    response = client.put(
        f"/api/admin/categories/templates/{template.id}",
        json={"label": "Updated Label"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["label"] == "Updated Label"


def test_update_template_description(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    template = db.query(CategoryTemplate).first()

    response = client.put(
        f"/api/admin/categories/templates/{template.id}",
        json={"description": "New description"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "New description"


def test_update_template_deactivate(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    template = db.query(CategoryTemplate).first()

    response = client.put(
        f"/api/admin/categories/templates/{template.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_update_nonexistent_returns_404(client, admin_auth_token, seeded_categories):
    response = client.put(
        "/api/admin/categories/templates/nonexistent-id",
        json={"label": "Nope"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404


def test_update_value_field_is_immutable(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    template = db.query(CategoryTemplate).first()
    original_value = template.value

    response = client.put(
        f"/api/admin/categories/templates/{template.id}",
        json={"value": "hacked_value", "label": "Changed Label"},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["value"] == original_value
    assert response.json()["label"] == "Changed Label"


# --- DELETE (Soft-Delete) Tests (AC-5, AC-6) ---


def test_delete_template_soft_deletes(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    template = db.query(CategoryTemplate).first()

    response = client.delete(
        f"/api/admin/categories/templates/{template.id}",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert "deactivated" in response.json()["message"]

    # Verify record still exists but is inactive
    db.expire_all()
    record = db.query(CategoryTemplate).filter(CategoryTemplate.id == template.id).first()
    assert record is not None
    assert record.is_active is False


def test_delete_returns_recipe_count(client, admin_auth_token, seeded_categories, sample_recipe):
    db = seeded_categories
    # sample_recipe has template="sour"
    sour = db.query(CategoryTemplate).filter(CategoryTemplate.value == "sour").first()

    response = client.delete(
        f"/api/admin/categories/templates/{sour.id}",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200
    assert response.json()["recipe_count"] >= 1


def test_delete_nonexistent_returns_404(client, admin_auth_token, seeded_categories):
    response = client.delete(
        "/api/admin/categories/templates/nonexistent-id",
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 404


# --- Reorder Tests (AC-7) ---


def test_reorder_templates(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    templates = db.query(CategoryTemplate).order_by(CategoryTemplate.sort_order).all()
    reversed_ids = [t.id for t in reversed(templates)]

    response = client.post(
        "/api/admin/categories/templates/reorder",
        json={"ids": reversed_ids},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 200

    # Verify new order
    db.expire_all()
    reordered = db.query(CategoryTemplate).order_by(CategoryTemplate.sort_order).all()
    assert [t.id for t in reordered] == reversed_ids


def test_reorder_with_invalid_ids_returns_400(client, admin_auth_token, seeded_categories):
    response = client.post(
        "/api/admin/categories/templates/reorder",
        json={"ids": ["fake-id-1", "fake-id-2"]},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_reorder_with_partial_ids_returns_400(client, admin_auth_token, seeded_categories):
    db = seeded_categories
    templates = db.query(CategoryTemplate).order_by(CategoryTemplate.sort_order).all()
    # Send only the first 2 IDs instead of all
    partial_ids = [t.id for t in templates[:2]]

    response = client.post(
        "/api/admin/categories/templates/reorder",
        json={"ids": partial_ids},
        headers={"Authorization": f"Bearer {admin_auth_token}"},
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]
