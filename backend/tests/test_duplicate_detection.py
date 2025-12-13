"""
Tests for duplicate detection service.
"""
import pytest
from io import BytesIO
from PIL import Image

from app.models import Recipe
from app.services.duplicate_detector import (
    compute_content_hash,
    compute_perceptual_hash,
    compute_recipe_fingerprint,
    check_for_duplicates,
    compute_hashes_for_recipe,
    check_exact_duplicate,
    check_similar_images,
    check_recipe_fingerprint,
)


def create_test_image(color=(255, 0, 0), size=(100, 100)) -> bytes:
    """Create a simple test image with specified color."""
    img = Image.new("RGB", size, color)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestContentHash:
    """Tests for SHA-256 content hash."""

    def test_same_content_same_hash(self):
        """Identical content produces identical hash."""
        image_data = create_test_image()
        hash1 = compute_content_hash(image_data)
        hash2 = compute_content_hash(image_data)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        """Different content produces different hash."""
        image1 = create_test_image(color=(255, 0, 0))
        image2 = create_test_image(color=(0, 255, 0))
        hash1 = compute_content_hash(image1)
        hash2 = compute_content_hash(image2)
        assert hash1 != hash2

    def test_hash_is_64_chars(self):
        """SHA-256 hash is 64 hex characters."""
        image_data = create_test_image()
        hash_value = compute_content_hash(image_data)
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)


class TestPerceptualHash:
    """Tests for perceptual hash (pHash)."""

    def test_same_image_same_hash(self):
        """Identical images produce identical perceptual hash."""
        image_data = create_test_image()
        hash1 = compute_perceptual_hash(image_data)
        hash2 = compute_perceptual_hash(image_data)
        assert hash1 == hash2

    def test_similar_images_similar_hash(self):
        """Slightly different images produce similar hashes."""
        import imagehash

        # Same color but slightly different size
        image1 = create_test_image(color=(255, 0, 0), size=(100, 100))
        image2 = create_test_image(color=(255, 0, 0), size=(110, 110))

        hash1 = compute_perceptual_hash(image1)
        hash2 = compute_perceptual_hash(image2)

        # Convert to imagehash objects for comparison
        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)

        # Hamming distance should be small for similar images
        distance = h1 - h2
        assert distance < 20  # Should be similar

    def test_very_different_images_different_hash(self):
        """Very different images produce different hashes."""
        import imagehash

        image1 = create_test_image(color=(255, 255, 255))  # White
        image2 = create_test_image(color=(0, 0, 0))  # Black

        hash1 = compute_perceptual_hash(image1)
        hash2 = compute_perceptual_hash(image2)

        h1 = imagehash.hex_to_hash(hash1)
        h2 = imagehash.hex_to_hash(hash2)

        # Hamming distance should be larger for very different images
        distance = h1 - h2
        assert distance > 0  # Should be different

    def test_hash_is_16_chars(self):
        """Perceptual hash is 16 hex characters."""
        image_data = create_test_image()
        hash_value = compute_perceptual_hash(image_data)
        assert len(hash_value) == 16
        assert all(c in "0123456789abcdef" for c in hash_value)


class TestRecipeFingerprint:
    """Tests for recipe fingerprint."""

    def test_same_recipe_same_fingerprint(self):
        """Same name and ingredients produce same fingerprint."""
        fp1 = compute_recipe_fingerprint(
            "Margarita",
            [("Tequila", 2.0, "oz"), ("Lime Juice", 1.0, "oz"), ("Triple Sec", 0.75, "oz")],
        )
        fp2 = compute_recipe_fingerprint(
            "Margarita",
            [("Tequila", 2.0, "oz"), ("Lime Juice", 1.0, "oz"), ("Triple Sec", 0.75, "oz")],
        )
        assert fp1 == fp2

    def test_ingredient_order_doesnt_matter(self):
        """Ingredient order doesn't affect fingerprint."""
        fp1 = compute_recipe_fingerprint(
            "Margarita",
            [("Tequila", 2.0, "oz"), ("Lime Juice", 1.0, "oz")],
        )
        fp2 = compute_recipe_fingerprint(
            "Margarita",
            [("Lime Juice", 1.0, "oz"), ("Tequila", 2.0, "oz")],
        )
        assert fp1 == fp2

    def test_case_insensitive(self):
        """Fingerprint is case-insensitive."""
        fp1 = compute_recipe_fingerprint(
            "MARGARITA",
            [("TEQUILA", 2.0, "OZ")],
        )
        fp2 = compute_recipe_fingerprint(
            "margarita",
            [("tequila", 2.0, "oz")],
        )
        assert fp1 == fp2

    def test_different_recipe_different_fingerprint(self):
        """Different recipes produce different fingerprints."""
        fp1 = compute_recipe_fingerprint(
            "Margarita",
            [("Tequila", 2.0, "oz")],
        )
        fp2 = compute_recipe_fingerprint(
            "Old Fashioned",
            [("Bourbon", 2.0, "oz")],
        )
        assert fp1 != fp2

    def test_different_amounts_different_fingerprint(self):
        """Different amounts produce different fingerprints."""
        fp1 = compute_recipe_fingerprint(
            "Margarita",
            [("Tequila", 2.0, "oz")],
        )
        fp2 = compute_recipe_fingerprint(
            "Margarita",
            [("Tequila", 3.0, "oz")],
        )
        assert fp1 != fp2

    def test_fingerprint_is_32_chars(self):
        """MD5 fingerprint is 32 hex characters."""
        fp = compute_recipe_fingerprint("Test", [("Vodka", 2.0, "oz")])
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)


class TestCheckExactDuplicate:
    """Tests for exact duplicate detection."""

    def test_finds_exact_match(self, test_session):
        """Finds recipe with matching content hash."""
        image_data = create_test_image()
        content_hash = compute_content_hash(image_data)

        # Create a recipe with this hash
        recipe = Recipe(
            name="Test Recipe",
            image_content_hash=content_hash,
        )
        test_session.add(recipe)
        test_session.commit()

        match = check_exact_duplicate(test_session, content_hash)
        assert match is not None
        assert match.recipe_id == recipe.id
        assert match.match_type == "exact_image"
        assert match.confidence == 1.0

    def test_no_match_when_hash_differs(self, test_session):
        """Returns None when no matching hash."""
        image_data = create_test_image()
        content_hash = compute_content_hash(image_data)

        # Create a recipe with different hash
        recipe = Recipe(
            name="Test Recipe",
            image_content_hash="different_hash_value",
        )
        test_session.add(recipe)
        test_session.commit()

        match = check_exact_duplicate(test_session, content_hash)
        assert match is None

    def test_excludes_specified_recipe(self, test_session):
        """Excludes specified recipe from match."""
        image_data = create_test_image()
        content_hash = compute_content_hash(image_data)

        recipe = Recipe(
            name="Test Recipe",
            image_content_hash=content_hash,
        )
        test_session.add(recipe)
        test_session.commit()

        # Should not find match when excluding this recipe
        match = check_exact_duplicate(test_session, content_hash, exclude_recipe_id=recipe.id)
        assert match is None


class TestCheckSimilarImages:
    """Tests for similar image detection."""

    def test_finds_similar_images(self, test_session):
        """Finds visually similar images."""
        image_data = create_test_image(color=(255, 0, 0))
        perceptual_hash = compute_perceptual_hash(image_data)

        # Create a recipe with similar hash
        recipe = Recipe(
            name="Test Recipe",
            image_perceptual_hash=perceptual_hash,
        )
        test_session.add(recipe)
        test_session.commit()

        matches = check_similar_images(test_session, perceptual_hash)
        assert len(matches) == 1
        assert matches[0].recipe_id == recipe.id
        assert matches[0].match_type == "similar_image"
        assert matches[0].confidence == 1.0  # Identical hash = distance 0

    def test_excludes_specified_recipe(self, test_session):
        """Excludes specified recipe from matches."""
        image_data = create_test_image()
        perceptual_hash = compute_perceptual_hash(image_data)

        recipe = Recipe(
            name="Test Recipe",
            image_perceptual_hash=perceptual_hash,
        )
        test_session.add(recipe)
        test_session.commit()

        matches = check_similar_images(test_session, perceptual_hash, exclude_recipe_id=recipe.id)
        assert len(matches) == 0


class TestCheckRecipeFingerprint:
    """Tests for recipe fingerprint matching."""

    def test_finds_matching_fingerprint(self, test_session):
        """Finds recipe with matching fingerprint."""
        fingerprint = compute_recipe_fingerprint("Margarita", [("Tequila", 2.0, "oz")])

        recipe = Recipe(
            name="Margarita",
            recipe_fingerprint=fingerprint,
        )
        test_session.add(recipe)
        test_session.commit()

        match = check_recipe_fingerprint(test_session, fingerprint)
        assert match is not None
        assert match.recipe_id == recipe.id
        assert match.match_type == "same_recipe"
        assert match.confidence == 0.95


class TestCheckForDuplicates:
    """Integration tests for full duplicate check."""

    def test_detects_exact_image_duplicate(self, test_session):
        """Full check detects exact image duplicate."""
        image_data = create_test_image()
        content_hash = compute_content_hash(image_data)

        recipe = Recipe(
            name="Existing Recipe",
            image_content_hash=content_hash,
        )
        test_session.add(recipe)
        test_session.commit()

        result = check_for_duplicates(test_session, image_data)
        assert result.is_duplicate
        assert len(result.matches) >= 1
        assert result.best_match.match_type == "exact_image"

    def test_detects_recipe_fingerprint_duplicate(self, test_session):
        """Full check detects recipe fingerprint duplicate."""
        image_data = create_test_image()
        fingerprint = compute_recipe_fingerprint("Margarita", [("Tequila", 2.0, "oz")])

        recipe = Recipe(
            name="Margarita",
            recipe_fingerprint=fingerprint,
        )
        test_session.add(recipe)
        test_session.commit()

        result = check_for_duplicates(
            test_session,
            image_data,
            recipe_name="Margarita",
            ingredients=[("Tequila", 2.0, "oz")],
        )
        assert result.is_duplicate
        assert any(m.match_type == "same_recipe" for m in result.matches)

    def test_no_duplicates_returns_empty(self, test_session):
        """Returns empty result when no duplicates found."""
        image_data = create_test_image()

        result = check_for_duplicates(test_session, image_data)
        assert not result.is_duplicate
        assert len(result.matches) == 0

    def test_deduplicates_by_recipe_id(self, test_session):
        """Same recipe appearing in multiple checks is deduplicated."""
        image_data = create_test_image()
        content_hash = compute_content_hash(image_data)
        perceptual_hash = compute_perceptual_hash(image_data)

        # Recipe matches both exact and perceptual hash
        recipe = Recipe(
            name="Test Recipe",
            image_content_hash=content_hash,
            image_perceptual_hash=perceptual_hash,
        )
        test_session.add(recipe)
        test_session.commit()

        result = check_for_duplicates(test_session, image_data)
        # Should only appear once despite matching both hashes
        assert len(result.matches) == 1
        assert result.matches[0].recipe_id == recipe.id


class TestComputeHashesForRecipe:
    """Tests for the combined hash computation."""

    def test_returns_all_three_hashes(self):
        """Returns content hash, perceptual hash, and fingerprint."""
        image_data = create_test_image()

        content_hash, perceptual_hash, fingerprint = compute_hashes_for_recipe(
            image_data,
            "Margarita",
            [("Tequila", 2.0, "oz")],
        )

        assert len(content_hash) == 64
        assert len(perceptual_hash) == 16
        assert len(fingerprint) == 32

    def test_consistent_results(self):
        """Same inputs produce same outputs."""
        image_data = create_test_image()

        result1 = compute_hashes_for_recipe(
            image_data, "Margarita", [("Tequila", 2.0, "oz")]
        )
        result2 = compute_hashes_for_recipe(
            image_data, "Margarita", [("Tequila", 2.0, "oz")]
        )

        assert result1 == result2
