#!/usr/bin/env python3
"""
Migrate existing BLOB images from database to filesystem.

This script should be run after deploying the filesystem image storage changes.
It migrates images stored as BLOBs in the database to the filesystem.

Usage:
    cd cocktail-app/backend
    source venv/bin/activate
    python scripts/migrate_images.py [--clear-blobs]

Options:
    --clear-blobs    After migration, clear the source_image_data column to free space.
                     Only use this after verifying all images are accessible.
"""
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.database import SessionLocal
from app.models.recipe import Recipe
from app.services.image_storage import get_image_storage


def migrate_images(clear_blobs: bool = False) -> None:
    """
    Migrate images from database BLOBs to filesystem.

    Args:
        clear_blobs: If True, set source_image_data to None after successful migration.
    """
    db = SessionLocal()
    image_storage = get_image_storage()

    try:
        # Find recipes with BLOB data but no filesystem path
        recipes = (
            db.query(Recipe)
            .filter(
                Recipe.source_image_data.isnot(None),
                Recipe.source_image_path.is_(None),
            )
            .all()
        )

        print(f"Found {len(recipes)} recipes with images to migrate")

        migrated = 0
        failed = 0

        for recipe in recipes:
            try:
                print(f"Migrating image for recipe: {recipe.name} (ID: {recipe.id})")

                # Save image to filesystem
                image_path = image_storage.save_image(
                    recipe.source_image_data,
                    recipe.source_image_mime or "image/jpeg",
                )

                # Update recipe with filesystem path
                recipe.source_image_path = image_path

                # Optionally clear BLOB after successful migration
                if clear_blobs:
                    recipe.source_image_data = None

                migrated += 1

            except Exception as e:
                print(f"  ERROR: Failed to migrate image for recipe {recipe.id}: {e}")
                failed += 1

        # Commit all changes
        db.commit()

        print(f"\nMigration complete:")
        print(f"  Migrated: {migrated}")
        print(f"  Failed: {failed}")

        if not clear_blobs and migrated > 0:
            print(
                "\nNote: BLOB data was kept in database. "
                "Run with --clear-blobs to remove after verifying images work."
            )

    finally:
        db.close()


def verify_migration() -> None:
    """Verify that all migrated images are accessible."""
    db = SessionLocal()
    image_storage = get_image_storage()

    try:
        # Find recipes that should have filesystem images
        recipes = (
            db.query(Recipe)
            .filter(Recipe.source_image_path.isnot(None))
            .all()
        )

        print(f"Verifying {len(recipes)} recipes with filesystem images...")

        missing = 0
        valid = 0

        for recipe in recipes:
            image_path = image_storage.get_image_path(recipe.source_image_path)
            if image_path.exists():
                valid += 1
            else:
                print(f"  MISSING: {recipe.name} (ID: {recipe.id}) - {recipe.source_image_path}")
                missing += 1

        print(f"\nVerification complete:")
        print(f"  Valid: {valid}")
        print(f"  Missing: {missing}")

        if missing > 0:
            print("\nWARNING: Some image files are missing!")
            print("Do NOT run with --clear-blobs until this is resolved.")

    finally:
        db.close()


def show_stats() -> None:
    """Show statistics about image storage."""
    db = SessionLocal()

    try:
        total = db.query(Recipe).count()
        with_blob = (
            db.query(Recipe).filter(Recipe.source_image_data.isnot(None)).count()
        )
        with_path = (
            db.query(Recipe).filter(Recipe.source_image_path.isnot(None)).count()
        )
        with_both = (
            db.query(Recipe)
            .filter(
                Recipe.source_image_data.isnot(None),
                Recipe.source_image_path.isnot(None),
            )
            .count()
        )
        blob_only = (
            db.query(Recipe)
            .filter(
                Recipe.source_image_data.isnot(None),
                Recipe.source_image_path.is_(None),
            )
            .count()
        )
        path_only = (
            db.query(Recipe)
            .filter(
                Recipe.source_image_data.is_(None),
                Recipe.source_image_path.isnot(None),
            )
            .count()
        )

        print("Image Storage Statistics:")
        print(f"  Total recipes: {total}")
        print(f"  With BLOB data: {with_blob}")
        print(f"  With filesystem path: {with_path}")
        print(f"  With both (pending cleanup): {with_both}")
        print(f"  BLOB only (need migration): {blob_only}")
        print(f"  Filesystem only (migrated): {path_only}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate recipe images from database BLOBs to filesystem"
    )
    parser.add_argument(
        "--clear-blobs",
        action="store_true",
        help="Clear source_image_data after migration (only after verification!)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify that all migrated images exist on filesystem",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics about image storage",
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
    elif args.verify:
        verify_migration()
    else:
        migrate_images(clear_blobs=args.clear_blobs)
