"""
Tests for admin recipe capabilities (Stories 1.2 and 1.3).

Story 1.2 - Admin Recipe Edit:
- AC-1: Admin can edit non-owned recipe (returns 200)
- AC-2: Non-admin cannot edit non-owned recipe (returns 403)
- AC-3: Admin can edit all fields including ownership transfer
- AC-4: Admin editing own recipe works (regression)
- AC-5: Regular user editing own recipe works (regression)

Story 1.3 - Admin Recipe Delete:
- AC-1: Admin can delete non-owned recipe (returns 200)
- AC-2: Non-admin cannot delete non-owned recipe (returns 403)
- AC-3: Image file cleanup on delete
- AC-4: Recipe ingredients cascade delete
- AC-5: Admin can delete own recipe (regression)
- AC-6: Regular user can delete own recipe (regression)
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

    def test_transfer_to_nonexistent_user_fails(
        self, client, sample_recipe, admin_auth_token, test_session
    ):
        """
        AC-3 edge case: Transfer to non-existent user fails with 400.

        GIVEN: A recipe exists
        WHEN: Admin tries to transfer to a non-existent user_id
        THEN: Request fails with 400 Bad Request
        AND: Recipe ownership is NOT changed
        """
        original_owner_id = sample_recipe.user_id

        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"user_id": "nonexistent-uuid-12345"},
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

        # Verify ownership unchanged
        test_session.refresh(sample_recipe)
        assert sample_recipe.user_id == original_owner_id


class TestOwnerCanTransferRecipe:
    """Test recipe owner can transfer their own recipe."""

    def test_owner_can_transfer_own_recipe(
        self, client, sample_recipe, sample_user, another_user, auth_token, test_session
    ):
        """
        Owner can transfer ownership of their own recipe.

        GIVEN: A recipe owned by sample_user
        WHEN: sample_user sets user_id to another_user.id
        THEN: Recipe ownership is transferred successfully
        """
        # Verify precondition: recipe owned by sample_user
        assert sample_recipe.user_id == sample_user.id

        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"user_id": another_user.id},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200

        # Verify ownership transferred
        test_session.refresh(sample_recipe)
        assert sample_recipe.user_id == another_user.id

    def test_owner_transfer_to_nonexistent_user_fails(
        self, client, sample_recipe, sample_user, auth_token, test_session
    ):
        """
        Owner cannot transfer to non-existent user.

        GIVEN: A recipe owned by sample_user
        WHEN: sample_user tries to transfer to non-existent user_id
        THEN: Request fails with 400 Bad Request
        """
        original_owner_id = sample_recipe.user_id

        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"user_id": "fake-user-id-99999"},
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

        # Verify ownership unchanged
        test_session.refresh(sample_recipe)
        assert sample_recipe.user_id == original_owner_id


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


# ============================================================================
# Admin Recipe Delete Tests (Story 1.3)
# ============================================================================


class TestAdminRecipeDeleteBypass:
    """Test admin bypass for recipe deletion (AC-1, AC-2)."""

    def test_admin_can_delete_any_recipe(
        self, client, sample_recipe, another_user, admin_auth_token, test_session
    ):
        """
        AC-1: Admin can delete recipe they don't own.

        GIVEN: A recipe owned by sample_user
        WHEN: Admin sends DELETE to /api/recipes/{id}
        THEN: Recipe is deleted successfully with 200 response
        """
        recipe_id = sample_recipe.id

        # Admin attempts to delete another user's recipe
        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        # Should succeed with 200
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify recipe no longer exists in database
        deleted_recipe = test_session.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert deleted_recipe is None

    def test_non_admin_cannot_delete_others_recipe(
        self, client, sample_recipe, another_auth_token, test_session
    ):
        """
        AC-2: Non-admin cannot delete recipe they don't own.

        GIVEN: A recipe owned by sample_user
        WHEN: another_user (non-admin) sends DELETE to /api/recipes/{id}
        THEN: Request is rejected with 403 Forbidden
        """
        recipe_id = sample_recipe.id

        # another_user attempts to delete sample_user's recipe
        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {another_auth_token}"},
        )

        # Should be rejected with 403
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

        # Verify recipe was NOT deleted
        recipe = test_session.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert recipe is not None
        assert recipe.name == "Margarita"


class TestAdminDeleteImageCleanup:
    """Test image cleanup on admin delete (AC-3)."""

    def test_admin_delete_removes_recipe_image(
        self, client, sample_user, admin_auth_token, test_session
    ):
        """
        AC-3: Image file is deleted when admin deletes recipe with image.

        GIVEN: A recipe with an associated image file
        WHEN: Admin deletes the recipe
        THEN: delete_image is called to clean up the image file
        """
        from unittest.mock import patch, MagicMock

        # Create a recipe with an image path
        recipe_with_image = Recipe(
            name="Recipe With Image",
            description="Has an image",
            instructions="Test",
            template="sour",
            main_spirit="vodka",
            source_type="manual",
            source_image_path="images/test-image-12345.jpg",  # Has image
            user_id=sample_user.id,
        )
        test_session.add(recipe_with_image)
        test_session.commit()
        test_session.refresh(recipe_with_image)
        recipe_id = recipe_with_image.id

        # Mock the image storage to verify delete_image is called
        mock_storage = MagicMock()
        with patch("app.routers.recipes.get_image_storage", return_value=mock_storage):
            response = client.delete(
                f"/api/recipes/{recipe_id}",
                headers={"Authorization": f"Bearer {admin_auth_token}"},
            )

        # Should succeed
        assert response.status_code == 200

        # Verify delete_image was called with correct path
        mock_storage.delete_image.assert_called_once_with("images/test-image-12345.jpg")


class TestAdminDeleteCascade:
    """Test cascade delete for recipe_ingredients (AC-4)."""

    def test_admin_delete_cascades_to_recipe_ingredients(
        self, client, sample_recipe, admin_auth_token, test_session
    ):
        """
        AC-4: Recipe ingredients are cascade deleted.

        GIVEN: A recipe with associated ingredients in recipe_ingredients table
        WHEN: Admin deletes the recipe
        THEN: The recipe_ingredients records are also deleted
        """
        from app.models import RecipeIngredient

        recipe_id = sample_recipe.id

        # Verify precondition: recipe has ingredients
        ingredients_before = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == recipe_id
        ).all()
        assert len(ingredients_before) >= 1

        # Admin deletes the recipe
        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200

        # Verify recipe_ingredients were cascade deleted
        ingredients_after = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == recipe_id
        ).all()
        assert len(ingredients_after) == 0


class TestAdminDeleteOwnRecipe:
    """Test admin can delete their own recipes (AC-5)."""

    def test_admin_can_delete_own_recipe(
        self, client, admin_user, admin_auth_token, test_session
    ):
        """
        AC-5: Admin deleting their OWN recipe works as before.

        GIVEN: A recipe owned by the admin user
        WHEN: Admin deletes their own recipe
        THEN: Delete succeeds (regression test)
        """
        # Create a recipe owned by admin
        admin_recipe = Recipe(
            name="Admin's Cocktail",
            description="Admin's recipe to delete",
            instructions="Test",
            template="sour",
            main_spirit="gin",
            source_type="manual",
            user_id=admin_user.id,
        )
        test_session.add(admin_recipe)
        test_session.commit()
        test_session.refresh(admin_recipe)
        recipe_id = admin_recipe.id

        # Admin deletes their own recipe
        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {admin_auth_token}"},
        )

        assert response.status_code == 200

        # Verify recipe deleted
        deleted = test_session.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert deleted is None


class TestRegularUserOwnRecipeDelete:
    """Test regular users can still delete their own recipes (AC-6)."""

    def test_owner_can_still_delete_own_recipe(
        self, client, sample_recipe, sample_user, auth_token, test_session
    ):
        """
        AC-6: Regular user deleting their OWN recipe works as before.

        GIVEN: A recipe owned by sample_user
        WHEN: sample_user deletes their own recipe
        THEN: Delete succeeds (regression test - existing functionality preserved)
        """
        # Verify precondition: sample_recipe owned by sample_user
        assert sample_recipe.user_id == sample_user.id
        recipe_id = sample_recipe.id

        # Owner deletes their own recipe
        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify recipe deleted
        deleted = test_session.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert deleted is None

    def test_unauthenticated_user_cannot_delete_recipe(
        self, client, sample_recipe, test_session
    ):
        """
        Regression test: Unauthenticated user cannot delete owned recipes.

        GIVEN: A recipe exists with an owner
        WHEN: Unauthenticated request to DELETE /api/recipes/{id}
        THEN: Request is rejected with 401 Unauthorized
        AND: Recipe is NOT deleted
        """
        recipe_id = sample_recipe.id

        response = client.delete(f"/api/recipes/{recipe_id}")

        assert response.status_code == 401
        assert "authentication" in response.json()["detail"].lower()

        # Verify recipe was NOT deleted
        recipe = test_session.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert recipe is not None


class TestOrphanRecipeDelete:
    """Test deletion of recipes with no owner (user_id=None)."""

    def test_anyone_can_delete_orphan_recipe(
        self, client, test_session
    ):
        """
        Edge case: Orphan recipes (no owner) can be deleted by anyone.

        GIVEN: A recipe with user_id=None (legacy/orphan recipe)
        WHEN: Any user (even unauthenticated) sends DELETE
        THEN: Recipe is deleted successfully

        Note: This is intentional backwards-compatibility behavior.
        """
        # Create an orphan recipe (no owner)
        orphan_recipe = Recipe(
            name="Orphan Cocktail",
            description="No owner",
            instructions="Test",
            template="sour",
            main_spirit="vodka",
            source_type="manual",
            user_id=None,  # No owner
        )
        test_session.add(orphan_recipe)
        test_session.commit()
        test_session.refresh(orphan_recipe)
        recipe_id = orphan_recipe.id

        # Unauthenticated delete should work for orphan recipes
        response = client.delete(f"/api/recipes/{recipe_id}")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify recipe deleted
        deleted = test_session.query(Recipe).filter(Recipe.id == recipe_id).first()
        assert deleted is None
