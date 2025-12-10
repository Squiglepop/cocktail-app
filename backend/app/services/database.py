"""
Database connection and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings
from app.models import Base


# Handle SQLite connection args
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all tables in the database.

    For development/testing convenience. In production, use Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)


def run_migrations():
    """Run Alembic migrations programmatically.

    This is an alternative to running `alembic upgrade head` manually.
    """
    from alembic.config import Config
    from alembic import command

    # Get the directory containing this file
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    alembic_cfg = Config(os.path.join(base_dir, "alembic.ini"))
    alembic_cfg.set_main_option("script_location", os.path.join(base_dir, "alembic"))
    command.upgrade(alembic_cfg, "head")


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
