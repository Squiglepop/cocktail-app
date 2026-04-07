"""
DB-specific integration tests for category endpoints (Story 1.5).

Tests verify database-driven category queries:
- AC-1: Database-driven queries (not enums)
- AC-2: Response format compatibility
- AC-3: Soft-delete filtering (is_active=false excluded)
- AC-4: Graceful degradation for empty/inactive states
"""
import pytest

from app.models import (
    CategoryTemplate,
    CategoryGlassware,
    CategoryServingStyle,
    CategoryMethod,
    CategorySpirit,
)
from app.models.enums import (
    CocktailTemplate,
    Glassware,
    GlasswareCategory,
    ServingStyle,
    Method,
    SpiritCategory,
)


@pytest.mark.usefixtures("seeded_categories")
class TestCombinedEndpoint:
    """Tests for GET /api/categories (combined endpoint)."""

    def test_get_all_categories_returns_200(self, client):
        """Combined endpoint returns all 5 category types."""
        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "spirits" in data
        assert "glassware" in data
        assert "serving_styles" in data
        assert "methods" in data
        assert len(data["templates"]) == len(CocktailTemplate)
        assert len(data["spirits"]) == len(SpiritCategory)
        assert len(data["methods"]) == len(Method)
        assert len(data["serving_styles"]) == len(ServingStyle)
        assert len(data["glassware"]) == len(GlasswareCategory)

    def test_combined_endpoint_format_matches_frontend_contract(self, client):
        """Validate CategoriesResponse schema shape matches frontend."""
        response = client.get("/api/categories")
        data = response.json()

        # Templates: list of CategoryItem
        template = data["templates"][0]
        assert "value" in template
        assert "display_name" in template
        # description is optional

        # Spirits: list of CategoryItem (no description)
        spirit = data["spirits"][0]
        assert "value" in spirit
        assert "display_name" in spirit

        # Glassware: list of CategoryGroup (name + items, NO category key)
        glass_group = data["glassware"][0]
        assert "name" in glass_group
        assert "items" in glass_group
        assert "category" not in glass_group  # Combined uses CategoryGroup schema
        assert "value" in glass_group["items"][0]
        assert "display_name" in glass_group["items"][0]

        # Serving styles: list of CategoryItem
        style = data["serving_styles"][0]
        assert "value" in style
        assert "display_name" in style

        # Methods: list of CategoryItem
        method = data["methods"][0]
        assert "value" in method
        assert "display_name" in method


@pytest.mark.usefixtures("seeded_categories")
class TestTemplatesEndpoint:
    """Tests for GET /api/categories/templates."""

    def test_get_templates_returns_database_values(self, client):
        """Templates come from DB, not enum."""
        response = client.get("/api/categories/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(CocktailTemplate)
        assert data[0]["value"] == "sour"  # First by sort_order
        assert data[0]["display_name"] == "Sour"
        assert "description" in data[0]

    def test_get_templates_ordered_by_sort_order(self, client):
        """Results respect sort_order."""
        response = client.get("/api/categories/templates")
        data = response.json()
        values = [t["value"] for t in data]
        # First few should match enum order (sort_order = enum index)
        expected_first = [t.value for t in list(CocktailTemplate)[:3]]
        assert values[:3] == expected_first

    def test_get_templates_excludes_inactive(self, client, test_session):
        """Inactive records filtered out."""
        # Deactivate the first template
        first = test_session.query(CategoryTemplate).filter(
            CategoryTemplate.sort_order == 0
        ).first()
        first.is_active = False
        test_session.commit()

        response = client.get("/api/categories/templates")
        data = response.json()
        assert len(data) == len(CocktailTemplate) - 1
        deactivated_values = [t["value"] for t in data]
        assert first.value not in deactivated_values


@pytest.mark.usefixtures("seeded_categories")
class TestGlasswareEndpoint:
    """Tests for GET /api/categories/glassware."""

    def test_get_glassware_grouped_by_category(self, client):
        """Glassware grouped into stemmed/short/tall/specialty."""
        response = client.get("/api/categories/glassware")
        assert response.status_code == 200
        data = response.json()
        group_names = [g["name"] for g in data]
        assert "Stemmed" in group_names
        assert "Short" in group_names
        assert "Tall" in group_names
        assert "Specialty" in group_names

    def test_get_glassware_individual_has_category_key(self, client):
        """Individual endpoint returns category field."""
        response = client.get("/api/categories/glassware")
        data = response.json()
        for group in data:
            assert "category" in group  # Raw dict has category key
            assert "name" in group
            assert "items" in group


@pytest.mark.usefixtures("seeded_categories")
class TestSpiritsEndpoint:
    """Tests for GET /api/categories/spirits."""

    def test_get_spirits_returns_database_values(self, client):
        """Spirits come from DB."""
        response = client.get("/api/categories/spirits")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(SpiritCategory)
        spirit_values = [s["value"] for s in data]
        assert "gin" in spirit_values
        assert "vodka" in spirit_values


@pytest.mark.usefixtures("seeded_categories")
class TestServingStylesEndpoint:
    """Tests for GET /api/categories/serving-styles."""

    def test_get_serving_styles_returns_database_values(self, client):
        """Serving styles come from DB."""
        response = client.get("/api/categories/serving-styles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(ServingStyle)
        style_values = [s["value"] for s in data]
        assert "up" in style_values
        assert "rocks" in style_values


@pytest.mark.usefixtures("seeded_categories")
class TestMethodsEndpoint:
    """Tests for GET /api/categories/methods."""

    def test_get_methods_returns_database_values(self, client):
        """Methods come from DB."""
        response = client.get("/api/categories/methods")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(Method)
        method_values = [m["value"] for m in data]
        assert "shaken" in method_values
        assert "stirred" in method_values


class TestEmptyAndInactiveStates:
    """Tests for empty tables and all-inactive scenarios."""

    def test_empty_table_returns_empty_list(self, client):
        """Graceful empty state — no seeded fixture, tables are empty."""
        response = client.get("/api/categories/templates")
        assert response.status_code == 200
        assert response.json() == []

    def test_all_inactive_returns_empty_list(self, client, test_session):
        """All soft-deleted returns empty."""
        # Add one inactive template
        test_session.add(CategoryTemplate(
            value="test_inactive",
            label="Test Inactive",
            description=None,
            sort_order=0,
            is_active=False,
        ))
        test_session.commit()

        response = client.get("/api/categories/templates")
        assert response.status_code == 200
        assert response.json() == []


class TestGracefulDegradationAC4:
    """AC-4: Recipes with inactive category values still display correctly."""

    @pytest.mark.usefixtures("seeded_categories")
    def test_recipe_with_inactive_category_still_returns(
        self, client, test_session, sample_recipe
    ):
        """Recipe with template='sour' still returns after 'sour' is deactivated."""
        # Verify recipe exists and has the category value
        response = client.get(f"/api/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        assert response.json()["template"] == "sour"

        # Deactivate the 'sour' template
        sour = test_session.query(CategoryTemplate).filter(
            CategoryTemplate.value == "sour"
        ).first()
        sour.is_active = False
        test_session.commit()

        # Recipe endpoint must still return the recipe with its category value
        response = client.get(f"/api/recipes/{sample_recipe.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["template"] == "sour"
        assert data["name"] == "Margarita"

    @pytest.mark.usefixtures("seeded_categories")
    def test_recipe_list_includes_recipes_with_inactive_categories(
        self, client, test_session, sample_recipe
    ):
        """Recipe list still includes recipes whose category was deactivated."""
        # Deactivate the 'sour' template
        sour = test_session.query(CategoryTemplate).filter(
            CategoryTemplate.value == "sour"
        ).first()
        sour.is_active = False
        test_session.commit()

        # Recipe list must still include the recipe
        response = client.get("/api/recipes")
        assert response.status_code == 200
        data = response.json()
        recipe_names = [r["name"] for r in data]
        assert "Margarita" in recipe_names
