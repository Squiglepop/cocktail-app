"""
Collection (Playlist) CRUD endpoints.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.models import Collection, CollectionRecipe, Recipe, User
from app.schemas import (
    CollectionCreate,
    CollectionUpdate,
    CollectionRecipeAdd,
    CollectionRecipeReorder,
    CollectionResponse,
    CollectionDetailResponse,
    CollectionListResponse,
    CollectionRecipeResponse,
)
from app.services import get_db
from app.services.auth import get_current_user, get_current_user_optional


router = APIRouter(prefix="/collections", tags=["collections"])


def _build_collection_recipe_response(cr: CollectionRecipe) -> CollectionRecipeResponse:
    """Build a CollectionRecipeResponse from a CollectionRecipe model."""
    return CollectionRecipeResponse(
        id=cr.id,
        recipe_id=cr.recipe_id,
        recipe_name=cr.recipe.name,
        recipe_template=cr.recipe.template,
        recipe_main_spirit=cr.recipe.main_spirit,
        recipe_has_image=cr.recipe.has_image,
        position=cr.position,
        added_at=cr.added_at,
    )


@router.get("", response_model=List[CollectionListResponse])
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_public: bool = Query(False, description="Include public collections from other users"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List collections. Returns user's own collections.
    If include_public=true, also returns public collections from other users.
    """
    query = db.query(Collection)

    if current_user:
        if include_public:
            # User's own + public from others
            query = query.filter(
                (Collection.user_id == current_user.id) | (Collection.is_public == True)
            )
        else:
            # Only user's own
            query = query.filter(Collection.user_id == current_user.id)
    else:
        # Anonymous: only public collections
        query = query.filter(Collection.is_public == True)

    query = query.order_by(Collection.updated_at.desc())
    collections = query.offset(skip).limit(limit).all()

    return [
        CollectionListResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            is_public=c.is_public,
            recipe_count=c.recipe_count,
            created_at=c.created_at,
        )
        for c in collections
    ]


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get a collection with its recipes."""
    collection = (
        db.query(Collection)
        .options(joinedload(Collection.collection_recipes).joinedload(CollectionRecipe.recipe))
        .filter(Collection.id == collection_id)
        .first()
    )

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Check access: owner or public
    if not collection.is_public:
        if current_user is None or collection.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Collection not found")

    # Sort recipes by position
    sorted_recipes = sorted(collection.collection_recipes, key=lambda cr: cr.position)

    return CollectionDetailResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        is_public=collection.is_public,
        user_id=collection.user_id,
        recipe_count=collection.recipe_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
        recipes=[_build_collection_recipe_response(cr) for cr in sorted_recipes],
    )


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    collection_data: CollectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new collection. Requires authentication."""
    collection = Collection(
        name=collection_data.name,
        description=collection_data.description,
        is_public=collection_data.is_public,
        user_id=current_user.id,
    )

    db.add(collection)
    db.commit()
    db.refresh(collection)

    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        is_public=collection.is_public,
        user_id=collection.user_id,
        recipe_count=0,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: str,
    collection_data: CollectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a collection. Only the owner can update."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this collection"
        )

    update_data = collection_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)

    db.commit()
    db.refresh(collection)

    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        description=collection.description,
        is_public=collection.is_public,
        user_id=collection.user_id,
        recipe_count=collection.recipe_count,
        created_at=collection.created_at,
        updated_at=collection.updated_at,
    )


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a collection. Only the owner can delete."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this collection"
        )

    db.delete(collection)
    db.commit()

    return {"message": "Collection deleted successfully"}


# --- Recipe management within collections ---

@router.post("/{collection_id}/recipes", response_model=CollectionRecipeResponse, status_code=status.HTTP_201_CREATED)
async def add_recipe_to_collection(
    collection_id: str,
    recipe_add: CollectionRecipeAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a recipe to a collection. Only the owner can modify."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this collection"
        )

    # Check recipe exists
    recipe = db.query(Recipe).filter(Recipe.id == recipe_add.recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Check if recipe already in collection
    existing = (
        db.query(CollectionRecipe)
        .filter(
            CollectionRecipe.collection_id == collection_id,
            CollectionRecipe.recipe_id == recipe_add.recipe_id
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Recipe already in collection")

    # Determine position
    if recipe_add.position is not None:
        position = recipe_add.position
    else:
        # Add to end
        max_pos = (
            db.query(CollectionRecipe)
            .filter(CollectionRecipe.collection_id == collection_id)
            .count()
        )
        position = max_pos

    collection_recipe = CollectionRecipe(
        collection_id=collection_id,
        recipe_id=recipe_add.recipe_id,
        position=position,
    )

    db.add(collection_recipe)
    db.commit()
    db.refresh(collection_recipe)

    # Load recipe for response
    collection_recipe = (
        db.query(CollectionRecipe)
        .options(joinedload(CollectionRecipe.recipe))
        .filter(CollectionRecipe.id == collection_recipe.id)
        .first()
    )

    return _build_collection_recipe_response(collection_recipe)


@router.delete("/{collection_id}/recipes/{recipe_id}")
async def remove_recipe_from_collection(
    collection_id: str,
    recipe_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a recipe from a collection. Only the owner can modify."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this collection"
        )

    collection_recipe = (
        db.query(CollectionRecipe)
        .filter(
            CollectionRecipe.collection_id == collection_id,
            CollectionRecipe.recipe_id == recipe_id
        )
        .first()
    )

    if not collection_recipe:
        raise HTTPException(status_code=404, detail="Recipe not in collection")

    db.delete(collection_recipe)
    db.commit()

    return {"message": "Recipe removed from collection"}


@router.put("/{collection_id}/recipes/reorder")
async def reorder_collection_recipes(
    collection_id: str,
    reorder_data: List[CollectionRecipeReorder],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reorder recipes in a collection. Only the owner can modify."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if collection.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this collection"
        )

    for item in reorder_data:
        collection_recipe = (
            db.query(CollectionRecipe)
            .filter(
                CollectionRecipe.collection_id == collection_id,
                CollectionRecipe.recipe_id == item.recipe_id
            )
            .first()
        )
        if collection_recipe:
            collection_recipe.position = item.position

    db.commit()

    return {"message": "Collection reordered successfully"}
