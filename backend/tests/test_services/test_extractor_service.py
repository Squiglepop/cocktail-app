"""
Unit tests for recipe extractor service.
"""
import pytest
from unittest.mock import patch, MagicMock
import json

from app.services.extractor import (
    RecipeExtractor,
    map_to_enum_value,
    map_extracted_to_create,
)
from app.schemas import ExtractedRecipe, ExtractedIngredient
from app.models.enums import (
    CocktailTemplate,
    Glassware,
    ServingStyle,
    Method,
    SpiritCategory,
    IngredientType,
    Unit,
)


class TestMapToEnumValue:
    """Tests for enum value mapping."""

    def test_map_template_exact(self):
        """Test exact template value mapping."""
        result = map_to_enum_value("sour", CocktailTemplate)
        assert result == "sour"

    def test_map_template_fuzzy(self):
        """Test fuzzy template value mapping."""
        result = map_to_enum_value("old fashioned", CocktailTemplate)
        assert result == "old_fashioned"

    def test_map_spirit_exact(self):
        """Test exact spirit category mapping."""
        result = map_to_enum_value("vodka", SpiritCategory)
        assert result == "vodka"

    def test_map_spirit_with_spaces(self):
        """Test spirit mapping with spaces."""
        result = map_to_enum_value("rum light", SpiritCategory)
        assert result == "rum_light"

    def test_map_glassware_exact(self):
        """Test exact glassware mapping."""
        result = map_to_enum_value("coupe", Glassware)
        assert result == "coupe"

    def test_map_serving_style_exact(self):
        """Test exact serving style mapping."""
        result = map_to_enum_value("up", ServingStyle)
        assert result == "up"

    def test_map_method_exact(self):
        """Test exact method mapping."""
        result = map_to_enum_value("shaken", Method)
        assert result == "shaken"

    def test_map_unit_exact(self):
        """Test exact unit mapping."""
        result = map_to_enum_value("oz", Unit)
        assert result == "oz"

    def test_map_none_returns_none(self):
        """Test None value returns None."""
        result = map_to_enum_value(None, CocktailTemplate)
        assert result is None

    def test_map_empty_returns_none(self):
        """Test empty string returns None."""
        result = map_to_enum_value("", CocktailTemplate)
        assert result is None

    def test_map_invalid_returns_none(self):
        """Test invalid value returns None."""
        result = map_to_enum_value("not_a_real_template", CocktailTemplate)
        assert result is None


class TestMapExtractedToCreate:
    """Tests for mapping extracted recipe to creation schema."""

    def test_map_basic_recipe(self):
        """Test mapping a basic extracted recipe."""
        extracted = ExtractedRecipe(
            name="Test Cocktail",
            description="A test description",
            instructions="Shake and strain",
            template="sour",
            main_spirit="vodka",
            glassware="coupe",
            serving_style="up",
            method="shaken",
            garnish="Lime wheel",
            notes="Test notes",
            ingredients=[],
        )

        result = map_extracted_to_create(extracted)

        assert result.name == "Test Cocktail"
        assert result.description == "A test description"
        assert result.instructions == "Shake and strain"
        assert result.template == "sour"
        assert result.main_spirit == "vodka"
        assert result.glassware == "coupe"
        assert result.serving_style == "up"
        assert result.method == "shaken"
        assert result.garnish == "Lime wheel"
        assert result.notes == "Test notes"

    def test_map_with_ingredients(self):
        """Test mapping extracted recipe with ingredients."""
        extracted = ExtractedRecipe(
            name="Cocktail With Ingredients",
            ingredients=[
                ExtractedIngredient(name="Vodka", amount=2.0, unit="oz", type="spirit"),
                ExtractedIngredient(name="Lime Juice", amount=1.0, unit="oz", type="juice"),
                ExtractedIngredient(name="Simple Syrup", amount=0.75, unit="oz", type="syrup"),
            ],
        )

        result = map_extracted_to_create(extracted)

        assert len(result.ingredients) == 3
        assert result.ingredients[0].ingredient_name == "Vodka"
        assert result.ingredients[0].amount == 2.0
        assert result.ingredients[0].unit == "oz"
        assert result.ingredients[0].ingredient_type == "spirit"

    def test_map_handles_missing_fields(self):
        """Test mapping handles missing optional fields."""
        extracted = ExtractedRecipe(
            name="Minimal Cocktail",
            ingredients=[],
        )

        result = map_extracted_to_create(extracted)

        assert result.name == "Minimal Cocktail"
        assert result.description is None
        assert result.template is None
        assert result.main_spirit is None

    def test_map_normalizes_enum_values(self):
        """Test that enum values are normalized properly."""
        extracted = ExtractedRecipe(
            name="Normalized Cocktail",
            template="Old Fashioned",  # Spaces should be handled
            main_spirit="rum light",  # Spaces and case
            glassware="COUPE",  # Uppercase
            ingredients=[],
        )

        result = map_extracted_to_create(extracted)

        assert result.template == "old_fashioned"
        assert result.main_spirit == "rum_light"
        assert result.glassware == "coupe"

    def test_map_ingredient_with_notes(self):
        """Test mapping ingredient with notes."""
        extracted = ExtractedRecipe(
            name="Cocktail",
            ingredients=[
                ExtractedIngredient(
                    name="Mint",
                    amount=8,
                    unit="leaves",
                    type="garnish",
                    notes="muddled"
                ),
            ],
        )

        result = map_extracted_to_create(extracted)

        assert result.ingredients[0].notes == "muddled"


class TestRecipeExtractorParseData:
    """Tests for RecipeExtractor._parse_extracted_data method."""

    def test_parse_full_data(self):
        """Test parsing complete extraction data."""
        extractor = RecipeExtractor.__new__(RecipeExtractor)
        extractor.client = MagicMock()

        data = {
            "name": "Margarita",
            "description": "Classic tequila cocktail",
            "ingredients": [
                {"name": "Tequila", "amount": 2, "unit": "oz", "type": "spirit"},
                {"name": "Lime Juice", "amount": 1, "unit": "oz", "type": "juice"},
            ],
            "instructions": "Shake with ice",
            "template": "sour",
            "main_spirit": "tequila",
            "glassware": "coupe",
            "serving_style": "up",
            "method": "shaken",
            "garnish": "Lime wheel",
            "notes": "Salt rim optional",
        }

        result = extractor._parse_extracted_data(data)

        assert isinstance(result, ExtractedRecipe)
        assert result.name == "Margarita"
        assert len(result.ingredients) == 2
        assert result.ingredients[0].name == "Tequila"

    def test_parse_minimal_data(self):
        """Test parsing minimal extraction data."""
        extractor = RecipeExtractor.__new__(RecipeExtractor)
        extractor.client = MagicMock()

        data = {"name": "Unknown"}

        result = extractor._parse_extracted_data(data)

        assert result.name == "Unknown"
        assert result.ingredients == []

    def test_parse_handles_missing_ingredient_fields(self):
        """Test parsing handles ingredients with missing fields."""
        extractor = RecipeExtractor.__new__(RecipeExtractor)
        extractor.client = MagicMock()

        data = {
            "name": "Test",
            "ingredients": [
                {"name": "Vodka"},  # Missing amount, unit, type
            ],
        }

        result = extractor._parse_extracted_data(data)

        assert len(result.ingredients) == 1
        assert result.ingredients[0].name == "Vodka"
        assert result.ingredients[0].amount is None
        assert result.ingredients[0].unit is None

    def test_parse_defaults_name(self):
        """Test parsing defaults to 'Untitled Recipe' if no name."""
        extractor = RecipeExtractor.__new__(RecipeExtractor)
        extractor.client = MagicMock()

        data = {}

        result = extractor._parse_extracted_data(data)

        assert result.name == "Untitled Recipe"


class TestRecipeExtractorExtract:
    """Tests for RecipeExtractor._extract method with mocked API."""

    def test_extract_parses_json_response(self):
        """Test extraction parses clean JSON response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"name": "Test Cocktail", "ingredients": []}')]

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            extractor = RecipeExtractor()
            result = extractor._extract("base64data", "image/jpeg")

            assert result.name == "Test Cocktail"

    def test_extract_parses_markdown_wrapped_json(self):
        """Test extraction parses JSON wrapped in markdown code blocks."""
        json_content = '{"name": "Margarita", "ingredients": []}'
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=f'```json\n{json_content}\n```')]

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            extractor = RecipeExtractor()
            result = extractor._extract("base64data", "image/jpeg")

            assert result.name == "Margarita"

    def test_extract_invalid_json_raises(self):
        """Test extraction raises error for invalid JSON."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='not valid json')]

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            extractor = RecipeExtractor()
            with pytest.raises(ValueError, match="Failed to parse"):
                extractor._extract("base64data", "image/jpeg")


class TestRecipeExtractorFromFile:
    """Tests for RecipeExtractor.extract_from_file method."""

    def test_extract_from_file_jpg(self, tmp_path):
        """Test extraction from JPG file."""
        # Create a test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"fake image data")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"name": "Test", "ingredients": []}')]

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            extractor = RecipeExtractor()
            result = extractor.extract_from_file(test_file)

            # Verify the media type was set correctly
            call_args = mock_client.messages.create.call_args
            content = call_args.kwargs["messages"][0]["content"]
            image_block = content[0]
            assert image_block["source"]["media_type"] == "image/jpeg"

    def test_extract_from_file_png(self, tmp_path):
        """Test extraction from PNG file."""
        test_file = tmp_path / "test.png"
        test_file.write_bytes(b"fake png data")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"name": "PNG Test", "ingredients": []}')]

        with patch("anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            extractor = RecipeExtractor()
            result = extractor.extract_from_file(test_file)

            call_args = mock_client.messages.create.call_args
            content = call_args.kwargs["messages"][0]["content"]
            image_block = content[0]
            assert image_block["source"]["media_type"] == "image/png"
