"""
Pytest fixtures for backend tests.
"""
import os
import sys
from datetime import timedelta
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.models import Base, User, Recipe, Ingredient, RecipeIngredient, ExtractionJob
from app.services.database import get_db
from app.services.auth import hash_password, create_access_token


# Test database URL - using SQLite in-memory
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def client(test_session) -> Generator[TestClient, None, None]:
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield test_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(test_session) -> User:
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
        display_name="Test User",
        is_active=True,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(test_session) -> User:
    """Create an inactive user for testing."""
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("testpassword123"),
        display_name="Inactive User",
        is_active=False,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def another_user(test_session) -> User:
    """Create another user for ownership tests."""
    user = User(
        email="another@example.com",
        hashed_password=hash_password("anotherpassword123"),
        display_name="Another User",
        is_active=True,
    )
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def auth_token(sample_user) -> str:
    """Create a valid JWT token for the sample user."""
    return create_access_token(
        data={"sub": sample_user.id},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def another_auth_token(another_user) -> str:
    """Create a valid JWT token for another user."""
    return create_access_token(
        data={"sub": another_user.id},
        expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def expired_token(sample_user) -> str:
    """Create an expired JWT token."""
    return create_access_token(
        data={"sub": sample_user.id},
        expires_delta=timedelta(seconds=-10)  # Already expired
    )


@pytest.fixture
def authenticated_client(client, auth_token) -> TestClient:
    """Create a test client with authentication headers."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client


@pytest.fixture
def sample_ingredient(test_session) -> Ingredient:
    """Create a sample ingredient for testing."""
    ingredient = Ingredient(
        name="Tequila",
        type="spirit",
        spirit_category="tequila",
        description="A distilled spirit made from blue agave",
    )
    test_session.add(ingredient)
    test_session.commit()
    test_session.refresh(ingredient)
    return ingredient


@pytest.fixture
def sample_recipe(test_session, sample_user, sample_ingredient) -> Recipe:
    """Create a sample recipe for testing."""
    recipe = Recipe(
        name="Margarita",
        description="A classic tequila cocktail",
        instructions="1. Shake all ingredients with ice. 2. Strain into a salt-rimmed glass.",
        template="sour",
        main_spirit="tequila",
        glassware="coupe",
        serving_style="up",
        method="shaken",
        garnish="Lime wheel",
        notes="Classic recipe",
        source_type="manual",
        user_id=sample_user.id,
    )
    test_session.add(recipe)
    test_session.flush()

    # Add ingredient to recipe
    recipe_ingredient = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=sample_ingredient.id,
        amount=2.0,
        unit="oz",
        order=0,
    )
    test_session.add(recipe_ingredient)
    test_session.commit()
    test_session.refresh(recipe)
    return recipe


@pytest.fixture
def orphan_recipe(test_session, sample_ingredient) -> Recipe:
    """Create a recipe without an owner for backwards compatibility tests."""
    recipe = Recipe(
        name="Old Fashioned",
        description="A classic whiskey cocktail",
        instructions="1. Muddle sugar with bitters. 2. Add whiskey and stir.",
        template="old_fashioned",
        main_spirit="bourbon",
        glassware="rocks",
        serving_style="rocks",
        method="built",
        garnish="Orange peel",
        source_type="manual",
        user_id=None,  # No owner
    )
    test_session.add(recipe)
    test_session.flush()

    # Add ingredient to recipe
    recipe_ingredient = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=sample_ingredient.id,
        amount=2.0,
        unit="oz",
        order=0,
    )
    test_session.add(recipe_ingredient)
    test_session.commit()
    test_session.refresh(recipe)
    return recipe


@pytest.fixture
def sample_extraction_job(test_session, tmp_path) -> ExtractionJob:
    """Create a sample extraction job for testing."""
    # Create a minimal valid JPEG file for testing
    # JPEG magic bytes + minimal valid structure
    jpeg_bytes = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
        0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
        0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
        0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
        0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x1F, 0x00, 0x00,
        0x01, 0x05, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0xFF, 0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04, 0x00, 0x00, 0x01, 0x7D,
        0x01, 0x02, 0x03, 0x00, 0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32, 0x81, 0x91, 0xA1, 0x08,
        0x23, 0x42, 0xB1, 0xC1, 0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59,
        0x5A, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85, 0x86, 0x87, 0x88, 0x89,
        0x8A, 0x92, 0x93, 0x94, 0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2, 0xB3, 0xB4, 0xB5, 0xB6,
        0xB7, 0xB8, 0xB9, 0xBA, 0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8, 0xD9, 0xDA, 0xE1, 0xE2,
        0xE3, 0xE4, 0xE5, 0xE6, 0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01,
        0x00, 0x00, 0x3F, 0x00, 0xFB, 0xD5, 0xDB, 0x20, 0xA8, 0xA0, 0x02, 0x8A,
        0x00, 0xFF, 0xD9
    ])
    test_image = tmp_path / "test_image.jpg"
    test_image.write_bytes(jpeg_bytes)

    job = ExtractionJob(
        image_path=str(test_image),
        status="pending",
    )
    test_session.add(job)
    test_session.commit()
    test_session.refresh(job)
    return job


@pytest.fixture
def mock_extractor():
    """Mock the RecipeExtractor for testing without API calls."""
    from app.schemas import ExtractedRecipe, ExtractedIngredient

    mock_extracted = ExtractedRecipe(
        name="Test Cocktail",
        description="A test cocktail description",
        ingredients=[
            ExtractedIngredient(
                name="Vodka",
                amount=2.0,
                unit="oz",
                type="spirit",
            ),
            ExtractedIngredient(
                name="Lime Juice",
                amount=1.0,
                unit="oz",
                type="juice",
            ),
        ],
        instructions="Shake and strain",
        template="sour",
        main_spirit="vodka",
        glassware="coupe",
        serving_style="up",
        method="shaken",
        garnish="Lime wheel",
    )

    with patch("app.routers.upload.RecipeExtractor") as mock:
        mock_instance = MagicMock()
        mock_instance.extract_from_file.return_value = mock_extracted
        mock.return_value = mock_instance
        yield mock_instance


# 1x1 pixel PNG for upload tests
TEST_IMAGE_DATA = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # 8-bit RGB
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0x0F, 0x00, 0x00,  # Image data
    0x01, 0x01, 0x01, 0x00, 0x18, 0xDD, 0x8D, 0xB4,
    0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND chunk
    0xAE, 0x42, 0x60, 0x82,
])


@pytest.fixture
def test_image_file():
    """Create a test image file data."""
    return TEST_IMAGE_DATA
