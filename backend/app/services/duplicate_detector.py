"""
Duplicate detection service for cocktail recipe uploads.

Uses a hybrid approach with three layers:
1. Content hash (SHA-256) - exact image duplicates
2. Perceptual hash (pHash) - visually similar images
3. Recipe fingerprint - same recipe from different sources
"""
import hashlib
import io
from dataclasses import dataclass
from typing import Optional, List

import imagehash
from PIL import Image
from sqlalchemy.orm import Session

from app.models import Recipe, RecipeIngredient


@dataclass
class DuplicateMatch:
    """Represents a potential duplicate match."""
    recipe_id: str
    recipe_name: str
    match_type: str  # "exact_image", "similar_image", "same_recipe"
    confidence: float  # 0.0 to 1.0
    details: str


@dataclass
class DuplicateCheckResult:
    """Result of duplicate detection check."""
    is_duplicate: bool
    matches: List[DuplicateMatch]

    @property
    def best_match(self) -> Optional[DuplicateMatch]:
        """Return the highest confidence match."""
        if not self.matches:
            return None
        return max(self.matches, key=lambda m: m.confidence)


# Perceptual hash similarity threshold (0-64 hamming distance)
# Lower = more similar. 10 is a reasonable default for "same image, different compression"
PHASH_SIMILARITY_THRESHOLD = 10


def compute_content_hash(image_data: bytes) -> str:
    """Compute SHA-256 hash of image bytes."""
    return hashlib.sha256(image_data).hexdigest()


def compute_perceptual_hash(image_data: bytes) -> str:
    """Compute perceptual hash using pHash algorithm."""
    img = Image.open(io.BytesIO(image_data))
    return str(imagehash.phash(img))


def compute_recipe_fingerprint(
    name: str,
    ingredients: List[tuple[str, Optional[float], Optional[str]]]  # (name, amount, unit)
) -> str:
    """
    Compute a fingerprint for a recipe based on name and ingredients.

    Args:
        name: Recipe name
        ingredients: List of (ingredient_name, amount, unit) tuples

    Returns:
        MD5 hash of normalized recipe data
    """
    # Normalize name
    normalized_name = name.lower().strip()

    # Sort and normalize ingredients (name:amount:unit)
    sorted_ingredients = sorted(
        f"{ing[0].lower().strip()}:{ing[1] or ''}:{(ing[2] or '').lower()}"
        for ing in ingredients
        if ing[0]  # Skip empty ingredient names
    )

    fingerprint_data = f"{normalized_name}|{'|'.join(sorted_ingredients)}"
    return hashlib.md5(fingerprint_data.encode()).hexdigest()


def check_exact_duplicate(
    db: Session,
    content_hash: str,
    exclude_recipe_id: Optional[str] = None,
) -> Optional[DuplicateMatch]:
    """Check for exact image duplicate by content hash."""
    query = db.query(Recipe).filter(Recipe.image_content_hash == content_hash)
    if exclude_recipe_id:
        query = query.filter(Recipe.id != exclude_recipe_id)

    match = query.first()
    if match:
        return DuplicateMatch(
            recipe_id=match.id,
            recipe_name=match.name,
            match_type="exact_image",
            confidence=1.0,
            details="Identical image file detected",
        )
    return None


def check_similar_images(
    db: Session,
    perceptual_hash: str,
    threshold: int = PHASH_SIMILARITY_THRESHOLD,
    exclude_recipe_id: Optional[str] = None,
) -> List[DuplicateMatch]:
    """Check for visually similar images using perceptual hash."""
    matches = []

    query = db.query(Recipe.id, Recipe.name, Recipe.image_perceptual_hash).filter(
        Recipe.image_perceptual_hash.isnot(None)
    )
    if exclude_recipe_id:
        query = query.filter(Recipe.id != exclude_recipe_id)

    new_hash = imagehash.hex_to_hash(perceptual_hash)

    for recipe_id, recipe_name, existing_hash in query.all():
        existing = imagehash.hex_to_hash(existing_hash)
        distance = new_hash - existing  # Hamming distance

        if distance <= threshold:
            # Convert distance to confidence (0 distance = 1.0 confidence)
            confidence = 1.0 - (distance / 64.0)
            matches.append(DuplicateMatch(
                recipe_id=recipe_id,
                recipe_name=recipe_name,
                match_type="similar_image",
                confidence=confidence,
                details=f"Visually similar image (hamming distance: {distance})",
            ))

    return sorted(matches, key=lambda m: m.confidence, reverse=True)


def check_recipe_fingerprint(
    db: Session,
    fingerprint: str,
    exclude_recipe_id: Optional[str] = None,
) -> Optional[DuplicateMatch]:
    """Check for duplicate recipe by ingredient fingerprint."""
    query = db.query(Recipe).filter(Recipe.recipe_fingerprint == fingerprint)
    if exclude_recipe_id:
        query = query.filter(Recipe.id != exclude_recipe_id)

    match = query.first()
    if match:
        return DuplicateMatch(
            recipe_id=match.id,
            recipe_name=match.name,
            match_type="same_recipe",
            confidence=0.95,
            details="Same recipe name and ingredients (possibly from different source)",
        )
    return None


def check_for_duplicates(
    db: Session,
    image_data: bytes,
    recipe_name: Optional[str] = None,
    ingredients: Optional[List[tuple[str, Optional[float], Optional[str]]]] = None,
    exclude_recipe_id: Optional[str] = None,
) -> DuplicateCheckResult:
    """
    Perform full duplicate detection check.

    Args:
        db: Database session
        image_data: Raw image bytes
        recipe_name: Extracted recipe name (optional, for fingerprint check)
        ingredients: List of (name, amount, unit) tuples (optional, for fingerprint check)
        exclude_recipe_id: Recipe ID to exclude from checks (for updates)

    Returns:
        DuplicateCheckResult with matches sorted by confidence
    """
    matches: List[DuplicateMatch] = []

    # 1. Check exact image duplicate
    content_hash = compute_content_hash(image_data)
    exact_match = check_exact_duplicate(db, content_hash, exclude_recipe_id)
    if exact_match:
        matches.append(exact_match)

    # 2. Check visually similar images
    perceptual_hash = compute_perceptual_hash(image_data)
    similar_matches = check_similar_images(db, perceptual_hash, exclude_recipe_id=exclude_recipe_id)
    matches.extend(similar_matches)

    # 3. Check recipe fingerprint (if we have extracted data)
    if recipe_name and ingredients:
        fingerprint = compute_recipe_fingerprint(recipe_name, ingredients)
        recipe_match = check_recipe_fingerprint(db, fingerprint, exclude_recipe_id)
        if recipe_match:
            matches.append(recipe_match)

    # Deduplicate matches by recipe_id (keep highest confidence)
    seen_recipes = {}
    for match in matches:
        if match.recipe_id not in seen_recipes or match.confidence > seen_recipes[match.recipe_id].confidence:
            seen_recipes[match.recipe_id] = match

    unique_matches = sorted(seen_recipes.values(), key=lambda m: m.confidence, reverse=True)

    return DuplicateCheckResult(
        is_duplicate=len(unique_matches) > 0,
        matches=unique_matches,
    )


def compute_hashes_for_recipe(
    image_data: bytes,
    recipe_name: str,
    ingredients: List[tuple[str, Optional[float], Optional[str]]],
) -> tuple[str, str, str]:
    """
    Compute all hashes for a recipe.

    Returns:
        Tuple of (content_hash, perceptual_hash, recipe_fingerprint)
    """
    content_hash = compute_content_hash(image_data)
    perceptual_hash = compute_perceptual_hash(image_data)
    fingerprint = compute_recipe_fingerprint(recipe_name, ingredients)
    return content_hash, perceptual_hash, fingerprint
