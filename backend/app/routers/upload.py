"""
Image upload and extraction endpoints.
"""
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import filetype
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import Recipe, Ingredient, RecipeIngredient, ExtractionJob
from app.schemas import (
    ExtractionJobResponse,
    RecipeResponse,
    DuplicateMatchResponse,
    DuplicateCheckResponse,
    UploadWithDuplicateCheckResponse,
)
from app.services import (
    get_db,
    RecipeExtractor,
    map_extracted_to_create,
    check_for_duplicates,
    compute_hashes_for_recipe,
    get_image_storage,
    ImageHashes,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["upload"])

# Rate limiter for upload endpoints
limiter = Limiter(key_func=get_remote_address)


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# Allowed MIME types based on magic bytes (actual file content)
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
}

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}

# Maximum file size: 20MB
MAX_FILE_SIZE = 20 * 1024 * 1024


def validate_image_content(file_content: bytes, filename: str) -> None:
    """Validate uploaded file is actually an image using magic bytes.

    This prevents attacks where a malicious file is uploaded with an
    image extension but contains non-image content.

    Args:
        file_content: Raw file bytes
        filename: Original filename for logging

    Raises:
        HTTPException: If validation fails
    """
    # Check file size
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    if len(file_content) < 100:
        raise HTTPException(
            status_code=400,
            detail="File too small to be a valid image"
        )

    # Check magic bytes (actual file content) using filetype (pure Python, no system deps)
    kind = filetype.guess(file_content)
    mime = kind.mime if kind else None

    if mime not in ALLOWED_MIME_TYPES:
        logger.warning(f"Invalid file upload attempt: {filename} has mime type {mime}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {mime}. Allowed: JPEG, PNG, GIF, WebP, HEIC"
        )

    # Check for extension/content mismatch (log warning but allow)
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    extension_mime_map = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "heic": "image/heic",
        "heif": "image/heif",
    }

    expected_mime = extension_mime_map.get(ext)
    if expected_mime and expected_mime != mime:
        logger.warning(f"Extension/content mismatch: {filename} has extension {ext} but content is {mime}")


def _convert_duplicate_result(result) -> Optional[DuplicateCheckResponse]:
    """Convert internal DuplicateCheckResult to API response schema."""
    if not result or not result.is_duplicate:
        return None
    return DuplicateCheckResponse(
        is_duplicate=result.is_duplicate,
        matches=[
            DuplicateMatchResponse(
                recipe_id=m.recipe_id,
                recipe_name=m.recipe_name,
                match_type=m.match_type,
                confidence=m.confidence,
                details=m.details,
            )
            for m in result.matches
        ],
    )


@router.post("", response_model=UploadWithDuplicateCheckResponse)
@limiter.limit("20/minute")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    check_duplicates: bool = Query(True, description="Check for duplicate images before creating job"),
    db: Session = Depends(get_db),
):
    """Upload an image and create an extraction job.

    By default, checks for duplicate images before creating the job.
    If duplicates are found, returns them in the response but still creates the job.
    Set check_duplicates=false to skip duplicate detection.
    """
    # Validate file type
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Generate unique filename
    file_id = uuid.uuid4()
    filename = f"{file_id}{suffix}"
    file_path = settings.upload_dir / filename

    # Read and validate file content
    content = await file.read()
    validate_image_content(content, file.filename or "unknown")

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Check for duplicates (image-based only, no recipe data yet)
    # Compute hashes once and reuse for duplicate check
    duplicates = None
    if check_duplicates:
        image_hashes = ImageHashes.from_image_data(content)
        dup_result = check_for_duplicates(db, content, precomputed_hashes=image_hashes)
        duplicates = _convert_duplicate_result(dup_result)

    # Create extraction job
    job = ExtractionJob(
        image_path=str(file_path),
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return UploadWithDuplicateCheckResponse(job=job, duplicates=duplicates)


@router.post("/{job_id}/extract", response_model=RecipeResponse)
@limiter.limit("10/minute")
def extract_recipe(request: Request, job_id: str, db: Session = Depends(get_db)):
    """Execute extraction for a pending job."""
    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status == "completed" and job.recipe_id:
        # Already extracted, return existing recipe
        recipe = (
            db.query(Recipe)
            .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
            .filter(Recipe.id == job.recipe_id)
            .first()
        )
        return recipe

    # Update status
    job.status = "processing"
    db.commit()

    try:
        # Run extraction
        extractor = RecipeExtractor()
        extracted = extractor.extract_from_file(Path(job.image_path))

        # Store raw extraction for debugging
        job.raw_extraction = json.dumps(extracted.model_dump())

        # Convert to create schema
        recipe_data = map_extracted_to_create(extracted)

        # Read image data from file for hashing and storage
        with open(Path(job.image_path), "rb") as img_file:
            image_data = img_file.read()
        suffix = Path(job.image_path).suffix.lower()
        mime_type = MIME_TYPES.get(suffix, "image/jpeg")

        # Compute image hashes once (single image load)
        image_hashes = ImageHashes.from_image_data(image_data)

        # Prepare ingredient data for fingerprint computation
        ingredient_tuples = [
            (ing.ingredient_name or "", ing.amount, ing.unit)
            for ing in recipe_data.ingredients
        ]

        # Compute hashes for duplicate detection (reuse precomputed image hashes)
        content_hash, perceptual_hash, fingerprint = compute_hashes_for_recipe(
            image_data, recipe_data.name, ingredient_tuples,
            precomputed_image_hashes=image_hashes
        )

        # Save image to filesystem
        image_storage = get_image_storage()
        image_path = image_storage.save_image(image_data, mime_type)

        # Create recipe
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
            source_type="screenshot",
            source_image_path=image_path,
            source_image_mime=mime_type,
            image_content_hash=content_hash,
            image_perceptual_hash=perceptual_hash,
            recipe_fingerprint=fingerprint,
        )
        db.add(recipe)
        db.flush()

        # Add ingredients
        for idx, ing_data in enumerate(recipe_data.ingredients):
            # Get or create ingredient
            ingredient = None
            if ing_data.ingredient_name:
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

        # Update job
        job.status = "completed"
        job.recipe_id = recipe.id
        job.completed_at = datetime.utcnow()

        db.commit()

        # Load full recipe with relationships
        recipe = (
            db.query(Recipe)
            .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
            .filter(Recipe.id == recipe.id)
            .first()
        )

        return recipe

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("/{job_id}", response_model=ExtractionJobResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status of an extraction job."""
    job = db.query(ExtractionJob).filter(ExtractionJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/extract-immediate", response_model=RecipeResponse)
@limiter.limit("10/minute")
async def upload_and_extract(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an image and immediately extract the recipe (synchronous)."""
    # Validate file type
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Generate unique filename
    file_id = uuid.uuid4()
    filename = f"{file_id}{suffix}"
    file_path = settings.upload_dir / filename

    # Read and validate file content
    content = await file.read()
    validate_image_content(content, file.filename or "unknown")

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Create extraction job for tracking
    job = ExtractionJob(
        image_path=str(file_path),
        status="processing",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        # Run extraction
        extractor = RecipeExtractor()
        extracted = extractor.extract_from_file(file_path)

        # Store raw extraction
        job.raw_extraction = json.dumps(extracted.model_dump())

        # Convert and create recipe
        recipe_data = map_extracted_to_create(extracted)

        # Compute image hashes once (single image load)
        image_hashes = ImageHashes.from_image_data(content)

        # Prepare ingredient data for fingerprint computation
        ingredient_tuples = [
            (ing.ingredient_name or "", ing.amount, ing.unit)
            for ing in recipe_data.ingredients
        ]

        # Compute hashes for duplicate detection (reuse precomputed image hashes)
        content_hash, perceptual_hash, fingerprint = compute_hashes_for_recipe(
            content, recipe_data.name, ingredient_tuples,
            precomputed_image_hashes=image_hashes
        )

        # Save image to filesystem
        mime_type = MIME_TYPES.get(suffix, "image/jpeg")
        image_storage = get_image_storage()
        image_path = image_storage.save_image(content, mime_type)

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
            source_type="screenshot",
            source_image_path=image_path,
            source_image_mime=mime_type,
            image_content_hash=content_hash,
            image_perceptual_hash=perceptual_hash,
            recipe_fingerprint=fingerprint,
        )
        db.add(recipe)
        db.flush()

        # Add ingredients
        for idx, ing_data in enumerate(recipe_data.ingredients):
            ingredient = None
            if ing_data.ingredient_name:
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

        # Update job
        job.status = "completed"
        job.recipe_id = recipe.id
        job.completed_at = datetime.utcnow()

        db.commit()

        # Return full recipe
        recipe = (
            db.query(Recipe)
            .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
            .filter(Recipe.id == recipe.id)
            .first()
        )

        return recipe

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/extract-multi", response_model=RecipeResponse)
@limiter.limit("10/minute")
async def upload_and_extract_multi(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload multiple images and extract a single recipe from them.

    Use this when a recipe spans multiple screenshots or pages.
    All images are sent to Claude together to extract one combined recipe.

    Memory optimization: Files are saved to disk immediately and only the
    primary image content is kept in memory for hash computation.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Validate and save all files - only keep paths, not content
    image_paths: List[Path] = []
    primary_path: Optional[Path] = None

    for idx, file in enumerate(files):
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        file_id = uuid.uuid4()
        filename = f"{file_id}{suffix}"
        file_path = settings.upload_dir / filename

        # Read and validate file content
        content = await file.read()
        validate_image_content(content, file.filename or "unknown")

        # Save to disk
        with open(file_path, "wb") as f:
            f.write(content)

        image_paths.append(file_path)

        # Track primary path (first image)
        if idx == 0:
            primary_path = file_path

        # Release content immediately after writing to disk
        del content

    # Read primary image content for hash computation (only keep one in memory)
    with open(primary_path, "rb") as f:
        primary_content = f.read()
    primary_suffix = primary_path.suffix.lower()

    try:
        # Run multi-image extraction
        extractor = RecipeExtractor()
        extracted = extractor.extract_from_multiple_files(image_paths)

        # Convert to create schema
        recipe_data = map_extracted_to_create(extracted)

        # Compute image hashes once (single image load for primary)
        image_hashes = ImageHashes.from_image_data(primary_content)

        # Prepare ingredient data for fingerprint computation
        ingredient_tuples = [
            (ing.ingredient_name or "", ing.amount, ing.unit)
            for ing in recipe_data.ingredients
        ]

        # Compute hashes for duplicate detection (using primary image, reuse precomputed hashes)
        content_hash, perceptual_hash, fingerprint = compute_hashes_for_recipe(
            primary_content, recipe_data.name, ingredient_tuples,
            precomputed_image_hashes=image_hashes
        )

        # Save primary image to filesystem
        primary_mime = MIME_TYPES.get(primary_suffix, "image/jpeg")
        image_storage = get_image_storage()
        image_path = image_storage.save_image(primary_content, primary_mime)

        # Create recipe
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
            source_type="screenshot",
            source_image_path=image_path,
            source_image_mime=primary_mime,
            image_content_hash=content_hash,
            image_perceptual_hash=perceptual_hash,
            recipe_fingerprint=fingerprint,
        )
        db.add(recipe)
        db.flush()

        # Add ingredients
        for idx, ing_data in enumerate(recipe_data.ingredients):
            ingredient = None
            if ing_data.ingredient_name:
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

        # Return full recipe
        recipe = (
            db.query(Recipe)
            .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
            .filter(Recipe.id == recipe.id)
            .first()
        )

        return recipe

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/enhance/{recipe_id}", response_model=RecipeResponse)
@limiter.limit("10/minute")
async def enhance_recipe_with_images(
    request: Request,
    recipe_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Enhance an existing recipe with additional screenshot(s).

    Sends the original image (if available) plus new images to Claude
    for re-extraction, merging any new information into the recipe.
    """
    # Get existing recipe
    recipe = (
        db.query(Recipe)
        .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
        .filter(Recipe.id == recipe_id)
        .first()
    )
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Validate and save new files
    new_image_paths: List[Path] = []
    new_image_contents: List[tuple[bytes, str]] = []  # (content, mime_type)

    for file in files:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.filename}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
            )

        file_id = uuid.uuid4()
        filename = f"{file_id}{suffix}"
        file_path = settings.upload_dir / filename

        # Read and validate file content
        content = await file.read()
        validate_image_content(content, file.filename or "unknown")

        # Save to disk
        with open(file_path, "wb") as f:
            f.write(content)

        new_image_paths.append(file_path)
        new_image_contents.append((content, MIME_TYPES.get(suffix, "image/jpeg")))

    # Build existing recipe data for enhancement prompt
    existing_recipe_data = {
        "name": recipe.name,
        "description": recipe.description,
        "ingredients": [
            {
                "name": ri.ingredient.name,
                "amount": ri.amount,
                "unit": ri.unit,
                "notes": ri.notes,
                "type": ri.ingredient.type,
            }
            for ri in sorted(recipe.ingredients, key=lambda x: x.order)
        ],
        "instructions": recipe.instructions,
        "template": recipe.template,
        "main_spirit": recipe.main_spirit,
        "glassware": recipe.glassware,
        "serving_style": recipe.serving_style,
        "method": recipe.method,
        "garnish": recipe.garnish,
        "notes": recipe.notes,
    }

    try:
        # Run enhancement extraction
        extractor = RecipeExtractor()

        # Get original image - prefer filesystem path, fall back to DB BLOB for migration
        original_image_path = None
        original_image_data = None
        if recipe.source_image_path:
            image_storage = get_image_storage()
            original_image_path = image_storage.get_image_path(recipe.source_image_path)
        elif recipe.source_image_data:
            # Legacy: image stored in DB (migration path)
            original_image_data = recipe.source_image_data

        extracted = extractor.enhance_recipe(
            existing_recipe=existing_recipe_data,
            new_image_paths=new_image_paths,
            original_image_path=original_image_path,
            original_image_data=original_image_data,
            original_image_mime=recipe.source_image_mime,
        )

        # Convert to update format
        recipe_data = map_extracted_to_create(extracted)

        # Update recipe fields
        recipe.name = recipe_data.name
        recipe.description = recipe_data.description
        recipe.instructions = recipe_data.instructions
        recipe.template = recipe_data.template
        recipe.main_spirit = recipe_data.main_spirit
        recipe.glassware = recipe_data.glassware
        recipe.serving_style = recipe_data.serving_style
        recipe.method = recipe_data.method
        recipe.garnish = recipe_data.garnish
        recipe.notes = recipe_data.notes

        # Clear existing ingredients and add new ones
        db.query(RecipeIngredient).filter(RecipeIngredient.recipe_id == recipe.id).delete()
        db.flush()

        for idx, ing_data in enumerate(recipe_data.ingredients):
            ingredient = None
            if ing_data.ingredient_name:
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

        # Return updated recipe
        recipe = (
            db.query(Recipe)
            .options(joinedload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))
            .filter(Recipe.id == recipe_id)
            .first()
        )

        return recipe

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {str(e)}")
