"""
Tests for recipe CRUD endpoints.
"""
import pytest


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
