"""
Pydantic schemas for cleanup operations.
"""
from typing import List

from pydantic import BaseModel


class CleanupStatsResponse(BaseModel):
    """Response model for cleanup operation statistics."""
    files_scanned: int
    orphans_found: int
    orphans_deleted: int
    bytes_reclaimed: int
    skipped_recent: int
    errors: List[str]
    dry_run: bool

    class Config:
        from_attributes = True
