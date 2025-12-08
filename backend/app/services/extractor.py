"""
Recipe extraction service using Claude Vision API.
"""
import base64
import json
import re
from pathlib import Path
from typing import Optional

import anthropic

from app.config import settings
from app.schemas import ExtractedRecipe, ExtractedIngredient
from app.models.enums import (
    CocktailTemplate,
    Glassware,
    ServingStyle,
    Method,
    SpiritCategory,
    IngredientType,
    Unit,
    TEMPLATE_DESCRIPTIONS,
)


EXTRACTION_PROMPT = """Analyze this cocktail recipe image and extract all the information you can see.

Return a JSON object with this structure:
{
  "name": "Name of the cocktail",
  "description": "Brief description if visible",
  "ingredients": [
    {
      "name": "ingredient name",
      "amount": 2.0,
      "unit": "oz",
      "notes": "any notes like 'muddled' or 'fresh'",
      "type": "spirit|liqueur|juice|syrup|bitter|mixer|garnish|other"
    }
  ],
  "instructions": "Step by step instructions if visible",
  "template": "The cocktail family/template",
  "main_spirit": "The primary spirit used",
  "glassware": "Type of glass",
  "serving_style": "How it's served (up, rocks, etc.)",
  "method": "Preparation method (shaken, stirred, etc.)",
  "garnish": "Garnish description",
  "notes": "Any additional notes"
}

For template, choose from: """ + ", ".join([f"{t.value} ({TEMPLATE_DESCRIPTIONS.get(t, '')})" for t in CocktailTemplate]) + """

For main_spirit, choose from: """ + ", ".join([s.value for s in SpiritCategory]) + """

For glassware, choose from: """ + ", ".join([g.value for g in Glassware]) + """

For serving_style, choose from: """ + ", ".join([s.value for s in ServingStyle]) + """

For method, choose from: """ + ", ".join([m.value for m in Method]) + """

For ingredient units, prefer: """ + ", ".join([u.value for u in Unit]) + """

Important:
- Extract all ingredients with exact measurements
- Infer the template/family based on the structure if not explicitly stated
- If information is not visible, use null
- Return ONLY the JSON object, no other text
"""


class RecipeExtractor:
    """Extract recipes from images using Claude Vision."""

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def extract_from_file(self, image_path: Path) -> ExtractedRecipe:
        """Extract recipe from an image file."""
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")

        # Determine media type
        suffix = image_path.suffix.lower()
        media_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(suffix, "image/jpeg")

        return self._extract(image_data, media_type)

    def extract_from_base64(
        self, image_data: str, media_type: str = "image/jpeg"
    ) -> ExtractedRecipe:
        """Extract recipe from base64-encoded image data."""
        return self._extract(image_data, media_type)

    def _extract(self, image_data: str, media_type: str) -> ExtractedRecipe:
        """Perform extraction using Claude Vision."""
        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT,
                        },
                    ],
                }
            ],
        )

        # Parse the response
        response_text = message.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse extraction response: {e}")

        return self._parse_extracted_data(data)

    def _parse_extracted_data(self, data: dict) -> ExtractedRecipe:
        """Parse raw extraction data into structured schema."""
        ingredients = []
        for ing_data in data.get("ingredients", []):
            ingredients.append(
                ExtractedIngredient(
                    name=ing_data.get("name", "Unknown"),
                    amount=ing_data.get("amount"),
                    unit=ing_data.get("unit"),
                    notes=ing_data.get("notes"),
                    type=ing_data.get("type"),
                )
            )

        return ExtractedRecipe(
            name=data.get("name", "Unknown Cocktail"),
            description=data.get("description"),
            ingredients=ingredients,
            instructions=data.get("instructions"),
            template=data.get("template"),
            main_spirit=data.get("main_spirit"),
            glassware=data.get("glassware"),
            serving_style=data.get("serving_style"),
            method=data.get("method"),
            garnish=data.get("garnish"),
            notes=data.get("notes"),
        )


def map_to_enum_value(value: Optional[str], enum_class) -> Optional[str]:
    """Safely map a string value to an enum value string."""
    if not value:
        return None

    # Normalize the value
    normalized = value.lower().replace(" ", "_").replace("-", "_")

    # Try direct match
    for member in enum_class:
        if member.value == normalized:
            return member.value

    # Try fuzzy match
    for member in enum_class:
        if normalized in member.value or member.value in normalized:
            return member.value

    return None


def map_extracted_to_create(extracted: ExtractedRecipe):
    """Map extracted recipe to creation schema format."""
    from app.schemas import RecipeCreate, RecipeIngredientCreate

    ingredients = []
    for ing in extracted.ingredients:
        ing_type = map_to_enum_value(ing.type, IngredientType) or "other"
        unit = map_to_enum_value(ing.unit, Unit)
        ingredients.append(
            RecipeIngredientCreate(
                ingredient_name=ing.name,
                ingredient_type=ing_type,
                amount=ing.amount,
                unit=unit,
                notes=ing.notes,
            )
        )

    return RecipeCreate(
        name=extracted.name,
        description=extracted.description,
        instructions=extracted.instructions,
        template=map_to_enum_value(extracted.template, CocktailTemplate),
        main_spirit=map_to_enum_value(extracted.main_spirit, SpiritCategory),
        glassware=map_to_enum_value(extracted.glassware, Glassware),
        serving_style=map_to_enum_value(extracted.serving_style, ServingStyle),
        method=map_to_enum_value(extracted.method, Method),
        garnish=extracted.garnish,
        notes=extracted.notes,
        ingredients=ingredients,
    )


# Keep old function name for backward compatibility
map_to_enum = map_to_enum_value
