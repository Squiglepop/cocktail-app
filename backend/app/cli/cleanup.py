"""
CLI command for cleaning up orphaned image files.

Usage:
    python -m app.cli.cleanup [--dry-run]
"""
import argparse
import logging
import sys

from ..services.cleanup import get_cleanup_service
from ..services.database import SessionLocal


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for CLI output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def format_bytes(size: int) -> str:
    """Format bytes into human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def main() -> int:
    """Main entry point for the cleanup CLI."""
    parser = argparse.ArgumentParser(
        description="Clean up orphaned image files from the storage directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview what would be deleted
    python -m app.cli.cleanup --dry-run

    # Actually delete orphaned files
    python -m app.cli.cleanup

    # Verbose output
    python -m app.cli.cleanup --verbose
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    if args.dry_run:
        logger.info("Running in DRY RUN mode - no files will be deleted")

    # Get database session
    db = SessionLocal()
    try:
        cleanup_service = get_cleanup_service()
        logger.info(f"Scanning image storage directory: {cleanup_service.storage_dir}")

        stats = cleanup_service.cleanup_orphans(db, dry_run=args.dry_run)

        # Print summary
        print("\n" + "=" * 50)
        print("CLEANUP SUMMARY")
        print("=" * 50)
        print(f"Files scanned:     {stats.files_scanned}")
        print(f"Orphans found:     {stats.orphans_found}")
        print(f"Skipped (recent):  {stats.skipped_recent}")

        if args.dry_run:
            print(f"Would delete:      {stats.orphans_found - stats.skipped_recent}")
            print("\nRun without --dry-run to actually delete files.")
        else:
            print(f"Files deleted:     {stats.orphans_deleted}")
            print(f"Space reclaimed:   {format_bytes(stats.bytes_reclaimed)}")

        if stats.errors:
            print(f"\nErrors ({len(stats.errors)}):")
            for error in stats.errors:
                print(f"  - {error}")

        print("=" * 50)

        # Return non-zero exit code if there were errors
        return 1 if stats.errors else 0

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
