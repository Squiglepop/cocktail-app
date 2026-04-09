"""
Integration tests for audit log wiring into admin endpoints (Story 4-2).
Tests that admin actions create correct audit entries.
"""
import pytest
from unittest.mock import patch

from app.models.audit_log import AuditLog


# --- Helpers ---

def _get_audit_entries(session, action=None, entity_type=None, entity_id=None):
    """Query audit log entries with optional filters."""
    q = session.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    return q.all()


# --- AC-1: Category Audit Tests ---


class TestCategoryAudit:

    def test_category_create_generates_audit_entry(
        self, client, test_session, admin_auth_token, admin_user, seeded_categories
    ):
        response = client.post(
            "/api/admin/categories/templates",
            json={"value": "daisy", "label": "Daisy"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 201
        category_id = response.json()["id"]

        entries = _get_audit_entries(test_session, action="category_create")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == category_id
        assert entry.entity_type == "category"
        assert entry.admin_user_id == admin_user.id
        assert entry.details["type"] == "templates"
        assert entry.details["value"] == "daisy"
        assert entry.details["label"] == "Daisy"

    def test_category_update_generates_audit_entry_with_changes(
        self, client, test_session, admin_auth_token, seeded_categories
    ):
        # Create a category to update
        create_resp = client.post(
            "/api/admin/categories/templates",
            json={"value": "fix", "label": "Fix"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        cat_id = create_resp.json()["id"]
        # Clear audit entries from create
        test_session.query(AuditLog).delete()
        test_session.commit()

        # Update the label
        response = client.put(
            f"/api/admin/categories/templates/{cat_id}",
            json={"label": "The Fix"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="category_update")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == cat_id
        assert entry.details["type"] == "templates"
        assert "label" in entry.details["changes"]
        assert entry.details["changes"]["label"] == ["Fix", "The Fix"]

    def test_category_update_no_change_skips_audit(
        self, client, test_session, admin_auth_token, seeded_categories
    ):
        # Create a category
        create_resp = client.post(
            "/api/admin/categories/templates",
            json={"value": "audit_test_nochange", "label": "NoChange"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert create_resp.status_code == 201
        cat_id = create_resp.json()["id"]
        # Clear audit
        test_session.query(AuditLog).delete()
        test_session.commit()

        # "Update" with same label — no actual change
        response = client.put(
            f"/api/admin/categories/templates/{cat_id}",
            json={"label": "NoChange"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="category_update")
        assert len(entries) == 0

    def test_category_delete_generates_audit_entry(
        self, client, test_session, admin_auth_token, seeded_categories
    ):
        # Create a category to delete
        create_resp = client.post(
            "/api/admin/categories/templates",
            json={"value": "audit_test_delete", "label": "DeleteMe"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert create_resp.status_code == 201
        cat_id = create_resp.json()["id"]
        # Clear audit
        test_session.query(AuditLog).delete()
        test_session.commit()

        response = client.delete(
            f"/api/admin/categories/templates/{cat_id}",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="category_delete")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == cat_id
        assert entry.details["type"] == "templates"
        assert entry.details["value"] == "audit_test_delete"


# --- AC-2: Ingredient Audit Tests ---


class TestIngredientAudit:

    def test_ingredient_create_generates_audit_entry(
        self, client, test_session, admin_auth_token, admin_user
    ):
        response = client.post(
            "/api/admin/ingredients",
            json={"name": "Campari", "type": "liqueur"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 201
        ingredient_id = response.json()["id"]

        entries = _get_audit_entries(test_session, action="ingredient_create")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == ingredient_id
        assert entry.entity_type == "ingredient"
        assert entry.admin_user_id == admin_user.id
        assert entry.details["name"] == "Campari"
        assert entry.details["type"] == "liqueur"

    def test_ingredient_update_generates_audit_entry_with_changes(
        self, client, test_session, admin_auth_token
    ):
        # Create ingredient
        create_resp = client.post(
            "/api/admin/ingredients",
            json={"name": "Aperol", "type": "liqueur"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        ing_id = create_resp.json()["id"]
        test_session.query(AuditLog).delete()
        test_session.commit()

        # Update name
        response = client.put(
            f"/api/admin/ingredients/{ing_id}",
            json={"name": "Aperol Spritz Base"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="ingredient_update")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == ing_id
        assert "name" in entry.details["changes"]
        assert entry.details["changes"]["name"] == ["Aperol", "Aperol Spritz Base"]

    def test_ingredient_update_no_change_skips_audit(
        self, client, test_session, admin_auth_token
    ):
        # Create ingredient
        create_resp = client.post(
            "/api/admin/ingredients",
            json={"name": "Maraschino", "type": "liqueur"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert create_resp.status_code == 201
        ing_id = create_resp.json()["id"]
        test_session.query(AuditLog).delete()
        test_session.commit()

        # "Update" with same name — no actual change
        response = client.put(
            f"/api/admin/ingredients/{ing_id}",
            json={"name": "Maraschino"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="ingredient_update")
        assert len(entries) == 0

    def test_ingredient_delete_generates_audit_entry(
        self, client, test_session, admin_auth_token
    ):
        # Create ingredient (no recipes using it)
        create_resp = client.post(
            "/api/admin/ingredients",
            json={"name": "Chartreuse", "type": "liqueur"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        ing_id = create_resp.json()["id"]
        test_session.query(AuditLog).delete()
        test_session.commit()

        response = client.delete(
            f"/api/admin/ingredients/{ing_id}",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="ingredient_delete")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == ing_id
        assert entry.details["name"] == "Chartreuse"
        assert entry.details["type"] == "liqueur"

    def test_ingredient_merge_generates_audit_entry(
        self, client, test_session, admin_auth_token
    ):
        # Create target and source ingredients
        target_resp = client.post(
            "/api/admin/ingredients",
            json={"name": "Lemon Juice", "type": "juice"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        target_id = target_resp.json()["id"]

        source_resp = client.post(
            "/api/admin/ingredients",
            json={"name": "Fresh Lemon", "type": "juice"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        source_id = source_resp.json()["id"]

        test_session.query(AuditLog).delete()
        test_session.commit()

        response = client.post(
            "/api/admin/ingredients/merge",
            json={"target_id": target_id, "source_ids": [source_id]},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="ingredient_merge")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == target_id
        assert entry.details["target_name"] == "Lemon Juice"
        assert entry.details["source_names"] == ["Fresh Lemon"]
        assert entry.details["source_ids"] == [source_id]
        assert entry.details["target_id"] == target_id
        assert "recipes_updated" in entry.details


# --- AC-3: Recipe Admin Audit Tests ---


class TestRecipeAdminAudit:

    def test_recipe_admin_update_generates_audit_when_admin_edits_other_user_recipe(
        self, client, test_session, admin_auth_token, admin_user, sample_recipe
    ):
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"name": "Updated Margarita"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="recipe_admin_update")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == sample_recipe.id
        assert entry.entity_type == "recipe"
        assert entry.admin_user_id == admin_user.id
        assert entry.details["recipe_name"] == "Margarita"
        assert entry.details["owner_id"] == sample_recipe.user_id
        assert "name" in entry.details["changes"]

    def test_recipe_admin_delete_generates_audit_when_admin_deletes_other_user_recipe(
        self, client, test_session, admin_auth_token, admin_user, sample_recipe
    ):
        recipe_id = sample_recipe.id
        recipe_name = sample_recipe.name
        owner_id = sample_recipe.user_id

        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="recipe_admin_delete")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == recipe_id
        assert entry.admin_user_id == admin_user.id
        assert entry.details["recipe_name"] == recipe_name
        assert entry.details["owner_id"] == owner_id

    def test_recipe_no_audit_when_admin_edits_own_recipe(
        self, client, test_session, admin_auth_token, admin_user
    ):
        # Create a recipe owned by the admin
        create_resp = client.post(
            "/api/recipes",
            json={
                "name": "Admin's Negroni",
                "instructions": "Stir with ice",
                "ingredients": [],
            },
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert create_resp.status_code == 200
        recipe_id = create_resp.json()["id"]

        # Update own recipe
        response = client.put(
            f"/api/recipes/{recipe_id}",
            json={"name": "Admin's Perfect Negroni"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="recipe_admin_update")
        assert len(entries) == 0

    def test_recipe_admin_update_no_change_skips_audit(
        self, client, test_session, admin_auth_token, admin_user, sample_recipe
    ):
        # Send update with same name — no actual change
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"name": sample_recipe.name},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="recipe_admin_update")
        assert len(entries) == 0

    def test_recipe_no_audit_when_admin_edits_unowned_recipe(
        self, client, test_session, admin_auth_token, orphan_recipe
    ):
        response = client.put(
            f"/api/recipes/{orphan_recipe.id}",
            json={"name": "Updated Old Fashioned"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="recipe_admin_update")
        assert len(entries) == 0


# --- AC-4: User Status Audit Tests ---


class TestUserStatusAudit:

    def test_user_activate_generates_audit_entry(
        self, client, test_session, admin_auth_token, inactive_user
    ):
        response = client.patch(
            f"/api/admin/users/{inactive_user.id}",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="user_activate")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == inactive_user.id
        assert entry.entity_type == "user"
        assert entry.details["email"] == inactive_user.email

    def test_user_deactivate_generates_audit_entry(
        self, client, test_session, admin_auth_token, another_user
    ):
        response = client.patch(
            f"/api/admin/users/{another_user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="user_deactivate")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == another_user.id
        assert entry.details["email"] == another_user.email

    def test_user_grant_admin_generates_audit_entry(
        self, client, test_session, admin_auth_token, another_user
    ):
        response = client.patch(
            f"/api/admin/users/{another_user.id}",
            json={"is_admin": True},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="user_grant_admin")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == another_user.id
        assert entry.details["email"] == another_user.email

    def test_user_revoke_admin_generates_audit_entry(
        self, client, test_session, admin_auth_token, admin_user, another_user
    ):
        # First grant admin
        client.patch(
            f"/api/admin/users/{another_user.id}",
            json={"is_admin": True},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        test_session.query(AuditLog).delete()
        test_session.commit()

        # Revoke admin
        response = client.patch(
            f"/api/admin/users/{another_user.id}",
            json={"is_admin": False},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, action="user_revoke_admin")
        assert len(entries) == 1
        entry = entries[0]
        assert entry.entity_id == another_user.id

    def test_user_status_no_change_no_audit(
        self, client, test_session, admin_auth_token, another_user
    ):
        # another_user is already active and non-admin — send same values
        response = client.patch(
            f"/api/admin/users/{another_user.id}",
            json={"is_active": True},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "No changes applied"

        entries = _get_audit_entries(test_session, entity_id=another_user.id)
        assert len(entries) == 0

    def test_user_status_both_changes_generate_two_audit_entries(
        self, client, test_session, admin_auth_token, inactive_user
    ):
        # inactive_user: is_active=False, is_admin=False
        response = client.patch(
            f"/api/admin/users/{inactive_user.id}",
            json={"is_active": True, "is_admin": True},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )
        assert response.status_code == 200

        entries = _get_audit_entries(test_session, entity_id=inactive_user.id)
        actions = {e.action for e in entries}
        assert "user_activate" in actions
        assert "user_grant_admin" in actions
        assert len(entries) == 2


# --- AC-5: Fire-and-Forget Tests ---


class TestAuditFireAndForget:

    def test_category_create_succeeds_when_audit_fails(
        self, client, admin_auth_token, seeded_categories
    ):
        with patch(
            "app.services.audit_service.AuditService.log",
            side_effect=Exception("DB connection lost"),
        ), patch("app.routers.admin.logger") as mock_logger:
            response = client.post(
                "/api/admin/categories/templates",
                json={"value": "tropical", "label": "Tropical"},
                headers={"Authorization": f"Bearer {admin_auth_token}"},
            )
        assert response.status_code == 201
        mock_logger.error.assert_called_once()

    def test_ingredient_create_succeeds_when_audit_fails(
        self, client, admin_auth_token
    ):
        with patch(
            "app.services.audit_service.AuditService.log",
            side_effect=Exception("DB connection lost"),
        ), patch("app.routers.admin.logger") as mock_logger:
            response = client.post(
                "/api/admin/ingredients",
                json={"name": "Absinthe", "type": "spirit"},
                headers={"Authorization": f"Bearer {admin_auth_token}"},
            )
        assert response.status_code == 201
        mock_logger.error.assert_called_once()

    def test_user_status_update_succeeds_when_audit_fails(
        self, client, admin_auth_token, inactive_user
    ):
        with patch(
            "app.services.audit_service.AuditService.log",
            side_effect=Exception("DB connection lost"),
        ), patch("app.routers.admin.logger") as mock_logger:
            response = client.patch(
                f"/api/admin/users/{inactive_user.id}",
                json={"is_active": True},
                headers={"Authorization": f"Bearer {admin_auth_token}"},
            )
        assert response.status_code == 200
        mock_logger.error.assert_called_once()

    def test_recipe_admin_delete_succeeds_when_audit_fails(
        self, client, admin_auth_token, sample_recipe
    ):
        with patch(
            "app.services.audit_service.AuditService.log",
            side_effect=Exception("DB connection lost"),
        ), patch("app.routers.recipes.logger") as mock_logger:
            response = client.delete(
                f"/api/recipes/{sample_recipe.id}",
                headers={"Authorization": f"Bearer {admin_auth_token}"},
            )
        assert response.status_code == 200
        mock_logger.error.assert_called_once()
