"""
Admin router for administrative operations.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..models import User
from ..schemas import CleanupStatsResponse
from ..services.auth import get_current_user
from ..services.cleanup import get_cleanup_service
from ..services.database import get_db

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/cleanup-orphans", response_model=CleanupStatsResponse)
async def cleanup_orphaned_images(
    dry_run: bool = Query(
        default=False,
        description="If true, only report what would be deleted without actually deleting"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CleanupStatsResponse:
    """
    Clean up orphaned image files.

    Scans the image storage directory and removes files that are not
    referenced by any recipe in the database.

    Requires authentication. Files newer than 1 hour are skipped to
    avoid deleting files from in-progress uploads.
    """
    cleanup_service = get_cleanup_service()
    stats = cleanup_service.cleanup_orphans(db, dry_run=dry_run)

    return CleanupStatsResponse(
        files_scanned=stats.files_scanned,
        orphans_found=stats.orphans_found,
        orphans_deleted=stats.orphans_deleted,
        bytes_reclaimed=stats.bytes_reclaimed,
        skipped_recent=stats.skipped_recent,
        errors=stats.errors,
        dry_run=dry_run,
    )
