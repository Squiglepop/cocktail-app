#!/usr/bin/env python3
"""
Migration script to backfill duplicate detection hashes for existing recipes.

This script computes and stores:
- image_content_hash: SHA-256 hash of the source image data
- image_perceptual_hash: Perceptual hash (pHash) for visually similar image detection
- recipe_fingerprint: MD5 hash of normalized recipe name + ingredients

Usage:
    cd cocktail-app/backend
    source venv/bin/activate
    python scripts/backfill_hashes.py [--dry-run]

    # For production (via Railway):
    railway run python scripts/backfill_hashes.py

Options:
    --dry-run   Show what would be updated without making changes
"""
import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Check if DATABASE_URL is set in environment (e.g., from Railway)
# before importing app.config which loads .env with override=True
_db_url_from_env = os.environ.get("DATABASE_URL")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import Recipe

# Use environment DATABASE_URL if it was set before config loaded
DATABASE_URL = _db_url_from_env or str(settings.database_url)
from app.services.duplicate_detector import (
    compute_content_hash,
    compute_perceptual_hash,
    compute_recipe_fingerprint,
)


def backfill_hashes(dry_run: bool = False) -> None:
    """Compute and store hashes for all existing recipes."""
    # Create database connection
    print(f"Connecting to: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get all recipes
        recipes = db.query(Recipe).all()
        total = len(recipes)
        updated = 0
        skipped = 0
        errors = 0

        print(f"Found {total} recipes to process")
        print("-" * 50)

        for i, recipe in enumerate(recipes, 1):
            recipe_name = recipe.name[:40] + "..." if len(recipe.name) > 40 else recipe.name
            print(f"[{i}/{total}] Processing: {recipe_name}")

            needs_update = False
            updates = {}

            # Check and compute image content hash
            if not recipe.image_content_hash and recipe.source_image_data:
                try:
                    content_hash = compute_content_hash(recipe.source_image_data)
                    updates["image_content_hash"] = content_hash
                    needs_update = True
                    print(f"  - Content hash: {content_hash[:16]}...")
                except Exception as e:
                    print(f"  ! Content hash error: {e}")
                    errors += 1

            # Check and compute perceptual hash
            if not recipe.image_perceptual_hash and recipe.source_image_data:
                try:
                    phash = compute_perceptual_hash(recipe.source_image_data)
                    if phash:
                        updates["image_perceptual_hash"] = phash
                        needs_update = True
                        print(f"  - Perceptual hash: {phash}")
                except Exception as e:
                    print(f"  ! Perceptual hash error: {e}")
                    errors += 1

            # Check and compute recipe fingerprint
            if not recipe.recipe_fingerprint:
                try:
                    # Get ingredient data from recipe
                    ingredient_tuples = [
                        (ri.ingredient.name, ri.amount, ri.unit)
                        for ri in recipe.ingredients
                    ]
                    fingerprint = compute_recipe_fingerprint(recipe.name, ingredient_tuples)
                    if fingerprint:
                        updates["recipe_fingerprint"] = fingerprint
                        needs_update = True
                        print(f"  - Recipe fingerprint: {fingerprint}")
                except Exception as e:
                    print(f"  ! Recipe fingerprint error: {e}")
                    errors += 1

            # Apply updates
            if needs_update:
                if not dry_run:
                    for field, value in updates.items():
                        setattr(recipe, field, value)
                updated += 1
                print(f"  -> {'Would update' if dry_run else 'Updated'}")
            else:
                skipped += 1
                print(f"  -> Skipped (already has hashes or no image)")

        # Commit all changes
        if not dry_run:
            db.commit()
            print("-" * 50)
            print(f"Committed changes to database")

        print("-" * 50)
        print(f"Summary:")
        print(f"  Total recipes: {total}")
        print(f"  Updated: {updated}")
        print(f"  Skipped: {skipped}")
        print(f"  Errors: {errors}")
        if dry_run:
            print(f"\n  (Dry run - no changes were made)")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Backfill duplicate detection hashes for existing recipes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    args = parser.parse_args()

    print("=" * 50)
    print("Backfill Duplicate Detection Hashes")
    print("=" * 50)
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
    print()

    backfill_hashes(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
