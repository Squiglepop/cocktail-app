#!/usr/bin/env python3
"""
Migrate recipes with legacy 'uploads/' path format to new filesystem storage.

This script handles recipes that were created before the image storage refactor
and still have source_image_path like 'uploads/xxx.jpg' instead of just 'xxx.jpg'.

The script will:
1. Find recipes with 'uploads/' prefix in source_image_path
2. Look for the file in ./uploads/ directory
3. Copy it to ./data/images/ (permanent storage)
4. Update the database path to just the filename

Usage:
    cd cocktail-app/backend
    source venv/bin/activate
    python scripts/migrate_upload_paths.py [--dry-run]

Options:
    --dry-run    Show what would be done without making changes
"""
import shutil
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.services.database import SessionLocal
from app.models.recipe import Recipe


def migrate_upload_paths(dry_run: bool = False) -> None:
    """
    Migrate recipes with legacy 'uploads/' paths to new format.

    Args:
        dry_run: If True, only show what would be done without making changes.
    """
    db = SessionLocal()
    upload_dir = settings.upload_dir
    storage_dir = settings.image_storage_dir

    try:
        # Find recipes with legacy 'uploads/' prefix paths
        recipes = (
            db.query(Recipe)
            .filter(Recipe.source_image_path.like("uploads/%"))
            .all()
        )

        print(f"Found {len(recipes)} recipes with legacy 'uploads/' paths")
        if dry_run:
            print("DRY RUN - no changes will be made\n")

        migrated = 0
        already_migrated = 0
        missing_source = 0
        failed = 0

        for recipe in recipes:
            old_path = recipe.source_image_path
            filename = old_path.replace("uploads/", "", 1)

            # Source file in uploads directory
            source_file = upload_dir / filename
            # Also check if path is relative to cwd
            if not source_file.exists():
                source_file = Path(old_path)

            # Destination in permanent storage
            dest_file = storage_dir / filename

            print(f"\nRecipe: {recipe.name} (ID: {recipe.id})")
            print(f"  Old path: {old_path}")
            print(f"  New path: {filename}")

            # Check if already migrated (file exists in storage_dir)
            if dest_file.exists():
                print(f"  Status: File already exists in storage, updating DB path only")
                if not dry_run:
                    recipe.source_image_path = filename
                already_migrated += 1
                continue

            # Check if source file exists
            if not source_file.exists():
                print(f"  Status: ERROR - Source file not found at {source_file}")
                missing_source += 1
                continue

            # Copy file to permanent storage
            print(f"  Status: Copying {source_file} -> {dest_file}")
            if not dry_run:
                try:
                    shutil.copy2(source_file, dest_file)
                    recipe.source_image_path = filename
                    migrated += 1
                except Exception as e:
                    print(f"  ERROR: Failed to copy file: {e}")
                    failed += 1
            else:
                migrated += 1

        if not dry_run:
            db.commit()

        print(f"\n{'DRY RUN ' if dry_run else ''}Migration Summary:")
        print(f"  Migrated (copied file): {migrated}")
        print(f"  Already in storage (path updated): {already_migrated}")
        print(f"  Missing source files: {missing_source}")
        print(f"  Failed: {failed}")

        if missing_source > 0:
            print("\nWARNING: Some source files are missing!")
            print("These recipes will show 404 for their images.")
            print("If this is on Railway, the files may have been lost during redeploy.")

    finally:
        db.close()


def show_stats() -> None:
    """Show statistics about path formats in the database."""
    db = SessionLocal()

    try:
        total = db.query(Recipe).count()
        with_path = (
            db.query(Recipe).filter(Recipe.source_image_path.isnot(None)).count()
        )
        legacy_paths = (
            db.query(Recipe).filter(Recipe.source_image_path.like("uploads/%")).count()
        )
        new_paths = with_path - legacy_paths

        print("Path Format Statistics:")
        print(f"  Total recipes: {total}")
        print(f"  With image path: {with_path}")
        print(f"  Legacy 'uploads/' format: {legacy_paths}")
        print(f"  New format (just filename): {new_paths}")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate recipes from legacy 'uploads/' path format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show statistics about path formats",
    )

    args = parser.parse_args()

    if args.stats:
        show_stats()
    else:
        migrate_upload_paths(dry_run=args.dry_run)
