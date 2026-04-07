"""
Tests for category database tables (Story 1.4).

Tests verify:
- AC-1: All 5 category tables exist with correct columns
- AC-2: Seed values match Python enum strings exactly
- AC-3: No orphaned recipe category values
- AC-4: Index on recipe_ingredients.ingredient_id exists
"""
import pytest
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from app.models import (
    CategoryTemplate,
    CategoryGlassware,
    CategoryServingStyle,
    CategoryMethod,
    CategorySpirit,
    Recipe,
    Base,
)
from app.models.enums import (
    CocktailTemplate,
    Glassware,
    ServingStyle,
    Method,
    SpiritCategory,
    TEMPLATE_DISPLAY_NAMES,
    TEMPLATE_DESCRIPTIONS,
    GLASSWARE_DISPLAY_NAMES,
    GLASSWARE_CATEGORIES,
    SERVING_STYLE_DESCRIPTIONS,
    METHOD_DESCRIPTIONS,
)


@pytest.fixture
def seeded_session(test_session: Session):
    """Create a session with seeded category data."""
    # Seed category_templates
    for i, template in enumerate(CocktailTemplate):
        cat = CategoryTemplate(
            value=template.value,
            label=TEMPLATE_DISPLAY_NAMES.get(template, template.value.replace("_", " ").title()),
            description=TEMPLATE_DESCRIPTIONS.get(template),
            sort_order=i,
            is_active=True,
        )
        test_session.add(cat)

    # Seed category_glassware
    for i, glass in enumerate(Glassware):
        cat = CategoryGlassware(
            value=glass.value,
            label=GLASSWARE_DISPLAY_NAMES.get(glass, glass.value.replace("_", " ").title()),
            category=GLASSWARE_CATEGORIES.get(glass, "specialty").value,
            sort_order=i,
            is_active=True,
        )
        test_session.add(cat)

    # Seed category_serving_styles
    for i, style in enumerate(ServingStyle):
        cat = CategoryServingStyle(
            value=style.value,
            label=style.value.replace("_", " ").title(),
            description=SERVING_STYLE_DESCRIPTIONS.get(style),
            sort_order=i,
            is_active=True,
        )
        test_session.add(cat)

    # Seed category_methods
    for i, method in enumerate(Method):
        cat = CategoryMethod(
            value=method.value,
            label=method.value.replace("_", " ").title(),
            description=METHOD_DESCRIPTIONS.get(method),
            sort_order=i,
            is_active=True,
        )
        test_session.add(cat)

    # Seed category_spirits
    for i, spirit in enumerate(SpiritCategory):
        cat = CategorySpirit(
            value=spirit.value,
            label=spirit.value.replace("_", " ").title(),
            sort_order=i,
            is_active=True,
        )
        test_session.add(cat)

    test_session.commit()
    return test_session


# AC-1: Table existence tests
class TestCategoryTablesExist:
    """Verify all 5 category tables exist with correct columns."""

    def test_category_template_table_exists(self, test_session: Session):
        """category_templates table exists with required columns."""
        inspector = inspect(test_session.get_bind())
        tables = inspector.get_table_names()
        assert "category_templates" in tables

        columns = {col["name"] for col in inspector.get_columns("category_templates")}
        expected = {"id", "value", "label", "description", "sort_order", "is_active", "created_at"}
        assert expected.issubset(columns)

    def test_category_glassware_table_exists(self, test_session: Session):
        """category_glassware table exists with required columns including category."""
        inspector = inspect(test_session.get_bind())
        tables = inspector.get_table_names()
        assert "category_glassware" in tables

        columns = {col["name"] for col in inspector.get_columns("category_glassware")}
        expected = {"id", "value", "label", "category", "sort_order", "is_active", "created_at"}
        assert expected.issubset(columns)

    def test_category_serving_style_table_exists(self, test_session: Session):
        """category_serving_styles table exists with required columns."""
        inspector = inspect(test_session.get_bind())
        tables = inspector.get_table_names()
        assert "category_serving_styles" in tables

        columns = {col["name"] for col in inspector.get_columns("category_serving_styles")}
        expected = {"id", "value", "label", "description", "sort_order", "is_active", "created_at"}
        assert expected.issubset(columns)

    def test_category_method_table_exists(self, test_session: Session):
        """category_methods table exists with required columns."""
        inspector = inspect(test_session.get_bind())
        tables = inspector.get_table_names()
        assert "category_methods" in tables

        columns = {col["name"] for col in inspector.get_columns("category_methods")}
        expected = {"id", "value", "label", "description", "sort_order", "is_active", "created_at"}
        assert expected.issubset(columns)

    def test_category_spirit_table_exists(self, test_session: Session):
        """category_spirits table exists with required columns (no description)."""
        inspector = inspect(test_session.get_bind())
        tables = inspector.get_table_names()
        assert "category_spirits" in tables

        columns = {col["name"] for col in inspector.get_columns("category_spirits")}
        expected = {"id", "value", "label", "sort_order", "is_active", "created_at"}
        assert expected.issubset(columns)
        # Spirits table should NOT have description column
        assert "description" not in columns


# AC-2: Seed value tests
class TestCategorySeedValues:
    """Verify seed values match Python enum strings exactly."""

    def test_category_seed_values_match_enum_strings(self, seeded_session: Session):
        """CRITICAL: category_templates.value contains exact enum strings."""
        # Get all template values from database
        db_values = {
            row.value for row in seeded_session.query(CategoryTemplate.value).all()
        }
        # Get all enum values
        enum_values = {template.value for template in CocktailTemplate}
        # They must match exactly
        assert db_values == enum_values, f"Mismatch: DB={db_values}, Enum={enum_values}"

    def test_glassware_values_match_enum_strings(self, seeded_session: Session):
        """category_glassware.value contains exact enum strings."""
        db_values = {
            row.value for row in seeded_session.query(CategoryGlassware.value).all()
        }
        enum_values = {glass.value for glass in Glassware}
        assert db_values == enum_values

    def test_serving_style_values_match_enum_strings(self, seeded_session: Session):
        """category_serving_styles.value contains exact enum strings."""
        db_values = {
            row.value for row in seeded_session.query(CategoryServingStyle.value).all()
        }
        enum_values = {style.value for style in ServingStyle}
        assert db_values == enum_values

    def test_method_values_match_enum_strings(self, seeded_session: Session):
        """category_methods.value contains exact enum strings."""
        db_values = {
            row.value for row in seeded_session.query(CategoryMethod.value).all()
        }
        enum_values = {method.value for method in Method}
        assert db_values == enum_values

    def test_spirit_values_match_enum_strings(self, seeded_session: Session):
        """category_spirits.value contains exact enum strings."""
        db_values = {
            row.value for row in seeded_session.query(CategorySpirit.value).all()
        }
        enum_values = {spirit.value for spirit in SpiritCategory}
        assert db_values == enum_values

    def test_category_seed_preserves_sort_order(self, seeded_session: Session):
        """sort_order matches enum definition order (starting from 0)."""
        # Templates
        templates = seeded_session.query(CategoryTemplate).order_by(CategoryTemplate.sort_order).all()
        expected_order = [t.value for t in CocktailTemplate]
        actual_order = [t.value for t in templates]
        assert actual_order == expected_order, "Template sort order doesn't match enum order"

        # Glassware
        glassware = seeded_session.query(CategoryGlassware).order_by(CategoryGlassware.sort_order).all()
        expected_order = [g.value for g in Glassware]
        actual_order = [g.value for g in glassware]
        assert actual_order == expected_order, "Glassware sort order doesn't match enum order"

    def test_all_seed_values_are_active(self, seeded_session: Session):
        """All seeded category values have is_active = true."""
        for model in [CategoryTemplate, CategoryGlassware, CategoryServingStyle, CategoryMethod, CategorySpirit]:
            inactive = seeded_session.query(model).filter(model.is_active == False).count()
            assert inactive == 0, f"{model.__name__} has {inactive} inactive records"


# AC-2 Migration validation: verify hardcoded seed lists match enums
class TestMigrationSeedDataMatchesEnums:
    """Validate that the migration's hardcoded seed lists are in sync with Python enums.

    The seeded_session fixture seeds from enums directly. These tests import
    the migration's hardcoded lists and compare them against the enums to catch
    drift between the two sources of truth.
    """

    @pytest.fixture(scope="class")
    def seed_migration(self):
        """Load the seed migration module by file path."""
        import importlib.util
        from pathlib import Path
        migration_dir = Path(__file__).parent.parent / "alembic" / "versions"
        seed_files = list(migration_dir.glob("*seed_categories_from_enums*.py"))
        assert len(seed_files) == 1, f"Expected 1 seed migration, found {len(seed_files)}"
        spec = importlib.util.spec_from_file_location("seed_migration", seed_files[0])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_migration_template_values_match_enums(self, seed_migration):
        """Migration TEMPLATES list values match CocktailTemplate enum exactly."""
        migration_values = {t[0] for t in seed_migration.TEMPLATES}
        enum_values = {t.value for t in CocktailTemplate}
        assert migration_values == enum_values, (
            f"Migration TEMPLATES drift! "
            f"In migration only: {migration_values - enum_values}, "
            f"In enum only: {enum_values - migration_values}"
        )

    def test_migration_glassware_values_match_enums(self, seed_migration):
        """Migration GLASSWARE list values match Glassware enum exactly."""
        migration_values = {g[0] for g in seed_migration.GLASSWARE}
        enum_values = {g.value for g in Glassware}
        assert migration_values == enum_values, (
            f"Migration GLASSWARE drift! "
            f"In migration only: {migration_values - enum_values}, "
            f"In enum only: {enum_values - migration_values}"
        )

    def test_migration_serving_styles_values_match_enums(self, seed_migration):
        """Migration SERVING_STYLES list values match ServingStyle enum exactly."""
        migration_values = {s[0] for s in seed_migration.SERVING_STYLES}
        enum_values = {s.value for s in ServingStyle}
        assert migration_values == enum_values, (
            f"Migration SERVING_STYLES drift! "
            f"In migration only: {migration_values - enum_values}, "
            f"In enum only: {enum_values - migration_values}"
        )

    def test_migration_methods_values_match_enums(self, seed_migration):
        """Migration METHODS list values match Method enum exactly."""
        migration_values = {m[0] for m in seed_migration.METHODS}
        enum_values = {m.value for m in Method}
        assert migration_values == enum_values, (
            f"Migration METHODS drift! "
            f"In migration only: {migration_values - enum_values}, "
            f"In enum only: {enum_values - migration_values}"
        )

    def test_migration_spirits_values_match_enums(self, seed_migration):
        """Migration SPIRITS list values match SpiritCategory enum exactly."""
        migration_values = {s[0] for s in seed_migration.SPIRITS}
        enum_values = {s.value for s in SpiritCategory}
        assert migration_values == enum_values, (
            f"Migration SPIRITS drift! "
            f"In migration only: {migration_values - enum_values}, "
            f"In enum only: {enum_values - migration_values}"
        )

    def test_migration_template_count_matches_enum(self, seed_migration):
        """Migration TEMPLATES list has same count as CocktailTemplate enum."""
        assert len(seed_migration.TEMPLATES) == len(CocktailTemplate), (
            f"Count mismatch: migration has {len(seed_migration.TEMPLATES)}, enum has {len(CocktailTemplate)}"
        )

    def test_migration_spirits_count_matches_enum(self, seed_migration):
        """Migration SPIRITS list has same count as SpiritCategory enum."""
        assert len(seed_migration.SPIRITS) == len(SpiritCategory), (
            f"Count mismatch: migration has {len(seed_migration.SPIRITS)}, enum has {len(SpiritCategory)}"
        )


# AC-3: No orphaned values test
class TestNoOrphanedValues:
    """Verify no recipes have orphaned category values."""

    def test_no_orphaned_recipe_category_values(self, seeded_session: Session, sample_recipe: Recipe):
        """All recipe category values exist in category tables."""
        # Get distinct template values from recipes
        result = seeded_session.execute(text("""
            SELECT DISTINCT template FROM recipes
            WHERE template IS NOT NULL
            AND template NOT IN (SELECT value FROM category_templates)
        """))
        orphaned_templates = result.fetchall()
        assert len(orphaned_templates) == 0, f"Orphaned templates: {orphaned_templates}"

        # Glassware
        result = seeded_session.execute(text("""
            SELECT DISTINCT glassware FROM recipes
            WHERE glassware IS NOT NULL
            AND glassware NOT IN (SELECT value FROM category_glassware)
        """))
        orphaned_glassware = result.fetchall()
        assert len(orphaned_glassware) == 0, f"Orphaned glassware: {orphaned_glassware}"

        # Serving style
        result = seeded_session.execute(text("""
            SELECT DISTINCT serving_style FROM recipes
            WHERE serving_style IS NOT NULL
            AND serving_style NOT IN (SELECT value FROM category_serving_styles)
        """))
        orphaned_styles = result.fetchall()
        assert len(orphaned_styles) == 0, f"Orphaned serving styles: {orphaned_styles}"

        # Method
        result = seeded_session.execute(text("""
            SELECT DISTINCT method FROM recipes
            WHERE method IS NOT NULL
            AND method NOT IN (SELECT value FROM category_methods)
        """))
        orphaned_methods = result.fetchall()
        assert len(orphaned_methods) == 0, f"Orphaned methods: {orphaned_methods}"

        # Main spirit
        result = seeded_session.execute(text("""
            SELECT DISTINCT main_spirit FROM recipes
            WHERE main_spirit IS NOT NULL
            AND main_spirit NOT IN (SELECT value FROM category_spirits)
        """))
        orphaned_spirits = result.fetchall()
        assert len(orphaned_spirits) == 0, f"Orphaned spirits: {orphaned_spirits}"


# AC-4: Index test
class TestIngredientIdIndex:
    """Verify index exists on recipe_ingredients.ingredient_id."""

    def test_ingredient_id_index_exists(self, test_session: Session):
        """Index ix_recipe_ingredients_ingredient_id exists for query performance."""
        inspector = inspect(test_session.get_bind())
        indexes = inspector.get_indexes("recipe_ingredients")
        index_names = {idx["name"] for idx in indexes}

        # The index should exist (either by name or covering ingredient_id)
        # Check if any index covers ingredient_id column
        ingredient_id_indexed = any(
            "ingredient_id" in idx["column_names"]
            for idx in indexes
        )
        assert ingredient_id_indexed, (
            f"No index found on recipe_ingredients.ingredient_id. "
            f"Existing indexes: {index_names}"
        )


# Model creation tests
class TestCategoryModelCreation:
    """Test creating category model instances."""

    def test_create_category_template(self, test_session: Session):
        """Can create and persist a CategoryTemplate."""
        template = CategoryTemplate(
            value="test_template",
            label="Test Template",
            description="A test template",
            sort_order=999,
            is_active=True,
        )
        test_session.add(template)
        test_session.commit()
        test_session.refresh(template)

        assert template.id is not None
        assert template.value == "test_template"
        assert template.created_at is not None

    def test_category_template_value_unique_constraint(self, test_session: Session):
        """CategoryTemplate.value must be unique."""
        t1 = CategoryTemplate(value="unique_test", label="Test 1", sort_order=0, is_active=True)
        test_session.add(t1)
        test_session.commit()

        t2 = CategoryTemplate(value="unique_test", label="Test 2", sort_order=1, is_active=True)
        test_session.add(t2)

        with pytest.raises(Exception):  # IntegrityError
            test_session.commit()

    def test_glassware_has_category_field(self, test_session: Session):
        """CategoryGlassware has category field for grouping."""
        glass = CategoryGlassware(
            value="test_glass",
            label="Test Glass",
            category="specialty",
            sort_order=0,
            is_active=True,
        )
        test_session.add(glass)
        test_session.commit()

        assert glass.category == "specialty"


# Row count tests (based on actual enum counts)
class TestCategoryRowCounts:
    """Verify expected row counts after seeding."""

    def test_template_row_count(self, seeded_session: Session):
        """category_templates has correct row count."""
        count = seeded_session.query(CategoryTemplate).count()
        expected = len(CocktailTemplate)
        assert count == expected, f"Expected {expected} templates, got {count}"

    def test_glassware_row_count(self, seeded_session: Session):
        """category_glassware has correct row count."""
        count = seeded_session.query(CategoryGlassware).count()
        expected = len(Glassware)
        assert count == expected, f"Expected {expected} glassware, got {count}"

    def test_serving_styles_row_count(self, seeded_session: Session):
        """category_serving_styles has correct row count."""
        count = seeded_session.query(CategoryServingStyle).count()
        expected = len(ServingStyle)
        assert count == expected, f"Expected {expected} serving styles, got {count}"

    def test_methods_row_count(self, seeded_session: Session):
        """category_methods has correct row count."""
        count = seeded_session.query(CategoryMethod).count()
        expected = len(Method)
        assert count == expected, f"Expected {expected} methods, got {count}"

    def test_spirits_row_count(self, seeded_session: Session):
        """category_spirits has correct row count."""
        count = seeded_session.query(CategorySpirit).count()
        expected = len(SpiritCategory)
        assert count == expected, f"Expected {expected} spirits, got {count}"
