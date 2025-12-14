"""
Tests for orphaned image file cleanup functionality.
"""
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.models import Recipe
from app.services.cleanup import OrphanedFileCleanupService, CleanupStats, get_cleanup_service


@pytest.fixture
def temp_storage_dir(tmp_path) -> Path:
    """Create a temporary storage directory."""
    storage_dir = tmp_path / "images"
    storage_dir.mkdir()
    return storage_dir


@pytest.fixture
def cleanup_service(temp_storage_dir) -> OrphanedFileCleanupService:
    """Create a cleanup service with a temporary storage directory."""
    return OrphanedFileCleanupService(temp_storage_dir)


def create_test_image(path: Path, content: bytes = b"test image data") -> None:
    """Create a test image file."""
    path.write_bytes(content)


class TestOrphanedFileCleanupService:
    """Tests for OrphanedFileCleanupService."""

    def test_get_files_on_disk_empty(self, cleanup_service: OrphanedFileCleanupService):
        """Test getting files from an empty directory."""
        files = cleanup_service.get_files_on_disk()
        assert files == set()

    def test_get_files_on_disk_with_images(
        self,
        cleanup_service: OrphanedFileCleanupService,
        temp_storage_dir: Path,
    ):
        """Test getting image files from the storage directory."""
        # Create some test files
        create_test_image(temp_storage_dir / "image1.jpg")
        create_test_image(temp_storage_dir / "image2.png")
        create_test_image(temp_storage_dir / "image3.webp")
        (temp_storage_dir / "not_an_image.txt").write_text("not an image")

        files = cleanup_service.get_files_on_disk()

        assert files == {"image1.jpg", "image2.png", "image3.webp"}

    def test_get_files_on_disk_nonexistent_dir(self, tmp_path: Path):
        """Test getting files from a nonexistent directory."""
        service = OrphanedFileCleanupService(tmp_path / "nonexistent")
        files = service.get_files_on_disk()
        assert files == set()

    def test_get_referenced_files(
        self,
        cleanup_service: OrphanedFileCleanupService,
        test_session: Session,
        sample_user,
    ):
        """Test getting referenced files from the database."""
        # Create recipes with image paths
        recipe1 = Recipe(
            name="Recipe 1",
            source_image_path="image1.jpg",
            user_id=sample_user.id,
        )
        recipe2 = Recipe(
            name="Recipe 2",
            source_image_path="image2.png",
            user_id=sample_user.id,
        )
        recipe3 = Recipe(
            name="Recipe 3",
            source_image_path=None,  # No image
            user_id=sample_user.id,
        )
        test_session.add_all([recipe1, recipe2, recipe3])
        test_session.commit()

        referenced = cleanup_service.get_referenced_files(test_session)

        assert referenced == {"image1.jpg", "image2.png"}

    def test_find_orphaned_files(
        self,
        cleanup_service: OrphanedFileCleanupService,
        temp_storage_dir: Path,
        test_session: Session,
        sample_user,
    ):
        """Test finding orphaned files."""
        # Create files on disk
        create_test_image(temp_storage_dir / "referenced.jpg")
        create_test_image(temp_storage_dir / "orphan1.jpg")
        create_test_image(temp_storage_dir / "orphan2.png")

        # Create a recipe referencing one file
        recipe = Recipe(
            name="Test Recipe",
            source_image_path="referenced.jpg",
            user_id=sample_user.id,
        )
        test_session.add(recipe)
        test_session.commit()

        orphans = cleanup_service.find_orphaned_files(test_session)

        assert orphans == {"orphan1.jpg", "orphan2.png"}

    def test_is_file_recent(
        self,
        cleanup_service: OrphanedFileCleanupService,
        temp_storage_dir: Path,
    ):
        """Test checking if a file is too recent to delete."""
        # Create a file (will have current timestamp)
        test_file = temp_storage_dir / "recent.jpg"
        create_test_image(test_file)

        # File just created should be considered recent
        assert cleanup_service.is_file_recent(test_file) is True

        # Modify the file timestamp to be old
        old_time = time.time() - 7200  # 2 hours ago
        os.utime(test_file, (old_time, old_time))

        assert cleanup_service.is_file_recent(test_file) is False

    def test_cleanup_orphans_dry_run(
        self,
        cleanup_service: OrphanedFileCleanupService,
        temp_storage_dir: Path,
        test_session: Session,
        sample_user,
    ):
        """Test dry run mode doesn't delete files."""
        # Create orphaned file with old timestamp
        orphan = temp_storage_dir / "orphan.jpg"
        create_test_image(orphan)
        old_time = time.time() - 7200
        os.utime(orphan, (old_time, old_time))

        stats = cleanup_service.cleanup_orphans(test_session, dry_run=True)

        assert stats.files_scanned == 1
        assert stats.orphans_found == 1
        assert stats.orphans_deleted == 0
        assert stats.bytes_reclaimed == 0
        assert orphan.exists()  # File should still exist

    def test_cleanup_orphans_deletes_files(
        self,
        cleanup_service: OrphanedFileCleanupService,
        temp_storage_dir: Path,
        test_session: Session,
        sample_user,
    ):
        """Test cleanup actually deletes orphaned files."""
        # Create orphaned file with old timestamp
        orphan = temp_storage_dir / "orphan.jpg"
        test_content = b"test image data"
        create_test_image(orphan, test_content)
        old_time = time.time() - 7200
        os.utime(orphan, (old_time, old_time))

        stats = cleanup_service.cleanup_orphans(test_session, dry_run=False)

        assert stats.files_scanned == 1
        assert stats.orphans_found == 1
        assert stats.orphans_deleted == 1
        assert stats.bytes_reclaimed == len(test_content)
        assert not orphan.exists()  # File should be deleted

    def test_cleanup_orphans_skips_recent_files(
        self,
        cleanup_service: OrphanedFileCleanupService,
        temp_storage_dir: Path,
        test_session: Session,
    ):
        """Test cleanup skips recently created files."""
        # Create orphaned file with current timestamp (recent)
        orphan = temp_storage_dir / "recent_orphan.jpg"
        create_test_image(orphan)

        stats = cleanup_service.cleanup_orphans(test_session, dry_run=False)

        assert stats.files_scanned == 1
        assert stats.orphans_found == 1
        assert stats.orphans_deleted == 0
        assert stats.skipped_recent == 1
        assert orphan.exists()  # File should still exist

    def test_cleanup_orphans_preserves_referenced_files(
        self,
        cleanup_service: OrphanedFileCleanupService,
        temp_storage_dir: Path,
        test_session: Session,
        sample_user,
    ):
        """Test cleanup doesn't delete files referenced by recipes."""
        # Create a referenced file
        referenced = temp_storage_dir / "referenced.jpg"
        create_test_image(referenced)
        old_time = time.time() - 7200
        os.utime(referenced, (old_time, old_time))

        # Create recipe referencing the file
        recipe = Recipe(
            name="Test Recipe",
            source_image_path="referenced.jpg",
            user_id=sample_user.id,
        )
        test_session.add(recipe)
        test_session.commit()

        stats = cleanup_service.cleanup_orphans(test_session, dry_run=False)

        assert stats.files_scanned == 1
        assert stats.orphans_found == 0
        assert stats.orphans_deleted == 0
        assert referenced.exists()  # File should still exist


class TestCleanupStats:
    """Tests for CleanupStats dataclass."""

    def test_dry_run_property_true(self):
        """Test dry_run property when orphans found but not deleted."""
        stats = CleanupStats(
            files_scanned=10,
            orphans_found=5,
            orphans_deleted=0,
            bytes_reclaimed=0,
            skipped_recent=0,
            errors=[],
        )
        assert stats.dry_run is True

    def test_dry_run_property_false_no_orphans(self):
        """Test dry_run property when no orphans found."""
        stats = CleanupStats(
            files_scanned=10,
            orphans_found=0,
            orphans_deleted=0,
            bytes_reclaimed=0,
            skipped_recent=0,
            errors=[],
        )
        assert stats.dry_run is False

    def test_dry_run_property_false_when_deleted(self):
        """Test dry_run property when orphans were deleted."""
        stats = CleanupStats(
            files_scanned=10,
            orphans_found=5,
            orphans_deleted=5,
            bytes_reclaimed=1024,
            skipped_recent=0,
            errors=[],
        )
        assert stats.dry_run is False


class TestAdminCleanupEndpoint:
    """Tests for the admin cleanup API endpoint."""

    def test_cleanup_requires_authentication(self, client):
        """Test cleanup endpoint requires authentication."""
        response = client.post("/api/admin/cleanup-orphans")
        assert response.status_code == 401

    def test_cleanup_dry_run(
        self,
        authenticated_client,
        test_session,
        tmp_path,
    ):
        """Test cleanup endpoint with dry_run=true."""
        # Patch the cleanup service to use a test directory
        with patch("app.routers.admin.get_cleanup_service") as mock_get_service:
            storage_dir = tmp_path / "images"
            storage_dir.mkdir()

            # Create an orphaned file with old timestamp
            orphan = storage_dir / "orphan.jpg"
            orphan.write_bytes(b"test")
            old_time = time.time() - 7200
            os.utime(orphan, (old_time, old_time))

            mock_service = OrphanedFileCleanupService(storage_dir)
            mock_get_service.return_value = mock_service

            response = authenticated_client.post(
                "/api/admin/cleanup-orphans",
                params={"dry_run": True},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["files_scanned"] == 1
        assert data["orphans_found"] == 1
        assert data["orphans_deleted"] == 0

    def test_cleanup_actual_delete(
        self,
        authenticated_client,
        test_session,
        tmp_path,
    ):
        """Test cleanup endpoint actually deletes files."""
        with patch("app.routers.admin.get_cleanup_service") as mock_get_service:
            storage_dir = tmp_path / "images"
            storage_dir.mkdir()

            # Create an orphaned file with old timestamp
            orphan = storage_dir / "orphan.jpg"
            orphan.write_bytes(b"test data")
            old_time = time.time() - 7200
            os.utime(orphan, (old_time, old_time))

            mock_service = OrphanedFileCleanupService(storage_dir)
            mock_get_service.return_value = mock_service

            response = authenticated_client.post(
                "/api/admin/cleanup-orphans",
                params={"dry_run": False},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is False
        assert data["orphans_deleted"] == 1
        assert data["bytes_reclaimed"] == len(b"test data")
        assert not orphan.exists()


class TestGetCleanupService:
    """Tests for get_cleanup_service factory function."""

    def test_get_cleanup_service_uses_settings(self):
        """Test that get_cleanup_service uses settings.image_storage_dir."""
        service = get_cleanup_service()
        from app.config import settings
        assert service.storage_dir == settings.image_storage_dir
