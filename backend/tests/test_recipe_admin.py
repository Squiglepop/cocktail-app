"""
Tests for admin recipe edit capabilities (Story 1.2).

Tests cover:
- AC-1: Admin can edit non-owned recipe (returns 200)
- AC-2: Non-admin cannot edit non-owned recipe (returns 403)
- AC-3: Admin can edit all fields including ownership transfer
- AC-4: Admin editing own recipe works (regression)
- AC-5: Regular user editing own recipe works (regression)

RED PHASE: These tests are designed to FAIL until the admin bypass
is implemented in recipes.py lines 546-550.
"""
import pytest
from app.models import Recipe


class TestAdminRecipeEditBypass:
    """Test admin bypass for recipe editing (AC-1, AC-2)."""

    def test_admin_can_edit_any_recipe(
        self, client, sample_recipe, another_user, admin_auth_token, test_session
    ):
        """
        AC-1: Admin can edit recipe they don't own.

        GIVEN: A recipe owned by another_user
        WHEN: Admin sends PUT to /api/recipes/{id} with updates
        THEN: Recipe is updated successfully with 200 response

        RED PHASE: Should FAIL until admin bypass added to recipes.py:546-550
        """
        # Verify precondition: recipe is owned by sample_user, not admin
        assert sample_recipe.user_id != None

        # Admin attempts to edit another user's recipe
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"name": "Admin Edited Margarita", "description": "Edited by admin"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        # Should succeed with 200 (currently fails with 403)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Admin Edited Margarita"
        assert data["description"] == "Edited by admin"

    def test_non_admin_cannot_edit_others_recipe(
        self, client, sample_recipe, another_auth_token, test_session
    ):
        """
        AC-2: Non-admin cannot edit recipe they don't own.

        GIVEN: A recipe owned by sample_user
        WHEN: another_user (non-admin) sends PUT to /api/recipes/{id}
        THEN: Request is rejected with 403 Forbidden

        RED PHASE: Should PASS (existing behavior preserved)
        """
        # another_user attempts to edit sample_user's recipe
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"name": "Hacked Margarita"},
            headers={"Authorization": f"Bearer {another_auth_token}"},
        )

        # Should be rejected with 403
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

        # Verify recipe was NOT modified
        test_session.refresh(sample_recipe)
        assert sample_recipe.name == "Margarita"


class TestAdminEditAllFields:
    """Test admin can edit all recipe fields (AC-3)."""

    def test_admin_can_edit_text_fields(
        self, client, sample_recipe, admin_auth_token, test_session
    ):
        """
        AC-3: Admin can modify all text fields.

        GIVEN: A recipe exists
        WHEN: Admin updates name, description, instructions, notes, garnish
        THEN: All fields are updated successfully

        RED PHASE: Should FAIL until admin bypass added
        """
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={
                "name": "Admin Modified Name",
                "description": "Admin modified description",
                "instructions": "Admin modified instructions",
                "notes": "Admin notes",
                "garnish": "Admin garnish",
            },
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Admin Modified Name"
        assert data["description"] == "Admin modified description"
        assert data["instructions"] == "Admin modified instructions"
        assert data["notes"] == "Admin notes"
        assert data["garnish"] == "Admin garnish"

    def test_admin_can_edit_category_fields(
        self, client, sample_recipe, admin_auth_token, test_session
    ):
        """
        AC-3: Admin can modify all category assignments.

        GIVEN: A recipe with template=sour, method=shaken
        WHEN: Admin updates template, glassware, method, serving_style, main_spirit
        THEN: All category fields are updated successfully

        RED PHASE: Should FAIL until admin bypass added
        """
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={
                "template": "old_fashioned",
                "glassware": "rocks",
                "method": "stirred",
                "serving_style": "rocks",
                "main_spirit": "bourbon",
            },
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["template"] == "old_fashioned"
        assert data["glassware"] == "rocks"
        assert data["method"] == "stirred"
        assert data["serving_style"] == "rocks"
        assert data["main_spirit"] == "bourbon"

    def test_admin_can_edit_visibility(
        self, client, sample_recipe, admin_auth_token, test_session
    ):
        """
        AC-3: Admin can modify visibility setting.

        GIVEN: A recipe with visibility=public
        WHEN: Admin changes visibility to private
        THEN: Visibility is updated successfully

        RED PHASE: Should FAIL until admin bypass added
        """
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"visibility": "private"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["visibility"] == "private"

    def test_admin_can_modify_recipe_ingredients(
        self, client, sample_recipe, sample_ingredient, admin_auth_token, test_session
    ):
        """
        AC-3: Admin can modify ingredients (add/remove/modify).

        GIVEN: A recipe with one ingredient (Tequila, 2oz)
        WHEN: Admin updates ingredients to a different set
        THEN: Ingredients are replaced with new values
        """
        # Verify precondition: recipe has 1 ingredient
        assert len(sample_recipe.ingredients) == 1
        original_ingredient_id = sample_recipe.ingredients[0].ingredient_id

        # Admin modifies ingredients - change amount and add a new ingredient
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={
                "ingredients": [
                    {
                        "ingredient_id": original_ingredient_id,
                        "amount": 3.0,  # Changed from 2.0
                        "unit": "oz",
                        "order": 0,
                    },
                    {
                        "ingredient_name": "Lime Juice",  # New ingredient
                        "ingredient_type": "juice",
                        "amount": 1.0,
                        "unit": "oz",
                        "order": 1,
                    },
                ]
            },
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify ingredients were modified
        assert len(data["ingredients"]) == 2
        # First ingredient amount changed
        tequila = next(i for i in data["ingredients"] if i["ingredient"]["name"] == "Tequila")
        assert tequila["amount"] == 3.0
        # New ingredient added
        lime = next(i for i in data["ingredients"] if i["ingredient"]["name"] == "Lime Juice")
        assert lime["amount"] == 1.0
        assert lime["unit"] == "oz"


class TestAdminOwnershipTransfer:
    """Test admin can transfer recipe ownership (AC-3)."""

    def test_admin_can_transfer_recipe_ownership(
        self, client, sample_recipe, sample_user, another_user, admin_auth_token, test_session
    ):
        """
        AC-3: Admin can transfer ownership to another user.

        GIVEN: A recipe owned by sample_user
        WHEN: Admin sets user_id to another_user.id
        THEN: Recipe ownership is transferred

        RED PHASE: Should FAIL until admin bypass added AND user_id in RecipeUpdate schema
        """
        # Verify precondition: recipe owned by sample_user
        assert sample_recipe.user_id == sample_user.id

        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"user_id": another_user.id},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200

        # Verify ownership transferred
        test_session.refresh(sample_recipe)
        assert sample_recipe.user_id == another_user.id


class TestAdminOwnRecipeEdit:
    """Test admin can still edit their own recipes (AC-4)."""

    def test_admin_editing_own_recipe_works(
        self, client, admin_user, admin_auth_token, test_session, sample_ingredient
    ):
        """
        AC-4: Admin editing their OWN recipe works as before.

        GIVEN: A recipe owned by the admin user
        WHEN: Admin edits their own recipe
        THEN: Edit succeeds (regression test)
        """
        # Create a recipe owned by admin
        admin_recipe = Recipe(
            name="Admin's Original Recipe",
            description="Admin's recipe",
            instructions="Admin's instructions",
            template="sour",
            main_spirit="vodka",
            glassware="coupe",
            serving_style="up",
            method="shaken",
            source_type="manual",
            user_id=admin_user.id,
        )
        test_session.add(admin_recipe)
        test_session.commit()
        test_session.refresh(admin_recipe)

        # Admin edits their own recipe
        response = client.put(
            f"/api/recipes/{admin_recipe.id}",
            json={"name": "Admin's Edited Recipe"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Admin's Edited Recipe"


class TestRegularUserOwnRecipeEdit:
    """Test regular users can still edit their own recipes (AC-5)."""

    def test_owner_can_still_edit_own_recipe(
        self, client, sample_recipe, sample_user, auth_token, test_session
    ):
        """
        AC-5: Regular user editing their OWN recipe works as before.

        GIVEN: A recipe owned by sample_user
        WHEN: sample_user edits their own recipe
        THEN: Edit succeeds (regression test - existing functionality preserved)
        """
        # Verify precondition: sample_recipe owned by sample_user
        assert sample_recipe.user_id == sample_user.id

        # Owner edits their own recipe
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"name": "My Edited Margarita"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "My Edited Margarita"

    def test_unauthenticated_user_cannot_edit_recipe(
        self, client, sample_recipe, test_session
    ):
        """
        Regression test: Unauthenticated user cannot edit recipes.

        GIVEN: A recipe exists
        WHEN: Unauthenticated request to PUT /api/recipes/{id}
        THEN: Request is rejected with 401 Unauthorized
        """
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"name": "Hacked"},
        )

        assert response.status_code == 401
