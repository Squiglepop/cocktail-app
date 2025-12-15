"""
Cleanup service for orphaned image files.

Scans the image storage directory and removes files that are not
referenced by any recipe in the database.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set

from sqlalchemy.orm import Session

from ..models import Recipe
from .image_storage import get_image_storage

logger = logging.getLogger(__name__)


@dataclass
class CleanupStats:
    """Statistics from a cleanup operation."""
    files_scanned: int
    orphans_found: int
    orphans_deleted: int
    bytes_reclaimed: int
    skipped_recent: int
    errors: List[str]

    @property
    def dry_run(self) -> bool:
        """Check if this was a dry run (found but not deleted)."""
        return self.orphans_found > 0 and self.orphans_deleted == 0


class OrphanedFileCleanupService:
    """Service for cleaning up orphaned image files."""

    # Supported image extensions
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    # Files newer than this won't be deleted (in case upload is in progress)
    MIN_FILE_AGE = timedelta(hours=1)

    def __init__(self, storage_dir: Path):
        """
        Initialize the cleanup service.

        Args:
            storage_dir: Directory where images are stored.
        """
        self.storage_dir = storage_dir

    def get_files_on_disk(self) -> Set[str]:
        """
        Get all image files in the storage directory.

        Returns:
            Set of filenames (not full paths) for all image files.
        """
        files = set()
        if not self.storage_dir.exists():
            return files

        for path in self.storage_dir.iterdir():
            if path.is_file() and path.suffix.lower() in self.IMAGE_EXTENSIONS:
                files.add(path.name)

        return files

    def get_referenced_files(self, db: Session) -> Set[str]:
        """
        Get all image filenames referenced by recipes in the database.

        Normalizes paths to just filenames for comparison, handling legacy
        'uploads/' prefix paths.

        Args:
            db: Database session.

        Returns:
            Set of filenames referenced in the source_image_path column.
        """
        result = db.query(Recipe.source_image_path).filter(
            Recipe.source_image_path.isnot(None)
        ).all()

        referenced = set()
        for row in result:
            path = row[0]
            if not path:
                continue
            # Normalize: extract just the filename from legacy 'uploads/' paths
            if path.startswith("uploads/"):
                path = path.replace("uploads/", "", 1)
            referenced.add(path)

        return referenced

    def find_orphaned_files(self, db: Session) -> Set[str]:
        """
        Find files on disk that are not referenced in the database.

        Args:
            db: Database session.

        Returns:
            Set of orphaned filenames.
        """
        files_on_disk = self.get_files_on_disk()
        referenced_files = self.get_referenced_files(db)
        return files_on_disk - referenced_files

    def is_file_recent(self, filepath: Path) -> bool:
        """
        Check if a file is too recent to delete.

        Args:
            filepath: Path to the file.

        Returns:
            True if the file was modified within MIN_FILE_AGE.
        """
        try:
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
            age = datetime.now() - mtime
            return age < self.MIN_FILE_AGE
        except OSError:
            # If we can't read the file stats, assume it's safe to delete
            return False

    def cleanup_orphans(self, db: Session, dry_run: bool = False) -> CleanupStats:
        """
        Find and delete orphaned image files.

        Args:
            db: Database session.
            dry_run: If True, only report what would be deleted without deleting.

        Returns:
            CleanupStats with operation results.
        """
        files_on_disk = self.get_files_on_disk()
        orphaned_files = self.find_orphaned_files(db)

        stats = CleanupStats(
            files_scanned=len(files_on_disk),
            orphans_found=len(orphaned_files),
            orphans_deleted=0,
            bytes_reclaimed=0,
            skipped_recent=0,
            errors=[],
        )

        for filename in orphaned_files:
            filepath = self.storage_dir / filename

            # Skip files that are too recent
            if self.is_file_recent(filepath):
                stats.skipped_recent += 1
                logger.debug(f"Skipping recent file: {filename}")
                continue

            try:
                file_size = filepath.stat().st_size
            except OSError as e:
                stats.errors.append(f"Could not stat {filename}: {e}")
                logger.warning(f"Could not stat orphaned file {filename}: {e}")
                continue

            if dry_run:
                logger.info(f"[DRY RUN] Would delete orphaned file: {filename} ({file_size} bytes)")
            else:
                try:
                    filepath.unlink()
                    stats.orphans_deleted += 1
                    stats.bytes_reclaimed += file_size
                    logger.info(f"Deleted orphaned file: {filename} ({file_size} bytes)")
                except OSError as e:
                    stats.errors.append(f"Failed to delete {filename}: {e}")
                    logger.error(f"Failed to delete orphaned file {filename}: {e}")

        return stats


def get_cleanup_service() -> OrphanedFileCleanupService:
    """
    Get the cleanup service configured with the current settings.

    Returns:
        OrphanedFileCleanupService instance.
    """
    from ..config import settings
    return OrphanedFileCleanupService(settings.image_storage_dir)
