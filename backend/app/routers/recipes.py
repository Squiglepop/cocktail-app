"""
Recipe CRUD endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Recipe,
    Ingredient,
    RecipeIngredient,
)
from app.schemas import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    RecipeListResponse,
)
from app.services import get_db


router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=List[RecipeListResponse])
def list_recipes(
    template: Optional[str] = None,
    main_spirit: Optional[str] = None,
    glassware: Optional[str] = None,
    serving_style: Optional[str] = None,
    method: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List recipes with optional filters."""
    query = db.query(Recipe)

    # Apply filters
    if template:
        query = query.filter(Recipe.template == template)
    if main_spirit:
        query = query.filter(Recipe.main_spirit == main_spirit)
    if glassware:
        query = query.filter(Recipe.glassware == glassware)
    if serving_style:
        query = query.filter(Recipe.serving_style == serving_style)
    if method:
        query = query.filter(Recipe.method == method)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(Recipe.name.ilike(search_term), Recipe.description.ilike(search_term))
        )

    # Order and paginate
    query = query.order_by(Recipe.created_at.desc())
    recipes = query.offset(skip).limit(limit).all()

    return recipes


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Get a single recipe by ID."""
    recipe = (
        db.query(Recipe)
        .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
        .filter(Recipe.id == recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return recipe


@router.post("", response_model=RecipeResponse)
def create_recipe(recipe_data: RecipeCreate, db: Session = Depends(get_db)):
    """Create a new recipe."""
    # Create the recipe
    recipe = Recipe(
        name=recipe_data.name,
        description=recipe_data.description,
        instructions=recipe_data.instructions,
        template=recipe_data.template,
        main_spirit=recipe_data.main_spirit,
        glassware=recipe_data.glassware,
        serving_style=recipe_data.serving_style,
        method=recipe_data.method,
        garnish=recipe_data.garnish,
        notes=recipe_data.notes,
        source_type="manual",
    )

    db.add(recipe)
    db.flush()  # Get the recipe ID

    # Add ingredients
    for idx, ing_data in enumerate(recipe_data.ingredients):
        # Get or create ingredient
        ingredient = None
        if ing_data.ingredient_id:
            ingredient = db.query(Ingredient).filter(Ingredient.id == ing_data.ingredient_id).first()
        elif ing_data.ingredient_name:
            ingredient = (
                db.query(Ingredient)
                .filter(Ingredient.name.ilike(ing_data.ingredient_name))
                .first()
            )
            if not ingredient:
                ingredient = Ingredient(
                    name=ing_data.ingredient_name,
                    type=ing_data.ingredient_type or "other",
                )
                db.add(ingredient)
                db.flush()

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

    db.commit()
    db.refresh(recipe)

    # Load relationships for response
    recipe = (
        db.query(Recipe)
        .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
        .filter(Recipe.id == recipe.id)
        .first()
    )

    return recipe


@router.put("/{recipe_id}", response_model=RecipeResponse)
def update_recipe(
    recipe_id: str, recipe_data: RecipeUpdate, db: Session = Depends(get_db)
):
    """Update a recipe."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Update scalar fields
    update_data = recipe_data.model_dump(exclude_unset=True, exclude={"ingredients"})
    for field, value in update_data.items():
        setattr(recipe, field, value)

    # Update ingredients if provided
    if recipe_data.ingredients is not None:
        # Remove existing ingredients
        db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe_id).delete()

        # Add new ingredients
        for idx, ing_data in enumerate(recipe_data.ingredients):
            ingredient = None
            if ing_data.ingredient_id:
                ingredient = db.query(Ingredient).filter(Ingredient.id == ing_data.ingredient_id).first()
            elif ing_data.ingredient_name:
                ingredient = (
                    db.query(Ingredient)
                    .filter(Ingredient.name.ilike(ing_data.ingredient_name))
                    .first()
                )
                if not ingredient:
                    ingredient = Ingredient(
                        name=ing_data.ingredient_name,
                        type=ing_data.ingredient_type or "other",
                    )
                    db.add(ingredient)
                    db.flush()

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

    db.commit()
    db.refresh(recipe)

    # Load relationships
    recipe = (
        db.query(Recipe)
        .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
        .filter(Recipe.id == recipe.id)
        .first()
    )

    return recipe


@router.delete("/{recipe_id}")
def delete_recipe(recipe_id: str, db: Session = Depends(get_db)):
    """Delete a recipe."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    db.delete(recipe)
    db.commit()

    return {"message": "Recipe deleted successfully"}
