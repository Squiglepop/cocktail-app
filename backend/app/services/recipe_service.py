"""
Recipe-related business logic and helpers.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Recipe, Ingredient, RecipeIngredient
from app.schemas import RecipeIngredientCreate


def get_or_create_ingredient(
    db: Session,
    *,
    ingredient_id: Optional[str] = None,
    ingredient_name: Optional[str] = None,
    ingredient_type: Optional[str] = None,
) -> Optional[Ingredient]:
    """
    Get an existing ingredient by ID or name, or create a new one.

    Args:
        db: Database session
        ingredient_id: Existing ingredient ID to look up
        ingredient_name: Ingredient name to search/create
        ingredient_type: Type for new ingredient (defaults to "other")

    Returns:
        Ingredient instance or None if no valid identifier provided

    Note:
        Uses db.flush() to get IDs for newly created ingredients but does NOT
        commit the transaction. Caller is responsible for committing or the
        changes will be lost when the session closes.
    """
    if ingredient_id:
        return db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()

    # Reject empty/whitespace-only names
    if ingredient_name and ingredient_name.strip():
        ingredient = (
            db.query(Ingredient)
            .filter(Ingredient.name.ilike(ingredient_name))
            .first()
        )
        if not ingredient:
            ingredient = Ingredient(
                name=ingredient_name,
                type=ingredient_type or "other",
            )
            db.add(ingredient)
            db.flush()
        return ingredient

    return None


def add_ingredients_to_recipe(
    db: Session,
    recipe: Recipe,
    ingredients_data: List[RecipeIngredientCreate],
) -> None:
    """
    Add ingredients to a recipe, creating new ingredients as needed.

    Args:
        db: Database session
        recipe: Recipe to add ingredients to
        ingredients_data: List of ingredient data to add

    Note:
        Uses db.flush() internally but does NOT commit. Caller must commit
        the transaction for changes to persist.
    """
    for idx, ing_data in enumerate(ingredients_data):
        ingredient = get_or_create_ingredient(
            db,
            ingredient_id=ing_data.ingredient_id,
            ingredient_name=ing_data.ingredient_name,
            ingredient_type=ing_data.ingredient_type,
        )

        if ingredient:
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                amount=ing_data.amount,
                unit=ing_data.unit,
                notes=ing_data.notes,
                optional=ing_data.optional,
                order=idx,
            )
            db.add(recipe_ingredient)


def replace_recipe_ingredients(
    db: Session,
    recipe: Recipe,
    ingredients_data: List[RecipeIngredientCreate],
) -> None:
    """
    Replace all ingredients on a recipe (for updates).

    Args:
        db: Database session
        recipe: Recipe to update ingredients for
        ingredients_data: New ingredient list

    Note:
        Deletes existing recipe-ingredient links and creates new ones.
        Uses db.flush() but does NOT commit. Caller must commit the transaction.
    """
    # Delete existing ingredients
    db.query(RecipeIngredient).filter(
        RecipeIngredient.recipe_id == recipe.id
    ).delete()
    db.flush()

    # Add new ingredients
    add_ingredients_to_recipe(db, recipe, ingredients_data)
