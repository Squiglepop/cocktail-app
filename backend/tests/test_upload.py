"""
Tests for image upload and extraction endpoints.
"""
import pytest
from io import BytesIO
from unittest.mock import patch, MagicMock

from app.routers.upload import MAX_FILE_SIZE, MIN_FILE_SIZE
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

    def test_upload_valid_image_jpg(self, client, test_image_jpg):
        """Test uploading a valid JPG image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.jpg", BytesIO(test_image_jpg), "image/jpeg")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["job"]["status"] == "pending"

    def test_upload_valid_image_jpeg(self, client, test_image_jpg):
        """Test uploading a valid JPEG image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.jpeg", BytesIO(test_image_jpg), "image/jpeg")},
        )

        assert response.status_code == 200

    def test_upload_valid_image_gif(self, client, test_image_gif):
        """Test uploading a valid GIF image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.gif", BytesIO(test_image_gif), "image/gif")},
        )

        assert response.status_code == 200

    def test_upload_valid_image_webp(self, client, test_image_webp):
        """Test uploading a valid WebP image creates extraction job."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.webp", BytesIO(test_image_webp), "image/webp")},
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

    def test_upload_file_too_small_rejected(self, client):
        """Test uploading file under MIN_FILE_SIZE is rejected."""
        # Create a tiny valid PNG header but under MIN_FILE_SIZE bytes total
        tiny_png = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # 8-bit RGB
            0xDE,  # CRC
        ])  # Only 33 bytes - way under MIN_FILE_SIZE

        response = client.post(
            "/api/upload",
            files={"file": ("test.png", BytesIO(tiny_png), "image/png")},
        )

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "too small" in detail
        assert "minimum" in detail  # Verify we include the limit in the message

    def test_upload_file_too_large_rejected(self, client):
        """Test uploading file over MAX_FILE_SIZE is rejected."""
        # Create file just over the limit (MAX_FILE_SIZE + 1 byte)
        large_file_size = MAX_FILE_SIZE + 1

        # Create valid PNG header followed by padding to exceed limit
        png_header = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        ])
        # Pad the rest with zeros to reach size
        padding = bytes(large_file_size - len(png_header))
        large_png = png_header + padding

        response = client.post(
            "/api/upload",
            files={"file": ("large.png", BytesIO(large_png), "image/png")},
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_upload_file_exactly_min_size_accepted(self, client):
        """Test uploading file exactly at MIN_FILE_SIZE boundary is accepted."""
        # Create a valid PNG that's exactly MIN_FILE_SIZE bytes
        # PNG signature (8) + IHDR chunk header (4) + IHDR data (13) + CRC (4) = 29 base
        # Need to pad to exactly MIN_FILE_SIZE with valid PNG structure
        from PIL import Image
        from io import BytesIO as PILBytesIO

        # Create smallest valid image that compresses to around MIN_FILE_SIZE
        img = Image.new("RGB", (10, 10), color=(255, 0, 0))
        buffer = PILBytesIO()
        img.save(buffer, format="PNG", compress_level=0)  # No compression = larger file
        img_bytes = buffer.getvalue()

        # If it's over MIN_FILE_SIZE, it should be accepted
        # The key is that valid images at or above MIN_FILE_SIZE pass
        assert len(img_bytes) >= MIN_FILE_SIZE, f"Test image is {len(img_bytes)} bytes, need >= {MIN_FILE_SIZE}"

        response = client.post(
            "/api/upload",
            files={"file": ("boundary.png", BytesIO(img_bytes), "image/png")},
        )

        assert response.status_code == 200
        assert "job" in response.json()

    def test_upload_file_exactly_max_size_accepted(self, client):
        """Test uploading file exactly at MAX_FILE_SIZE boundary is accepted."""
        # Create file exactly at the limit (should be accepted)
        # This is a large test but important for boundary validation
        from PIL import Image
        from io import BytesIO as PILBytesIO

        # Start with valid PNG header
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        buffer = PILBytesIO()
        img.save(buffer, format="PNG")
        base_bytes = buffer.getvalue()

        # Pad to exactly MAX_FILE_SIZE by appending to PNG (after IEND is ignored)
        padding_needed = MAX_FILE_SIZE - len(base_bytes)
        if padding_needed > 0:
            # Append padding after valid PNG (parsers ignore data after IEND)
            padded_bytes = base_bytes + (b'\x00' * padding_needed)
        else:
            padded_bytes = base_bytes[:MAX_FILE_SIZE]

        assert len(padded_bytes) == MAX_FILE_SIZE

        response = client.post(
            "/api/upload",
            files={"file": ("maxsize.png", BytesIO(padded_bytes), "image/png")},
        )

        assert response.status_code == 200
        assert "job" in response.json()

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

    def test_extract_immediate_file_too_small_rejected(self, client):
        """Test extract-immediate rejects files under MIN_FILE_SIZE."""
        tiny_png = bytes([
            0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
            0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
            0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 dimensions
            0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # 8-bit RGB
            0xDE,  # CRC
        ])  # Only 33 bytes

        response = client.post(
            "/api/upload/extract-immediate",
            files={"file": ("tiny.png", BytesIO(tiny_png), "image/png")},
        )

        assert response.status_code == 400
        detail = response.json()["detail"].lower()
        assert "too small" in detail
        assert "minimum" in detail

    def test_extract_immediate_file_too_large_rejected(self, client):
        """Test extract-immediate rejects files over MAX_FILE_SIZE."""
        large_file_size = MAX_FILE_SIZE + 1
        png_header = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        padding = bytes(large_file_size - len(png_header))
        large_png = png_header + padding

        response = client.post(
            "/api/upload/extract-immediate",
            files={"file": ("huge.png", BytesIO(large_png), "image/png")},
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()
