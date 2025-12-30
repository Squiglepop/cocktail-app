"""
Unit tests for recipe service.
"""
import pytest

from app.services.recipe_service import (
    get_or_create_ingredient,
    add_ingredients_to_recipe,
    replace_recipe_ingredients,
)
from app.models import Recipe, Ingredient, RecipeIngredient
from app.schemas import RecipeIngredientCreate


class TestGetOrCreateIngredient:
    """Tests for get_or_create_ingredient function."""

    def test_lookup_by_id_existing(self, test_session, sample_ingredient):
        """Test looking up existing ingredient by ID."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_id=sample_ingredient.id,
        )

        assert result is not None
        assert result.id == sample_ingredient.id
        assert result.name == sample_ingredient.name

    def test_lookup_by_id_nonexistent(self, test_session):
        """Test looking up non-existent ingredient by ID returns None."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_id="nonexistent-uuid-12345",
        )

        assert result is None

    def test_lookup_by_name_existing_exact_case(self, test_session, sample_ingredient):
        """Test looking up existing ingredient by exact name match."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_name=sample_ingredient.name,
        )

        assert result is not None
        assert result.id == sample_ingredient.id
        assert result.name == sample_ingredient.name

    def test_lookup_by_name_existing_case_insensitive(self, test_session, sample_ingredient):
        """Test looking up existing ingredient with different case."""
        # sample_ingredient.name is "Tequila"
        result = get_or_create_ingredient(
            test_session,
            ingredient_name="TEQUILA",
        )

        assert result is not None
        assert result.id == sample_ingredient.id

    def test_lookup_by_name_existing_lowercase(self, test_session, sample_ingredient):
        """Test looking up existing ingredient with lowercase name."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_name="tequila",
        )

        assert result is not None
        assert result.id == sample_ingredient.id

    def test_create_new_ingredient_with_name(self, test_session):
        """Test creating a new ingredient when name doesn't exist."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_name="Fresh Lime Juice",
            ingredient_type="juice",
        )

        assert result is not None
        assert result.name == "Fresh Lime Juice"
        assert result.type == "juice"

        # Verify it was added to the session
        found = test_session.query(Ingredient).filter(
            Ingredient.name == "Fresh Lime Juice"
        ).first()
        assert found is not None
        assert found.id == result.id

    def test_create_new_ingredient_default_type(self, test_session):
        """Test creating new ingredient uses 'other' as default type."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_name="Mystery Ingredient",
        )

        assert result is not None
        assert result.type == "other"

    def test_no_identifier_returns_none(self, test_session):
        """Test that no identifier provided returns None."""
        result = get_or_create_ingredient(test_session)

        assert result is None

    def test_empty_name_returns_none(self, test_session):
        """Test that empty string name returns None."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_name="",
        )

        assert result is None

    def test_whitespace_only_name_returns_none(self, test_session):
        """Test that whitespace-only name returns None."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_name="   ",
        )

        assert result is None

    def test_none_name_returns_none(self, test_session):
        """Test that None name returns None."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_name=None,
        )

        assert result is None

    def test_id_takes_precedence_over_name(self, test_session, sample_ingredient):
        """Test that ingredient_id lookup is tried before name."""
        result = get_or_create_ingredient(
            test_session,
            ingredient_id=sample_ingredient.id,
            ingredient_name="Some Other Name",
        )

        assert result is not None
        assert result.id == sample_ingredient.id
        assert result.name == sample_ingredient.name  # Not "Some Other Name"


class TestAddIngredientsToRecipe:
    """Tests for add_ingredients_to_recipe function."""

    @pytest.fixture
    def empty_recipe(self, test_session, sample_user):
        """Create an empty recipe without ingredients."""
        recipe = Recipe(
            name="Test Recipe",
            description="A test recipe",
            instructions="Test instructions",
            user_id=sample_user.id,
        )
        test_session.add(recipe)
        test_session.flush()
        return recipe

    def test_add_single_ingredient(self, test_session, empty_recipe, sample_ingredient):
        """Test adding a single ingredient to a recipe."""
        ingredients_data = [
            RecipeIngredientCreate(
                ingredient_id=sample_ingredient.id,
                amount=2.0,
                unit="oz",
            )
        ]

        add_ingredients_to_recipe(test_session, empty_recipe, ingredients_data)
        test_session.flush()

        recipe_ingredients = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == empty_recipe.id
        ).all()

        assert len(recipe_ingredients) == 1
        assert recipe_ingredients[0].ingredient_id == sample_ingredient.id
        assert recipe_ingredients[0].amount == 2.0
        assert recipe_ingredients[0].unit == "oz"
        assert recipe_ingredients[0].order == 0

    def test_add_multiple_ingredients_correct_order(self, test_session, empty_recipe):
        """Test that multiple ingredients are added with correct order values."""
        ingredients_data = [
            RecipeIngredientCreate(
                ingredient_name="Gin",
                ingredient_type="spirit",
                amount=2.0,
                unit="oz",
            ),
            RecipeIngredientCreate(
                ingredient_name="Lemon Juice",
                ingredient_type="juice",
                amount=0.75,
                unit="oz",
            ),
            RecipeIngredientCreate(
                ingredient_name="Simple Syrup",
                ingredient_type="sweetener",
                amount=0.75,
                unit="oz",
            ),
        ]

        add_ingredients_to_recipe(test_session, empty_recipe, ingredients_data)
        test_session.flush()

        recipe_ingredients = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == empty_recipe.id
        ).order_by(RecipeIngredient.order).all()

        assert len(recipe_ingredients) == 3
        assert recipe_ingredients[0].order == 0
        assert recipe_ingredients[1].order == 1
        assert recipe_ingredients[2].order == 2

        # Verify the ingredients were created
        gin = test_session.query(Ingredient).filter(Ingredient.name == "Gin").first()
        assert gin is not None
        assert recipe_ingredients[0].ingredient_id == gin.id

    def test_add_ingredients_with_optional_fields(self, test_session, empty_recipe, sample_ingredient):
        """Test adding ingredients with optional fields (notes, optional flag)."""
        ingredients_data = [
            RecipeIngredientCreate(
                ingredient_id=sample_ingredient.id,
                amount=2.0,
                unit="oz",
                notes="Use reposado",
                optional=True,
            )
        ]

        add_ingredients_to_recipe(test_session, empty_recipe, ingredients_data)
        test_session.flush()

        recipe_ingredient = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == empty_recipe.id
        ).first()

        assert recipe_ingredient.notes == "Use reposado"
        assert recipe_ingredient.optional is True

    def test_add_empty_list(self, test_session, empty_recipe):
        """Test that adding empty ingredient list does nothing."""
        add_ingredients_to_recipe(test_session, empty_recipe, [])
        test_session.flush()

        recipe_ingredients = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == empty_recipe.id
        ).all()

        assert len(recipe_ingredients) == 0

    def test_skips_ingredient_with_invalid_name(self, test_session, empty_recipe):
        """Test that ingredients with empty names are skipped."""
        ingredients_data = [
            RecipeIngredientCreate(
                ingredient_name="Valid Ingredient",
                amount=1.0,
                unit="oz",
            ),
            RecipeIngredientCreate(
                ingredient_name="",  # Empty name - should be skipped
                amount=1.0,
                unit="oz",
            ),
            RecipeIngredientCreate(
                ingredient_name="Another Valid",
                amount=1.0,
                unit="oz",
            ),
        ]

        add_ingredients_to_recipe(test_session, empty_recipe, ingredients_data)
        test_session.flush()

        recipe_ingredients = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == empty_recipe.id
        ).all()

        # Only 2 valid ingredients should be added
        assert len(recipe_ingredients) == 2


class TestReplaceRecipeIngredients:
    """Tests for replace_recipe_ingredients function."""

    def test_replace_existing_ingredients(self, test_session, sample_recipe):
        """Test replacing existing ingredients with new ones."""
        # sample_recipe already has one ingredient (Tequila)
        initial_count = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == sample_recipe.id
        ).count()
        assert initial_count == 1

        new_ingredients = [
            RecipeIngredientCreate(
                ingredient_name="Vodka",
                ingredient_type="spirit",
                amount=2.0,
                unit="oz",
            ),
            RecipeIngredientCreate(
                ingredient_name="Cranberry Juice",
                ingredient_type="juice",
                amount=4.0,
                unit="oz",
            ),
        ]

        replace_recipe_ingredients(test_session, sample_recipe, new_ingredients)
        test_session.flush()

        recipe_ingredients = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == sample_recipe.id
        ).order_by(RecipeIngredient.order).all()

        assert len(recipe_ingredients) == 2

        # Verify the old Tequila ingredient link is gone
        tequila_links = [ri for ri in recipe_ingredients if ri.ingredient.name == "Tequila"]
        assert len(tequila_links) == 0

        # Verify new ingredients are present
        vodka = test_session.query(Ingredient).filter(Ingredient.name == "Vodka").first()
        cranberry = test_session.query(Ingredient).filter(Ingredient.name == "Cranberry Juice").first()
        assert vodka is not None
        assert cranberry is not None

    def test_replace_with_empty_list(self, test_session, sample_recipe):
        """Test replacing ingredients with empty list removes all."""
        initial_count = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == sample_recipe.id
        ).count()
        assert initial_count > 0

        replace_recipe_ingredients(test_session, sample_recipe, [])
        test_session.flush()

        final_count = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == sample_recipe.id
        ).count()
        assert final_count == 0

    def test_replace_preserves_order(self, test_session, sample_recipe):
        """Test that replacement maintains correct order values."""
        new_ingredients = [
            RecipeIngredientCreate(
                ingredient_name="First",
                amount=1.0,
                unit="oz",
            ),
            RecipeIngredientCreate(
                ingredient_name="Second",
                amount=2.0,
                unit="oz",
            ),
            RecipeIngredientCreate(
                ingredient_name="Third",
                amount=3.0,
                unit="oz",
            ),
        ]

        replace_recipe_ingredients(test_session, sample_recipe, new_ingredients)
        test_session.flush()

        recipe_ingredients = test_session.query(RecipeIngredient).filter(
            RecipeIngredient.recipe_id == sample_recipe.id
        ).order_by(RecipeIngredient.order).all()

        assert recipe_ingredients[0].order == 0
        assert recipe_ingredients[0].ingredient.name == "First"
        assert recipe_ingredients[1].order == 1
        assert recipe_ingredients[1].ingredient.name == "Second"
        assert recipe_ingredients[2].order == 2
        assert recipe_ingredients[2].ingredient.name == "Third"

    def test_does_not_delete_ingredient_entities(self, test_session, sample_recipe, sample_ingredient):
        """Test that replacing only deletes links, not the ingredients themselves."""
        # sample_recipe uses sample_ingredient (Tequila)
        ingredient_id = sample_ingredient.id

        new_ingredients = [
            RecipeIngredientCreate(
                ingredient_name="Vodka",
                amount=2.0,
                unit="oz",
            ),
        ]

        replace_recipe_ingredients(test_session, sample_recipe, new_ingredients)
        test_session.flush()

        # The Tequila ingredient should still exist in the database
        tequila = test_session.query(Ingredient).filter(
            Ingredient.id == ingredient_id
        ).first()
        assert tequila is not None
        assert tequila.name == "Tequila"
