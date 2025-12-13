"""
Tests for image upload and extraction endpoints.
"""
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock

from app.schemas import ExtractedRecipe, ExtractedIngredient


class TestUploadImage:
    """Tests for POST /api/upload endpoint."""

    def test_upload_valid_image_png(self, client, test_image_file):
        """Test uploading a valid PNG image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.png", BytesIO(test_image_file), "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "job" in data
        assert "id" in data["job"]
        assert data["job"]["status"] == "pending"
        assert data["job"]["image_path"] is not None

    def test_upload_valid_image_jpg(self, client, test_image_file):
        """Test uploading a valid JPG image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.jpg", BytesIO(test_image_file), "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job"]["status"] == "pending"

    def test_upload_valid_image_jpeg(self, client, test_image_file):
        """Test uploading a valid JPEG image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.jpeg", BytesIO(test_image_file), "image/jpeg")},
        )

        assert response.status_code == 200

    def test_upload_valid_image_gif(self, client, test_image_file):
        """Test uploading a valid GIF image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.gif", BytesIO(test_image_file), "image/gif")},
        )

        assert response.status_code == 200

    def test_upload_valid_image_webp(self, client, test_image_file):
        """Test uploading a valid WebP image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.webp", BytesIO(test_image_file), "image/webp")},
        )

        assert response.status_code == 200

    def test_upload_invalid_type(self, client):
        """Test uploading non-image file returns 400."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")},
        )

        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()

    def test_upload_pdf_invalid(self, client):
        """Test uploading PDF file returns 400."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", BytesIO(b"%PDF-1.4"), "application/pdf")},
        )

        assert response.status_code == 400

    def test_upload_detects_duplicate_image(self, client, test_session, test_image_file):
        """Test that uploading same image twice returns duplicate info."""
        from app.models import Recipe
        from app.services.duplicate_detector import compute_content_hash, compute_perceptual_hash

        # Create a recipe with the same image hash
        content_hash = compute_content_hash(test_image_file)
        perceptual_hash = compute_perceptual_hash(test_image_file)

        existing_recipe = Recipe(
            name="Existing Recipe",
            image_content_hash=content_hash,
            image_perceptual_hash=perceptual_hash,
        )
        test_session.add(existing_recipe)
        test_session.commit()

        # Upload same image
        response = client.post(
            "/api/upload",
            files={"file": ("test.png", BytesIO(test_image_file), "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["duplicates"] is not None
        assert data["duplicates"]["is_duplicate"] is True
        assert len(data["duplicates"]["matches"]) >= 1
        assert data["duplicates"]["matches"][0]["recipe_id"] == existing_recipe.id

    def test_upload_skip_duplicate_check(self, client, test_session, test_image_file):
        """Test that duplicate check can be skipped."""
        from app.models import Recipe
        from app.services.duplicate_detector import compute_content_hash

        # Create a recipe with the same image hash
        content_hash = compute_content_hash(test_image_file)
        existing_recipe = Recipe(
            name="Existing Recipe",
            image_content_hash=content_hash,
        )
        test_session.add(existing_recipe)
        test_session.commit()

        # Upload with duplicate check disabled
        response = client.post(
            "/api/upload?check_duplicates=false",
            files={"file": ("test.png", BytesIO(test_image_file), "image/png")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["duplicates"] is None


class TestExtractRecipe:
    """Tests for POST /api/upload/{job_id}/extract endpoint."""

    def test_extract_success(self, client, sample_extraction_job, test_session):
        """Test successful extraction returns recipe."""
        mock_extracted = ExtractedRecipe(
            name="Extracted Cocktail",
            description="A test extraction",
            ingredients=[
                ExtractedIngredient(name="Vodka", amount=2.0, unit="oz", type="spirit"),
            ],
            instructions="Shake and strain",
            template="sour",
            main_spirit="vodka",
            glassware="coupe",
            serving_style="up",
            method="shaken",
        )

        with patch("app.routers.upload.RecipeExtractor") as mock_extractor:
            mock_instance = MagicMock()
            mock_instance.extract_from_file.return_value = mock_extracted
            mock_extractor.return_value = mock_instance

            response = client.post(f"/api/upload/{sample_extraction_job.id}/extract")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Extracted Cocktail"
            assert len(data["ingredients"]) >= 1

    def test_extract_job_not_found(self, client):
        """Test extraction for non-existent job returns 404."""
        response = client.post("/api/upload/non-existent-id/extract")

        assert response.status_code == 404

    def test_extract_already_completed(self, client, sample_extraction_job, sample_recipe, test_session):
        """Test extraction for already completed job returns existing recipe."""
        # Mark job as completed with a recipe
        sample_extraction_job.status = "completed"
        sample_extraction_job.recipe_id = sample_recipe.id
        test_session.commit()

        response = client.post(f"/api/upload/{sample_extraction_job.id}/extract")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_recipe.id

    def test_extract_api_error(self, client, sample_extraction_job, test_session):
        """Test extraction API error is handled properly."""
        with patch("app.routers.upload.RecipeExtractor") as mock_extractor:
            mock_instance = MagicMock()
            mock_instance.extract_from_file.side_effect = Exception("API Error")
            mock_extractor.return_value = mock_instance

            response = client.post(f"/api/upload/{sample_extraction_job.id}/extract")

            assert response.status_code == 500
            assert "extraction failed" in response.json()["detail"].lower()


class TestGetJobStatus:
    """Tests for GET /api/upload/{job_id} endpoint."""

    def test_get_job_status_success(self, client, sample_extraction_job):
        """Test getting job status works."""
        response = client.get(f"/api/upload/{sample_extraction_job.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_extraction_job.id
        assert data["status"] == "pending"

    def test_get_job_status_not_found(self, client):
        """Test getting non-existent job status returns 404."""
        response = client.get("/api/upload/non-existent-id")

        assert response.status_code == 404


class TestExtractImmediate:
    """Tests for POST /api/upload/extract-immediate endpoint."""

    def test_extract_immediate_success(self, client, test_image_file):
        """Test immediate extraction returns recipe."""
        mock_extracted = ExtractedRecipe(
            name="Immediate Cocktail",
            description="Extracted immediately",
            ingredients=[
                ExtractedIngredient(name="Gin", amount=2.0, unit="oz", type="spirit"),
                ExtractedIngredient(name="Tonic", amount=4.0, unit="oz", type="mixer"),
            ],
            instructions="Build in glass",
            template="highball",
            main_spirit="gin",
            glassware="highball",
            serving_style="rocks",
            method="built",
            garnish="Lime wedge",
        )

        with patch("app.routers.upload.RecipeExtractor") as mock_extractor:
            mock_instance = MagicMock()
            mock_instance.extract_from_file.return_value = mock_extracted
            mock_extractor.return_value = mock_instance

            response = client.post(
                "/api/upload/extract-immediate",
                files={"file": ("test.png", BytesIO(test_image_file), "image/png")},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "Immediate Cocktail"
            assert data["source_type"] == "screenshot"

    def test_extract_immediate_invalid_file_type(self, client):
        """Test immediate extraction with invalid file type returns 400."""
        response = client.post(
            "/api/upload/extract-immediate",
            files={"file": ("test.txt", BytesIO(b"not an image"), "text/plain")},
        )

        assert response.status_code == 400

    def test_extract_immediate_api_error(self, client, test_image_file):
        """Test immediate extraction API error is handled properly."""
        with patch("app.routers.upload.RecipeExtractor") as mock_extractor:
            mock_instance = MagicMock()
            mock_instance.extract_from_file.side_effect = Exception("API Error")
            mock_extractor.return_value = mock_instance

            response = client.post(
                "/api/upload/extract-immediate",
                files={"file": ("test.png", BytesIO(test_image_file), "image/png")},
            )

            assert response.status_code == 500
            assert "extraction failed" in response.json()["detail"].lower()

    def test_extract_immediate_no_recipe_found(self, client, test_image_file):
        """Test extraction when no recipe is found in image."""
        with patch("app.routers.upload.RecipeExtractor") as mock_extractor:
            mock_instance = MagicMock()
            mock_instance.extract_from_file.side_effect = ValueError("No recipe found in image")
            mock_extractor.return_value = mock_instance

            response = client.post(
                "/api/upload/extract-immediate",
                files={"file": ("test.png", BytesIO(test_image_file), "image/png")},
            )

            assert response.status_code == 500
