"""
Image upload and extraction endpoints.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
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
)


router = APIRouter(prefix="/upload", tags=["upload"])


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


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
async def upload_image(
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

    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Check for duplicates (image-based only, no recipe data yet)
    duplicates = None
    if check_duplicates:
        dup_result = check_for_duplicates(db, content)
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
def extract_recipe(job_id: str, db: Session = Depends(get_db)):
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

        # Read image data from file for storage in DB
        with open(Path(job.image_path), "rb") as img_file:
            image_data = img_file.read()
        suffix = Path(job.image_path).suffix.lower()

        # Prepare ingredient data for fingerprint computation
        ingredient_tuples = [
            (ing.ingredient_name or "", ing.amount, ing.unit)
            for ing in recipe_data.ingredients
        ]

        # Compute hashes for duplicate detection
        content_hash, perceptual_hash, fingerprint = compute_hashes_for_recipe(
            image_data, recipe_data.name, ingredient_tuples
        )

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
            source_image_data=image_data,
            source_image_mime=MIME_TYPES.get(suffix, "image/jpeg"),
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
async def upload_and_extract(
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

    # Save file
    content = await file.read()
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

        # Prepare ingredient data for fingerprint computation
        ingredient_tuples = [
            (ing.ingredient_name or "", ing.amount, ing.unit)
            for ing in recipe_data.ingredients
        ]

        # Compute hashes for duplicate detection
        content_hash, perceptual_hash, fingerprint = compute_hashes_for_recipe(
            content, recipe_data.name, ingredient_tuples
        )

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
            source_image_data=content,
            source_image_mime=MIME_TYPES.get(suffix, "image/jpeg"),
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
async def upload_and_extract_multi(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """Upload multiple images and extract a single recipe from them.

    Use this when a recipe spans multiple screenshots or pages.
    All images are sent to Claude together to extract one combined recipe.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    # Validate and save all files
    image_paths: List[Path] = []
    all_content: List[bytes] = []

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

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        image_paths.append(file_path)
        all_content.append(content)

    # Use first image as the primary for storage
    primary_content = all_content[0]
    primary_suffix = image_paths[0].suffix.lower()

    try:
        # Run multi-image extraction
        extractor = RecipeExtractor()
        extracted = extractor.extract_from_multiple_files(image_paths)

        # Convert to create schema
        recipe_data = map_extracted_to_create(extracted)

        # Prepare ingredient data for fingerprint computation
        ingredient_tuples = [
            (ing.ingredient_name or "", ing.amount, ing.unit)
            for ing in recipe_data.ingredients
        ]

        # Compute hashes for duplicate detection (using primary image)
        content_hash, perceptual_hash, fingerprint = compute_hashes_for_recipe(
            primary_content, recipe_data.name, ingredient_tuples
        )

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
            source_image_data=primary_content,
            source_image_mime=MIME_TYPES.get(primary_suffix, "image/jpeg"),
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
async def enhance_recipe_with_images(
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

        content = await file.read()
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
        extracted = extractor.enhance_recipe(
            existing_recipe=existing_recipe_data,
            new_image_paths=new_image_paths,
            original_image_data=recipe.source_image_data,
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
