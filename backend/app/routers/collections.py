"""
Collection (Playlist) CRUD endpoints.
"""
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.models import Collection, CollectionRecipe, CollectionShare, Recipe, User
from app.schemas import (
    CollectionCreate,
    CollectionUpdate,
    CollectionRecipeAdd,
    CollectionRecipeReorder,
    CollectionResponse,
    CollectionDetailResponse,
    CollectionListResponse,
    CollectionRecipeResponse,
    CollectionShareCreate,
    CollectionShareUpdate,
    CollectionShareResponse,
    CollectionShareListResponse,
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


def _get_user_share(collection_id: str, user_id: str, db: Session) -> Optional[CollectionShare]:
    """Get the share record for a user on a collection, if any."""
    return (
        db.query(CollectionShare)
        .filter(
            CollectionShare.collection_id == collection_id,
            CollectionShare.shared_with_user_id == user_id
        )
        .first()
    )


def _user_can_view_collection(collection: Collection, user: Optional[User], db: Session) -> bool:
    """Check if a user can view a collection (owner, shared with, or public)."""
    if collection.is_public:
        return True
    if user is None:
        return False
    if collection.user_id == user.id:
        return True
    # Check if shared with this user
    share = _get_user_share(collection.id, user.id, db)
    return share is not None


def _user_can_edit_collection(collection: Collection, user: User, db: Session) -> Tuple[bool, bool]:
    """
    Check if a user can edit a collection's recipes.
    Returns (can_edit, is_owner).
    Owner can always edit. Shared users can edit if can_edit=True on their share.
    """
    if collection.user_id == user.id:
        return True, True

    share = _get_user_share(collection.id, user.id, db)
    if share and share.can_edit:
        return True, False

    return False, False


def _user_is_owner(collection: Collection, user: User) -> bool:
    """Check if user is the owner of the collection."""
    return collection.user_id == user.id


@router.get("", response_model=List[CollectionListResponse])
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_public: bool = Query(False, description="Include public collections from other users"),
    include_shared: bool = Query(True, description="Include collections shared with me"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List collections. Returns user's own collections plus collections shared with them.
    If include_public=true, also returns public collections from other users.
    """
    # Build a map of shared collection IDs to their can_edit status
    shared_permissions = {}

    if current_user:
        if include_shared:
            shares = (
                db.query(CollectionShare.collection_id, CollectionShare.can_edit)
                .filter(CollectionShare.shared_with_user_id == current_user.id)
                .all()
            )
            shared_permissions = {s[0]: s[1] for s in shares}

        # Build query conditions
        conditions = [Collection.user_id == current_user.id]
        if shared_permissions:
            conditions.append(Collection.id.in_(shared_permissions.keys()))
        if include_public:
            conditions.append(Collection.is_public == True)

        query = db.query(Collection).options(joinedload(Collection.user)).filter(or_(*conditions))
    else:
        # Anonymous: only public collections
        query = db.query(Collection).options(joinedload(Collection.user)).filter(Collection.is_public == True)

    query = query.order_by(Collection.updated_at.desc())
    collections = query.offset(skip).limit(limit).all()

    # Build response with is_shared, can_edit, and owner_name info
    results = []
    for c in collections:
        is_owner = current_user is not None and c.user_id == current_user.id
        is_shared = current_user is not None and c.user_id != current_user.id

        # Determine can_edit: owner always can, shared users check permission
        can_edit = is_owner
        if not can_edit and c.id in shared_permissions:
            can_edit = shared_permissions[c.id]

        owner_name = None
        if is_shared:
            owner_name = c.user.display_name or c.user.email

        results.append(
            CollectionListResponse(
                id=c.id,
                name=c.name,
                description=c.description,
                is_public=c.is_public,
                recipe_count=c.recipe_count,
                created_at=c.created_at,
                is_shared=is_shared,
                can_edit=can_edit,
                owner_name=owner_name,
            )
        )

    return results


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

    # Check access: owner, shared with, or public
    if not _user_can_view_collection(collection, current_user, db):
        raise HTTPException(status_code=404, detail="Collection not found")

    # Sort recipes by position
    sorted_recipes = sorted(collection.collection_recipes, key=lambda cr: cr.position)

    # Determine is_shared and can_edit
    is_shared = False
    can_edit = False
    if current_user:
        is_owner = collection.user_id == current_user.id
        if is_owner:
            can_edit = True
        else:
            is_shared = True
            share = _get_user_share(collection.id, current_user.id, db)
            if share and share.can_edit:
                can_edit = True

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
        is_shared=is_shared,
        can_edit=can_edit,
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
    """Update a collection's metadata (name, description, visibility). Only the owner can update."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not _user_is_owner(collection, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit this collection's settings"
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

    if not _user_is_owner(collection, current_user):
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
    """Add a recipe to a collection. Owner or users with edit permission can modify."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    can_edit, _ = _user_can_edit_collection(collection, current_user, db)
    if not can_edit:
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
    """Remove a recipe from a collection. Owner or users with edit permission can modify."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    can_edit, _ = _user_can_edit_collection(collection, current_user, db)
    if not can_edit:
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
    """Reorder recipes in a collection. Owner or users with edit permission can modify."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    can_edit, _ = _user_can_edit_collection(collection, current_user, db)
    if not can_edit:
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


# --- Collection Sharing ---

@router.get("/{collection_id}/shares", response_model=CollectionShareListResponse)
async def list_collection_shares(
    collection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users a collection is shared with. Only the owner can view."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not _user_is_owner(collection, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view shares for this collection"
        )

    shares = (
        db.query(CollectionShare)
        .options(joinedload(CollectionShare.shared_with_user))
        .filter(CollectionShare.collection_id == collection_id)
        .order_by(CollectionShare.shared_at.desc())
        .all()
    )

    return CollectionShareListResponse(
        shares=[
            CollectionShareResponse(
                id=s.id,
                collection_id=s.collection_id,
                shared_with_user_id=s.shared_with_user_id,
                shared_with_email=s.shared_with_user.email,
                shared_with_display_name=s.shared_with_user.display_name,
                can_edit=s.can_edit,
                shared_at=s.shared_at,
            )
            for s in shares
        ]
    )


@router.post("/{collection_id}/shares", response_model=CollectionShareResponse, status_code=status.HTTP_201_CREATED)
async def share_collection(
    collection_id: str,
    share_data: CollectionShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Share a collection with another user by email. Only the owner can share."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not _user_is_owner(collection, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this collection"
        )

    # Find user by email
    target_user = db.query(User).filter(User.email == share_data.email.lower()).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found with that email")

    # Can't share with yourself
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share a collection with yourself")

    # Check if already shared
    existing = (
        db.query(CollectionShare)
        .filter(
            CollectionShare.collection_id == collection_id,
            CollectionShare.shared_with_user_id == target_user.id
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Collection is already shared with this user")

    # Create share
    share = CollectionShare(
        collection_id=collection_id,
        shared_with_user_id=target_user.id,
        can_edit=share_data.can_edit,
    )

    db.add(share)
    db.commit()
    db.refresh(share)

    return CollectionShareResponse(
        id=share.id,
        collection_id=share.collection_id,
        shared_with_user_id=share.shared_with_user_id,
        shared_with_email=target_user.email,
        shared_with_display_name=target_user.display_name,
        can_edit=share.can_edit,
        shared_at=share.shared_at,
    )


@router.put("/{collection_id}/shares/{share_id}", response_model=CollectionShareResponse)
async def update_collection_share(
    collection_id: str,
    share_id: str,
    share_data: CollectionShareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update share permissions. Only the owner can modify shares."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not _user_is_owner(collection, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify shares for this collection"
        )

    share = (
        db.query(CollectionShare)
        .options(joinedload(CollectionShare.shared_with_user))
        .filter(
            CollectionShare.id == share_id,
            CollectionShare.collection_id == collection_id
        )
        .first()
    )

    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    share.can_edit = share_data.can_edit
    db.commit()
    db.refresh(share)

    return CollectionShareResponse(
        id=share.id,
        collection_id=share.collection_id,
        shared_with_user_id=share.shared_with_user_id,
        shared_with_email=share.shared_with_user.email,
        shared_with_display_name=share.shared_with_user.display_name,
        can_edit=share.can_edit,
        shared_at=share.shared_at,
    )


@router.delete("/{collection_id}/shares/{share_id}")
async def remove_collection_share(
    collection_id: str,
    share_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a share from a collection. Only the owner can remove shares."""
    collection = db.query(Collection).filter(Collection.id == collection_id).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if not _user_is_owner(collection, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify shares for this collection"
        )

    share = (
        db.query(CollectionShare)
        .filter(
            CollectionShare.id == share_id,
            CollectionShare.collection_id == collection_id
        )
        .first()
    )

    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    db.delete(share)
    db.commit()

    return {"message": "Share removed successfully"}
