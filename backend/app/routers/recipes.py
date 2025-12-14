"""
Recipe CRUD endpoints.
"""
from pathlib import Path
from typing import Generator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Recipe,
    Ingredient,
    RecipeIngredient,
    User,
    UserRating,
    Visibility,
)
from app.schemas import (
    RecipeCreate,
    RecipeUpdate,
    RecipeRatingUpdate,
    RecipeResponse,
    RecipeListResponse,
    RecipeIngredientResponse,
    IngredientResponse,
)
from app.services import get_db, get_image_storage
from app.services.auth import get_current_user, get_current_user_optional


router = APIRouter(prefix="/recipes", tags=["recipes"])


def _apply_visibility_filter(query, current_user: Optional[User], include_own: bool = True):
    """
    Apply visibility filtering to a recipe query.
    - Public recipes are visible to everyone
    - Private recipes are only visible to their owner
    - Group recipes are placeholder (treated as private for now)
    """
    if current_user and include_own:
        # User can see: public recipes OR their own recipes (any visibility)
        query = query.filter(
            or_(
                Recipe.visibility == Visibility.PUBLIC.value,
                Recipe.user_id == current_user.id
            )
        )
    else:
        # Anonymous users only see public recipes
        query = query.filter(Recipe.visibility == Visibility.PUBLIC.value)
    return query


@router.get("/count")
def get_recipe_count(
    template: Optional[str] = None,
    main_spirit: Optional[str] = None,
    glassware: Optional[str] = None,
    serving_style: Optional[str] = None,
    method: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    visibility: Optional[str] = Query(None, description="Filter by visibility"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by minimum personal rating"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get total recipe count and filtered count."""
    # Get total count (respecting visibility)
    total_query = db.query(Recipe)
    total_query = _apply_visibility_filter(total_query, current_user)
    total = total_query.count()

    # Build filtered query
    query = db.query(Recipe)
    query = _apply_visibility_filter(query, current_user)

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
    if user_id:
        query = query.filter(Recipe.user_id == user_id)
    if visibility:
        query = query.filter(Recipe.visibility == visibility)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(Recipe.name.ilike(search_term), Recipe.description.ilike(search_term))
        )
    if min_rating and current_user:
        # Filter by user's personal rating
        query = query.join(UserRating, UserRating.recipe_id == Recipe.id).filter(
            UserRating.user_id == current_user.id,
            UserRating.rating >= min_rating
        )

    filtered = query.count()

    return {"total": total, "filtered": filtered}


@router.get("", response_model=List[RecipeListResponse])
def list_recipes(
    template: Optional[str] = None,
    main_spirit: Optional[str] = None,
    glassware: Optional[str] = None,
    serving_style: Optional[str] = None,
    method: Optional[str] = None,
    search: Optional[str] = None,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    visibility: Optional[str] = Query(None, description="Filter by visibility"),
    min_rating: Optional[int] = Query(None, ge=1, le=5, description="Filter by minimum personal rating"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """List recipes with optional filters. Respects visibility settings."""
    query = db.query(Recipe)

    # Apply visibility filter
    query = _apply_visibility_filter(query, current_user)

    # Apply other filters
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
    if user_id:
        query = query.filter(Recipe.user_id == user_id)
    if visibility:
        query = query.filter(Recipe.visibility == visibility)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(Recipe.name.ilike(search_term), Recipe.description.ilike(search_term))
        )
    if min_rating and current_user:
        # Filter by user's personal rating
        query = query.join(UserRating, UserRating.recipe_id == Recipe.id).filter(
            UserRating.user_id == current_user.id,
            UserRating.rating >= min_rating
        )

    # Order and paginate
    query = query.order_by(Recipe.created_at.desc())
    recipes = query.offset(skip).limit(limit).all()

    # Get user's ratings for these recipes if authenticated
    user_ratings_map = {}
    if current_user:
        recipe_ids = [r.id for r in recipes]
        if recipe_ids:
            user_ratings = (
                db.query(UserRating)
                .filter(
                    UserRating.user_id == current_user.id,
                    UserRating.recipe_id.in_(recipe_ids)
                )
                .all()
            )
            user_ratings_map = {ur.recipe_id: ur.rating for ur in user_ratings}

    # Build response with user's rating
    result = []
    for recipe in recipes:
        recipe_dict = {
            "id": recipe.id,
            "name": recipe.name,
            "template": recipe.template,
            "main_spirit": recipe.main_spirit,
            "glassware": recipe.glassware,
            "serving_style": recipe.serving_style,
            "has_image": recipe.has_image,
            "user_id": recipe.user_id,
            "visibility": recipe.visibility,
            "my_rating": user_ratings_map.get(recipe.id),
            "created_at": recipe.created_at,
        }
        result.append(RecipeListResponse(**recipe_dict))

    return result


@router.get("/{recipe_id}", response_model=RecipeResponse)
def get_recipe(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get a single recipe by ID. Respects visibility settings."""
    recipe = (
        db.query(Recipe)
        .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
        .filter(Recipe.id == recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check visibility
    is_owner = current_user and recipe.user_id == current_user.id
    if recipe.visibility != Visibility.PUBLIC.value and not is_owner:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Get current user's rating for this recipe
    my_rating = None
    if current_user:
        user_rating = (
            db.query(UserRating)
            .filter(
                UserRating.user_id == current_user.id,
                UserRating.recipe_id == recipe_id
            )
            .first()
        )
        if user_rating:
            my_rating = user_rating.rating

    # Build response manually to include my_rating
    return RecipeResponse(
        id=recipe.id,
        name=recipe.name,
        description=recipe.description,
        instructions=recipe.instructions,
        template=recipe.template,
        main_spirit=recipe.main_spirit,
        glassware=recipe.glassware,
        serving_style=recipe.serving_style,
        method=recipe.method,
        garnish=recipe.garnish,
        notes=recipe.notes,
        source_url=recipe.source_url,
        source_type=recipe.source_type,
        user_id=recipe.user_id,
        visibility=recipe.visibility,
        my_rating=my_rating,
        has_image=recipe.has_image,
        created_at=recipe.created_at,
        updated_at=recipe.updated_at,
        ingredients=[
            RecipeIngredientResponse(
                id=ri.id,
                amount=ri.amount,
                unit=ri.unit,
                notes=ri.notes,
                optional=ri.optional,
                order=ri.order,
                ingredient=IngredientResponse(
                    id=ri.ingredient.id,
                    name=ri.ingredient.name,
                    type=ri.ingredient.type,
                    spirit_category=ri.ingredient.spirit_category,
                    description=ri.ingredient.description,
                    common_brands=ri.ingredient.common_brands,
                )
            )
            for ri in recipe.ingredients
        ]
    )


def _stream_file(
    file_path: Path, start: int = 0, end: Optional[int] = None, chunk_size: int = 64 * 1024
) -> Generator[bytes, None, None]:
    """Stream file contents in chunks for memory-efficient serving.

    Args:
        file_path: Path to the file to stream
        start: Byte offset to start reading from (for range requests)
        end: Byte offset to stop reading at (inclusive, for range requests)
        chunk_size: Size of chunks to yield (default 64KB)
    """
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = (end - start + 1) if end is not None else None

        while True:
            read_size = min(chunk_size, remaining) if remaining is not None else chunk_size
            chunk = f.read(read_size)
            if not chunk:
                break
            yield chunk
            if remaining is not None:
                remaining -= len(chunk)
                if remaining <= 0:
                    break


def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    """Parse HTTP Range header and return (start, end) byte positions.

    Supports formats: "bytes=0-499", "bytes=500-", "bytes=-500"
    """
    if not range_header.startswith("bytes="):
        raise ValueError("Invalid range header format")

    range_spec = range_header[6:]  # Remove "bytes=" prefix

    if range_spec.startswith("-"):
        # Last N bytes: "bytes=-500"
        suffix_length = int(range_spec[1:])
        start = max(0, file_size - suffix_length)
        end = file_size - 1
    elif range_spec.endswith("-"):
        # From start to end: "bytes=500-"
        start = int(range_spec[:-1])
        end = file_size - 1
    else:
        # Specific range: "bytes=0-499"
        parts = range_spec.split("-")
        start = int(parts[0])
        end = min(int(parts[1]), file_size - 1)

    if start > end or start >= file_size:
        raise ValueError("Invalid range")

    return start, end


@router.get("/{recipe_id}/image")
def get_recipe_image(
    recipe_id: str, request: Request, db: Session = Depends(get_db)
):
    """Get the source image for a recipe.

    Supports HTTP Range requests for efficient streaming to mobile devices.
    Uses chunked streaming to minimize memory usage.
    """
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    media_type = recipe.source_image_mime or "image/jpeg"
    cache_headers = {"Cache-Control": "public, max-age=86400"}  # Cache for 24h

    # Prefer filesystem storage, fall back to DB BLOB for legacy data
    if recipe.source_image_path:
        image_storage = get_image_storage()
        image_path = image_storage.get_image_path(recipe.source_image_path)
        if not image_path.exists():
            raise HTTPException(status_code=404, detail="Image file not found")

        file_size = image_path.stat().st_size
        range_header = request.headers.get("range")

        if range_header:
            # Handle range request for partial content (mobile optimization)
            try:
                start, end = _parse_range_header(range_header, file_size)
            except ValueError:
                raise HTTPException(
                    status_code=416,
                    detail="Requested range not satisfiable",
                    headers={"Content-Range": f"bytes */{file_size}"},
                )

            content_length = end - start + 1
            headers = {
                **cache_headers,
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            }

            return StreamingResponse(
                _stream_file(image_path, start, end),
                status_code=206,
                media_type=media_type,
                headers=headers,
            )
        else:
            # Full file request - still stream for memory efficiency
            headers = {
                **cache_headers,
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            }

            return StreamingResponse(
                _stream_file(image_path),
                media_type=media_type,
                headers=headers,
            )

    elif recipe.source_image_data:
        # Legacy: serve from database BLOB (no streaming available)
        # Consider migrating these to filesystem storage
        return Response(
            content=recipe.source_image_data,
            media_type=media_type,
            headers={**cache_headers, "Accept-Ranges": "none"},
        )
    else:
        raise HTTPException(status_code=404, detail="No image available for this recipe")


@router.post("", response_model=RecipeResponse)
def create_recipe(
    recipe_data: RecipeCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Create a new recipe. Optionally associates with current user if authenticated."""
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
        user_id=current_user.id if current_user else None,
        visibility=recipe_data.visibility,
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
    recipe_id: str,
    recipe_data: RecipeUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Update a recipe. Only the owner can update their recipes."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check ownership - only owner can edit (or if recipe has no owner, anyone can edit for backwards compatibility)
    if recipe.user_id is not None:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to edit this recipe",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if recipe.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this recipe"
            )

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
def delete_recipe(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Delete a recipe. Only the owner can delete their recipes."""
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check ownership - only owner can delete (or if recipe has no owner, anyone can delete for backwards compatibility)
    if recipe.user_id is not None:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to delete this recipe",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if recipe.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this recipe"
            )

    # Delete image file from filesystem if it exists
    if recipe.source_image_path:
        image_storage = get_image_storage()
        image_storage.delete_image(recipe.source_image_path)

    db.delete(recipe)
    db.commit()

    return {"message": "Recipe deleted successfully"}


@router.put("/{recipe_id}/my-rating")
def set_my_rating(
    recipe_id: str,
    rating_data: RecipeRatingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set or update personal rating for any recipe in the library.
    Rating is private and only visible to the current user.
    """
    # Check recipe exists and is accessible
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check visibility - user must be able to see the recipe to rate it
    is_owner = recipe.user_id == current_user.id
    if recipe.visibility != Visibility.PUBLIC.value and not is_owner:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if rating_data.rating is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating is required"
        )

    # Find existing rating or create new one
    user_rating = (
        db.query(UserRating)
        .filter(
            UserRating.user_id == current_user.id,
            UserRating.recipe_id == recipe_id
        )
        .first()
    )

    if user_rating:
        user_rating.rating = rating_data.rating
    else:
        user_rating = UserRating(
            user_id=current_user.id,
            recipe_id=recipe_id,
            rating=rating_data.rating,
        )
        db.add(user_rating)

    db.commit()

    return {"message": "Rating updated", "rating": rating_data.rating}


@router.delete("/{recipe_id}/my-rating")
def delete_my_rating(
    recipe_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clear personal rating for a recipe.
    """
    # Check recipe exists
    recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Find and delete the user's rating
    user_rating = (
        db.query(UserRating)
        .filter(
            UserRating.user_id == current_user.id,
            UserRating.recipe_id == recipe_id
        )
        .first()
    )

    if user_rating:
        db.delete(user_rating)
        db.commit()

    return {"message": "Rating cleared"}
