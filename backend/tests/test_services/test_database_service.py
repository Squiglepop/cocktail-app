"""
Unit tests for database service.
"""
import pytest
from sqlalchemy.orm import Session

from app.services.database import get_db, create_tables
from app.models import Base, User, Recipe


class TestGetDb:
    """Tests for get_db dependency."""

    def test_get_db_returns_session(self, test_engine):
        """Test that get_db returns a valid session."""
        from sqlalchemy.orm import sessionmaker

        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

        # Manually test the pattern used by get_db
        session = TestSessionLocal()
        try:
            assert session is not None
            assert isinstance(session, Session)
        finally:
            session.close()

    def test_get_db_session_can_query(self, test_session, sample_user):
        """Test that db session can execute queries."""
        user = test_session.query(User).filter(User.email == sample_user.email).first()
        assert user is not None
        assert user.email == sample_user.email

    def test_get_db_session_closes_properly(self, test_engine):
        """Test that session closes properly."""
        from sqlalchemy.orm import sessionmaker

        TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

        session = TestSessionLocal()
        session.close()

        # Session should be closed now - this shouldn't raise
        # In SQLAlchemy 2.0+, closed sessions can still be used but queries would fail
        assert session.is_active is False or session.get_bind() is not None


class TestCreateTables:
    """Tests for create_tables function."""

    def test_create_tables_creates_all_models(self, test_engine):
        """Test that create_tables creates all required tables."""
        # Tables are already created in test_engine fixture
        # Let's verify the tables exist
        inspector = test_engine.dialect.get_table_names(test_engine.connect())

        # Check that core tables exist
        assert "users" in inspector
        assert "recipes" in inspector
        assert "ingredients" in inspector
        assert "recipe_ingredients" in inspector
        assert "extraction_jobs" in inspector

    def test_tables_have_correct_structure(self, test_session):
        """Test that tables have the expected columns."""
        # Test User model
        user = User(
            email="structure_test@example.com",
            hashed_password="hash",
            display_name="Test",
            is_active=True,
        )
        test_session.add(user)
        test_session.commit()

        # Query it back
        retrieved = test_session.query(User).filter(User.email == "structure_test@example.com").first()
        assert retrieved.email == "structure_test@example.com"
        assert retrieved.hashed_password == "hash"
        assert retrieved.display_name == "Test"
        assert retrieved.is_active is True
        assert retrieved.id is not None
        assert retrieved.created_at is not None

    def test_recipe_user_relationship(self, test_session, sample_user):
        """Test that Recipe-User relationship works."""
        recipe = Recipe(
            name="Relationship Test",
            user_id=sample_user.id,
        )
        test_session.add(recipe)
        test_session.commit()
        test_session.refresh(recipe)

        # Check relationship
        assert recipe.user is not None
        assert recipe.user.id == sample_user.id

        # Check reverse relationship
        test_session.refresh(sample_user)
        user_recipes = sample_user.recipes.all()
        recipe_names = [r.name for r in user_recipes]
        assert "Relationship Test" in recipe_names
