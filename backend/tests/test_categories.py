"""
Tests for category endpoints.
"""
import pytest


class TestGetAllCategories:
    """Tests for GET /api/categories endpoint."""

    def test_get_all_categories(self, client):
        """Test getting all categories returns expected structure."""
        response = client.get("/api/categories")

        assert response.status_code == 200
        data = response.json()

        # Check all required keys exist
        assert "templates" in data
        assert "spirits" in data
        assert "glassware" in data
        assert "serving_styles" in data
        assert "methods" in data

        # Check templates have required fields
        assert len(data["templates"]) > 0
        template = data["templates"][0]
        assert "value" in template
        assert "display_name" in template

        # Check spirits have required fields
        assert len(data["spirits"]) > 0
        spirit = data["spirits"][0]
        assert "value" in spirit
        assert "display_name" in spirit

        # Check glassware is grouped
        assert len(data["glassware"]) > 0
        glass_group = data["glassware"][0]
        assert "name" in glass_group
        assert "items" in glass_group
        assert len(glass_group["items"]) > 0

        # Check serving styles
        assert len(data["serving_styles"]) > 0
        style = data["serving_styles"][0]
        assert "value" in style
        assert "display_name" in style

        # Check methods
        assert len(data["methods"]) > 0
        method = data["methods"][0]
        assert "value" in method
        assert "display_name" in method


class TestGetTemplates:
    """Tests for GET /api/categories/templates endpoint."""

    def test_get_templates(self, client):
        """Test getting templates returns list with display names."""
        response = client.get("/api/categories/templates")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check expected templates exist
        template_values = [t["value"] for t in data]
        assert "sour" in template_values
        assert "old_fashioned" in template_values
        assert "martini" in template_values
        assert "negroni" in template_values

        # Check each has required fields
        for template in data:
            assert "value" in template
            assert "display_name" in template
            # description may be None for some

    def test_get_templates_has_descriptions(self, client):
        """Test that templates have descriptions."""
        response = client.get("/api/categories/templates")
        data = response.json()

        # At least some templates should have descriptions
        has_description = [t for t in data if t.get("description")]
        assert len(has_description) > 0


class TestGetSpirits:
    """Tests for GET /api/categories/spirits endpoint."""

    def test_get_spirits(self, client):
        """Test getting spirits returns list."""
        response = client.get("/api/categories/spirits")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check expected spirits exist
        spirit_values = [s["value"] for s in data]
        assert "vodka" in spirit_values
        assert "gin" in spirit_values
        assert "tequila" in spirit_values
        assert "bourbon" in spirit_values
        assert "rum_light" in spirit_values  # Various rum types available

        # Check each has required fields
        for spirit in data:
            assert "value" in spirit
            assert "display_name" in spirit


class TestGetGlassware:
    """Tests for GET /api/categories/glassware endpoint."""

    def test_get_glassware_grouped(self, client):
        """Test getting glassware returns grouped by category."""
        response = client.get("/api/categories/glassware")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check groups have expected structure
        for group in data:
            assert "category" in group
            assert "name" in group
            assert "items" in group
            assert isinstance(group["items"], list)
            assert len(group["items"]) > 0

            # Check items have required fields
            for item in group["items"]:
                assert "value" in item
                assert "display_name" in item

    def test_get_glassware_has_all_categories(self, client):
        """Test glassware includes expected categories."""
        response = client.get("/api/categories/glassware")
        data = response.json()

        category_names = [g["category"] for g in data]

        # Should have at least these categories
        assert "stemmed" in category_names or "Stemmed" in [g["name"] for g in data]


class TestGetServingStyles:
    """Tests for GET /api/categories/serving-styles endpoint."""

    def test_get_serving_styles(self, client):
        """Test getting serving styles returns list with descriptions."""
        response = client.get("/api/categories/serving-styles")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check expected styles exist
        style_values = [s["value"] for s in data]
        assert "up" in style_values
        assert "rocks" in style_values
        assert "neat" in style_values

        # Check each has required fields
        for style in data:
            assert "value" in style
            assert "display_name" in style

    def test_get_serving_styles_has_descriptions(self, client):
        """Test that serving styles have descriptions."""
        response = client.get("/api/categories/serving-styles")
        data = response.json()

        # Check that descriptions exist
        has_description = [s for s in data if s.get("description")]
        assert len(has_description) > 0


class TestGetMethods:
    """Tests for GET /api/categories/methods endpoint."""

    def test_get_methods(self, client):
        """Test getting preparation methods returns list with descriptions."""
        response = client.get("/api/categories/methods")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) > 0

        # Check expected methods exist
        method_values = [m["value"] for m in data]
        assert "shaken" in method_values
        assert "stirred" in method_values
        assert "built" in method_values

        # Check each has required fields
        for method in data:
            assert "value" in method
            assert "display_name" in method

    def test_get_methods_has_descriptions(self, client):
        """Test that methods have descriptions."""
        response = client.get("/api/categories/methods")
        data = response.json()

        # Check that descriptions exist
        has_description = [m for m in data if m.get("description")]
        assert len(has_description) > 0
