"""
Tests for recipe CRUD endpoints.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestListRecipes:
    """Tests for GET /api/recipes endpoint."""

    def test_list_recipes_empty(self, client):
        """Test listing recipes with empty database returns empty list."""
        response = client.get("/api/recipes")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_recipes_with_data(self, client, sample_recipe):
        """Test listing recipes returns all recipes."""
        response = client.get("/api/recipes")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margarita"

    def test_list_recipes_filter_template(self, client, sample_recipe, orphan_recipe):
        """Test filtering recipes by template."""
        response = client.get("/api/recipes?template=sour")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margarita"

    def test_list_recipes_filter_spirit(self, client, sample_recipe, orphan_recipe):
        """Test filtering recipes by main_spirit."""
        response = client.get("/api/recipes?main_spirit=bourbon")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Old Fashioned"

    def test_list_recipes_filter_glassware(self, client, sample_recipe, orphan_recipe):
        """Test filtering recipes by glassware."""
        response = client.get("/api/recipes?glassware=coupe")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margarita"

    def test_list_recipes_filter_serving_style(self, client, sample_recipe, orphan_recipe):
        """Test filtering recipes by serving_style."""
        response = client.get("/api/recipes?serving_style=rocks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Old Fashioned"

    def test_list_recipes_filter_method(self, client, sample_recipe, orphan_recipe):
        """Test filtering recipes by method."""
        response = client.get("/api/recipes?method=shaken")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margarita"

    def test_list_recipes_search(self, client, sample_recipe, orphan_recipe):
        """Test searching recipes by name/description."""
        response = client.get("/api/recipes?search=tequila")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margarita"

    def test_list_recipes_search_description(self, client, sample_recipe, orphan_recipe):
        """Test searching recipes by description."""
        response = client.get("/api/recipes?search=whiskey")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Old Fashioned"

    def test_list_recipes_pagination_skip(self, client, sample_recipe, orphan_recipe):
        """Test pagination with skip parameter."""
        # Get all first
        all_response = client.get("/api/recipes")
        all_data = all_response.json()

        # Skip first one
        response = client.get("/api/recipes?skip=1")
        data = response.json()

        assert response.status_code == 200
        assert len(data) == len(all_data) - 1

    def test_list_recipes_pagination_limit(self, client, sample_recipe, orphan_recipe):
        """Test pagination with limit parameter."""
        response = client.get("/api/recipes?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_list_recipes_by_user(self, client, sample_recipe, orphan_recipe, sample_user):
        """Test filtering recipes by user_id."""
        response = client.get(f"/api/recipes?user_id={sample_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Margarita"


class TestGetRecipe:
    """Tests for GET /api/recipes/{recipe_id} endpoint."""

    def test_get_recipe_success(self, client, sample_recipe):
        """Test getting a single recipe with ingredients."""
        response = client.get(f"/api/recipes/{sample_recipe.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Margarita"
        assert data["template"] == "sour"
        assert "ingredients" in data
        assert len(data["ingredients"]) > 0

    def test_get_recipe_not_found(self, client):
        """Test getting non-existent recipe returns 404."""
        response = client.get("/api/recipes/non-existent-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateRecipe:
    """Tests for POST /api/recipes endpoint."""

    def test_create_recipe_anonymous(self, client):
        """Test creating a recipe without authentication sets no user_id."""
        response = client.post(
            "/api/recipes",
            json={
                "name": "Test Cocktail",
                "description": "A test cocktail",
                "ingredients": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Cocktail"
        assert data["user_id"] is None

    def test_create_recipe_authenticated(self, client, sample_user, auth_token):
        """Test creating a recipe with authentication sets user_id."""
        response = client.post(
            "/api/recipes",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Auth Cocktail",
                "description": "A cocktail by authenticated user",
                "ingredients": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Auth Cocktail"
        assert data["user_id"] == sample_user.id

    def test_create_recipe_with_ingredients(self, client):
        """Test creating a recipe with ingredients."""
        response = client.post(
            "/api/recipes",
            json={
                "name": "Cocktail With Ingredients",
                "ingredients": [
                    {
                        "ingredient_name": "Vodka",
                        "ingredient_type": "spirit",
                        "amount": 2.0,
                        "unit": "oz",
                    },
                    {
                        "ingredient_name": "Lime Juice",
                        "ingredient_type": "juice",
                        "amount": 1.0,
                        "unit": "oz",
                    },
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Cocktail With Ingredients"
        assert len(data["ingredients"]) == 2

    def test_create_recipe_minimal(self, client):
        """Test creating a recipe with only required name field."""
        response = client.post(
            "/api/recipes",
            json={
                "name": "Minimal Cocktail",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Cocktail"

    def test_create_recipe_all_fields(self, client):
        """Test creating a recipe with all fields."""
        response = client.post(
            "/api/recipes",
            json={
                "name": "Complete Cocktail",
                "description": "Full description",
                "instructions": "Step 1. Step 2.",
                "template": "sour",
                "main_spirit": "tequila",
                "glassware": "coupe",
                "serving_style": "up",
                "method": "shaken",
                "garnish": "Lime wheel",
                "notes": "Some notes",
                "ingredients": [],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Complete Cocktail"
        assert data["template"] == "sour"
        assert data["main_spirit"] == "tequila"
        assert data["glassware"] == "coupe"
        assert data["serving_style"] == "up"
        assert data["method"] == "shaken"
        assert data["garnish"] == "Lime wheel"
        assert data["notes"] == "Some notes"

    def test_create_recipe_missing_name(self, client):
        """Test creating a recipe without name returns 422."""
        response = client.post(
            "/api/recipes",
            json={
                "description": "No name provided",
            },
        )

        assert response.status_code == 422


class TestUpdateRecipe:
    """Tests for PUT /api/recipes/{recipe_id} endpoint."""

    def test_update_recipe_owner(self, client, sample_recipe, auth_token):
        """Test owner can update their recipe."""
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Updated Margarita"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Margarita"

    def test_update_recipe_not_owner(self, client, sample_recipe, another_auth_token):
        """Test non-owner cannot update recipe."""
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            headers={"Authorization": f"Bearer {another_auth_token}"},
            json={"name": "Hacked Name"},
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    def test_update_recipe_no_auth(self, client, sample_recipe):
        """Test unauthenticated user cannot update owned recipe."""
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            json={"name": "No Auth Update"},
        )

        assert response.status_code == 401

    def test_update_recipe_orphan(self, client, orphan_recipe):
        """Test recipe without owner can be updated by anyone."""
        response = client.put(
            f"/api/recipes/{orphan_recipe.id}",
            json={"name": "Updated Old Fashioned"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Old Fashioned"

    def test_update_recipe_ingredients(self, client, sample_recipe, auth_token):
        """Test updating recipe ingredients replaces them."""
        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "ingredients": [
                    {
                        "ingredient_name": "New Ingredient",
                        "amount": 1.5,
                        "unit": "oz",
                    },
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["ingredients"]) == 1
        assert data["ingredients"][0]["ingredient"]["name"] == "New Ingredient"

    def test_update_recipe_partial(self, client, sample_recipe, auth_token):
        """Test partial update only changes specified fields."""
        original_description = sample_recipe.description

        response = client.put(
            f"/api/recipes/{sample_recipe.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"notes": "New notes only"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "New notes only"
        assert data["description"] == original_description

    def test_update_recipe_not_found(self, client, auth_token):
        """Test updating non-existent recipe returns 404."""
        response = client.put(
            "/api/recipes/non-existent-id",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Won't Work"},
        )

        assert response.status_code == 404


class TestDeleteRecipe:
    """Tests for DELETE /api/recipes/{recipe_id} endpoint."""

    def test_delete_recipe_owner(self, client, sample_recipe, auth_token, test_session):
        """Test owner can delete their recipe."""
        recipe_id = sample_recipe.id

        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

        # Verify it's actually deleted
        get_response = client.get(f"/api/recipes/{recipe_id}")
        assert get_response.status_code == 404

    def test_delete_recipe_not_owner(self, client, sample_recipe, another_auth_token):
        """Test non-owner cannot delete recipe."""
        response = client.delete(
            f"/api/recipes/{sample_recipe.id}",
            headers={"Authorization": f"Bearer {another_auth_token}"},
        )

        assert response.status_code == 403

    def test_delete_recipe_no_auth(self, client, sample_recipe):
        """Test unauthenticated user cannot delete owned recipe."""
        response = client.delete(f"/api/recipes/{sample_recipe.id}")

        assert response.status_code == 401

    def test_delete_recipe_orphan(self, client, orphan_recipe, test_session):
        """Test recipe without owner can be deleted by anyone."""
        recipe_id = orphan_recipe.id

        response = client.delete(f"/api/recipes/{recipe_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = client.get(f"/api/recipes/{recipe_id}")
        assert get_response.status_code == 404

    def test_delete_recipe_cascades(self, client, sample_recipe, auth_token, test_session):
        """Test deleting recipe also deletes its ingredients."""
        from app.models import RecipeIngredient

        recipe_id = sample_recipe.id

        # Verify ingredients exist before delete
        ingredients_before = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == recipe_id
        ).count()
        assert ingredients_before > 0

        # Delete the recipe
        response = client.delete(
            f"/api/recipes/{recipe_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

        # Verify ingredients are also deleted
        test_session.expire_all()
        ingredients_after = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == recipe_id
        ).count()
        assert ingredients_after == 0

    def test_delete_recipe_not_found(self, client, auth_token):
        """Test deleting non-existent recipe returns 404."""
        response = client.delete(
            "/api/recipes/non-existent-id",
            headers={"Authorization": f"Bearer {auth_token}"},
        )

        assert response.status_code == 404


class TestGetRecipeImage:
    """Tests for GET /api/recipes/{recipe_id}/image endpoint with streaming."""

    def test_get_image_not_found(self, client):
        """Test getting image for non-existent recipe returns 404."""
        response = client.get("/api/recipes/non-existent-id/image")
        assert response.status_code == 404

    def test_get_image_no_image(self, client, orphan_recipe):
        """Test getting image for recipe without image returns 404."""
        response = client.get(f"/api/recipes/{orphan_recipe.id}/image")
        assert response.status_code == 404
        assert "no image" in response.json()["detail"].lower()

    def test_get_image_streaming_full(self, client, test_session, tmp_path):
        """Test getting full image returns streaming response with correct headers."""
        from app.models import Recipe

        # Create a test image file
        image_data = b"FAKE_IMAGE_DATA_" * 1000  # ~16KB test data
        image_file = tmp_path / "test_image.jpg"
        image_file.write_bytes(image_data)

        # Create recipe with image path
        recipe = Recipe(
            name="Image Test Recipe",
            source_image_path=str(image_file),
            source_image_mime="image/jpeg",
        )
        test_session.add(recipe)
        test_session.commit()

        # Mock the image storage to return our test file path
        with patch("app.routers.recipes.get_image_storage") as mock_storage:
            mock_service = MagicMock()
            mock_service.get_image_path.return_value = image_file
            mock_storage.return_value = mock_service

            response = client.get(f"/api/recipes/{recipe.id}/image")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"
            assert response.headers["accept-ranges"] == "bytes"
            assert response.headers["content-length"] == str(len(image_data))
            assert "cache-control" in response.headers
            assert response.content == image_data

    def test_get_image_range_request(self, client, test_session, tmp_path):
        """Test range request returns partial content (206)."""
        from app.models import Recipe

        # Create a test image file
        image_data = b"0123456789" * 100  # 1000 bytes
        image_file = tmp_path / "range_test.jpg"
        image_file.write_bytes(image_data)

        # Create recipe with image path
        recipe = Recipe(
            name="Range Test Recipe",
            source_image_path=str(image_file),
            source_image_mime="image/jpeg",
        )
        test_session.add(recipe)
        test_session.commit()

        with patch("app.routers.recipes.get_image_storage") as mock_storage:
            mock_service = MagicMock()
            mock_service.get_image_path.return_value = image_file
            mock_storage.return_value = mock_service

            # Request bytes 0-99 (first 100 bytes)
            response = client.get(
                f"/api/recipes/{recipe.id}/image",
                headers={"Range": "bytes=0-99"},
            )

            assert response.status_code == 206
            assert response.headers["content-range"] == "bytes 0-99/1000"
            assert response.headers["content-length"] == "100"
            assert len(response.content) == 100
            assert response.content == image_data[:100]

    def test_get_image_range_request_suffix(self, client, test_session, tmp_path):
        """Test range request with suffix (last N bytes)."""
        from app.models import Recipe

        image_data = b"0123456789" * 100  # 1000 bytes
        image_file = tmp_path / "suffix_test.jpg"
        image_file.write_bytes(image_data)

        recipe = Recipe(
            name="Suffix Range Test",
            source_image_path=str(image_file),
            source_image_mime="image/jpeg",
        )
        test_session.add(recipe)
        test_session.commit()

        with patch("app.routers.recipes.get_image_storage") as mock_storage:
            mock_service = MagicMock()
            mock_service.get_image_path.return_value = image_file
            mock_storage.return_value = mock_service

            # Request last 50 bytes
            response = client.get(
                f"/api/recipes/{recipe.id}/image",
                headers={"Range": "bytes=-50"},
            )

            assert response.status_code == 206
            assert response.headers["content-range"] == "bytes 950-999/1000"
            assert len(response.content) == 50
            assert response.content == image_data[-50:]

    def test_get_image_range_request_open_end(self, client, test_session, tmp_path):
        """Test range request with open end (from N to end)."""
        from app.models import Recipe

        image_data = b"0123456789" * 100  # 1000 bytes
        image_file = tmp_path / "open_end_test.jpg"
        image_file.write_bytes(image_data)

        recipe = Recipe(
            name="Open End Range Test",
            source_image_path=str(image_file),
            source_image_mime="image/jpeg",
        )
        test_session.add(recipe)
        test_session.commit()

        with patch("app.routers.recipes.get_image_storage") as mock_storage:
            mock_service = MagicMock()
            mock_service.get_image_path.return_value = image_file
            mock_storage.return_value = mock_service

            # Request from byte 900 to end
            response = client.get(
                f"/api/recipes/{recipe.id}/image",
                headers={"Range": "bytes=900-"},
            )

            assert response.status_code == 206
            assert response.headers["content-range"] == "bytes 900-999/1000"
            assert len(response.content) == 100
            assert response.content == image_data[900:]

    def test_get_image_invalid_range(self, client, test_session, tmp_path):
        """Test invalid range request returns 416."""
        from app.models import Recipe

        image_data = b"0123456789" * 100  # 1000 bytes
        image_file = tmp_path / "invalid_range_test.jpg"
        image_file.write_bytes(image_data)

        recipe = Recipe(
            name="Invalid Range Test",
            source_image_path=str(image_file),
            source_image_mime="image/jpeg",
        )
        test_session.add(recipe)
        test_session.commit()

        with patch("app.routers.recipes.get_image_storage") as mock_storage:
            mock_service = MagicMock()
            mock_service.get_image_path.return_value = image_file
            mock_storage.return_value = mock_service

            # Request range beyond file size
            response = client.get(
                f"/api/recipes/{recipe.id}/image",
                headers={"Range": "bytes=2000-3000"},
            )

            assert response.status_code == 416
            assert "content-range" in response.headers
            assert response.headers["content-range"] == "bytes */1000"

    def test_get_image_legacy_blob(self, client, test_session):
        """Test legacy BLOB images still work (without streaming)."""
        from app.models import Recipe

        # Create recipe with legacy BLOB storage
        recipe = Recipe(
            name="Legacy BLOB Recipe",
            source_image_data=b"LEGACY_IMAGE_DATA",
            source_image_mime="image/png",
        )
        test_session.add(recipe)
        test_session.commit()

        response = client.get(f"/api/recipes/{recipe.id}/image")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["accept-ranges"] == "none"  # No range support for BLOB
        assert response.content == b"LEGACY_IMAGE_DATA"


class TestUploaderName:
    """Tests for uploader_name field on recipes."""

    def test_uploader_name_with_display_name(self, client, sample_recipe, sample_user):
        """Test uploader_name shows display_name when available."""
        # sample_user has display_name='Test User' from conftest
        response = client.get(f"/api/recipes/{sample_recipe.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["uploader_name"] == "Test User"

    def test_uploader_name_fallback_to_email_prefix(self, client, test_session):
        """Test uploader_name falls back to email prefix when display_name is null."""
        from app.models import Recipe, User

        # Create user without display_name
        user = User(
            email="nodisplay@example.com",
            hashed_password="fakehash",
            display_name=None,
        )
        test_session.add(user)
        test_session.flush()

        # Create recipe owned by this user
        recipe = Recipe(
            name="No Display Name Recipe",
            user_id=user.id,
        )
        test_session.add(recipe)
        test_session.commit()

        response = client.get(f"/api/recipes/{recipe.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["uploader_name"] == "nodisplay"  # email prefix

    def test_uploader_name_null_for_anonymous_recipe(self, client, orphan_recipe):
        """Test uploader_name is null for recipes without user."""
        response = client.get(f"/api/recipes/{orphan_recipe.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["uploader_name"] is None

    def test_uploader_name_in_list_response(self, client, sample_recipe, sample_user):
        """Test uploader_name appears in list endpoint response."""
        response = client.get("/api/recipes")

        assert response.status_code == 200
        data = response.json()
        # Find our sample recipe
        sample = next(r for r in data if r["id"] == sample_recipe.id)
        assert sample["uploader_name"] == "Test User"

    def test_uploader_name_null_in_list_for_orphan(self, client, orphan_recipe):
        """Test uploader_name is null in list for orphan recipes."""
        response = client.get("/api/recipes")

        assert response.status_code == 200
        data = response.json()
        # Find the orphan recipe
        orphan = next(r for r in data if r["id"] == orphan_recipe.id)
        assert orphan["uploader_name"] is None
