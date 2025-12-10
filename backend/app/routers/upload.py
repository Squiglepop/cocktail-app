"""
Image upload and extraction endpoints.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models import Recipe, Ingredient, RecipeIngredient, ExtractionJob
from app.schemas import ExtractionJobResponse, RecipeResponse
from app.services import get_db, RecipeExtractor, map_extracted_to_create


router = APIRouter(prefix="/upload", tags=["upload"])


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


@router.post("", response_model=ExtractionJobResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload an image and create an extraction job."""
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

    # Create extraction job
    job = ExtractionJob(
        image_path=str(file_path),
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return job


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
