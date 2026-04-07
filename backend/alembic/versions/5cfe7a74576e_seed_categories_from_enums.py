"""seed_categories_from_enums

Revision ID: 5cfe7a74576e
Revises: 5c3647b698e1
Create Date: 2026-01-30 10:47:10.323040

Story 1.4 AC-2: Seed category tables from Python enums.
Values MUST match enum strings exactly (snake_case) for recipe compatibility.
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cfe7a74576e'
down_revision: Union[str, None] = '5c3647b698e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Seed data - values MUST match Python enum strings exactly
TEMPLATES = [
    ("sour", "Sour", "Spirit + citrus + sweet"),
    ("old_fashioned", "Old Fashioned", "Spirit + sugar + bitters"),
    ("martini", "Martini", "Spirit + vermouth"),
    ("negroni", "Negroni", "Spirit + bitter liqueur + vermouth"),
    ("highball", "Highball", "Spirit + lengthener"),
    ("collins", "Collins", "Sour + soda (on ice)"),
    ("fizz", "Fizz", "Sour + soda (no ice in glass)"),
    ("spritz", "Spritz", "Aperitif + sparkling wine + soda"),
    ("buck_mule", "Buck/Mule", "Spirit + ginger beer + citrus"),
    ("julep", "Julep", "Spirit + sugar + mint (crushed ice)"),
    ("smash", "Smash", "Julep + citrus"),
    ("swizzle", "Swizzle", "Spirit + citrus + sweet + bitters (crushed ice, swizzled)"),
    ("cobbler", "Cobbler", "Wine/spirit + sugar + fruit (crushed ice)"),
    ("punch", "Punch", "Spirit + citrus + sweet + tea/water + spice"),
    ("clarified_punch", "Clarified Punch", "Milk-clarified punch"),
    ("flip", "Flip", "Spirit + whole egg + sugar"),
    ("nog", "Nog", "Spirit + egg + dairy"),
    ("tiki", "Tiki", "Complex, often multi-rum, tropical"),
    ("rickey", "Rickey", "Spirit + citrus + soda (no sugar)"),
    ("toddy", "Toddy", "Spirit + hot water + sweet"),
    ("sling", "Sling", "Spirit + citrus + sweet + soda + liqueur"),
    ("frozen", "Frozen", "Blended with ice"),
    ("duo_trio", "Duo/Trio", "Spirit + liqueur (optionally + cream)"),
    ("scaffa", "Scaffa", "Room temp spirit + liqueur + bitters"),
    ("other", "Other", "Catch-all for oddballs"),
]

GLASSWARE = [
    ("coupe", "Coupe", "stemmed"),
    ("nick_and_nora", "Nick & Nora", "stemmed"),
    ("martini", "Martini Glass", "stemmed"),
    ("flute", "Flute", "stemmed"),
    ("saucer", "Champagne Saucer", "stemmed"),
    ("rocks", "Rocks Glass", "short"),
    ("double_rocks", "Double Rocks", "short"),
    ("julep_cup", "Julep Cup", "short"),
    ("highball", "Highball", "tall"),
    ("collins", "Collins Glass", "tall"),
    ("copper_mug", "Copper Mug", "tall"),
    ("pilsner", "Pilsner", "tall"),
    ("tiki_mug", "Tiki Mug", "specialty"),
    ("hurricane", "Hurricane", "specialty"),
    ("goblet", "Goblet/Copa", "specialty"),
    ("poco_grande", "Poco Grande", "specialty"),
    ("margarita", "Margarita Glass", "specialty"),
    ("snifter", "Snifter", "specialty"),
    ("wine_glass", "Wine Glass", "specialty"),
    ("irish_coffee", "Irish Coffee Glass", "specialty"),
    ("fizz_glass", "Fizz Glass", "specialty"),
    ("punch_cup", "Punch Cup", "specialty"),
    ("glencairn", "Glencairn", "specialty"),
    ("shot_glass", "Shot Glass", "specialty"),
]

SERVING_STYLES = [
    ("up", "Up", "Chilled, strained, no ice in glass"),
    ("rocks", "Rocks", "Over ice cubes"),
    ("large_cube", "Large Cube", "Over a single large ice cube"),
    ("long", "Long", "Tall glass, topped with mixer, lots of ice"),
    ("crushed_ice", "Crushed Ice", "Packed crushed/pebble ice"),
    ("frozen", "Frozen", "Blended with ice"),
    ("neat", "Neat", "Room temperature, no ice"),
    ("hot", "Hot", "Heated, served warm"),
]

METHODS = [
    ("shaken", "Shaken", "With ice in shaker, strained"),
    ("stirred", "Stirred", "With ice in mixing glass, strained"),
    ("built", "Built", "Made directly in serving glass"),
    ("thrown", "Thrown", "Poured between vessels (Cuban style)"),
    ("swizzled", "Swizzled", "Spun with swizzle stick in crushed ice"),
    ("blended", "Blended", "In a blender with ice"),
    ("dry_shake", "Dry Shake", "Shaken without ice first (for egg drinks)"),
    ("whip_shake", "Whip Shake", "Quick shake with just a little crushed ice"),
]

SPIRITS = [
    ("gin", "Gin"),
    ("vodka", "Vodka"),
    ("rum_light", "Rum Light"),
    ("rum_dark", "Rum Dark"),
    ("rum_aged", "Rum Aged"),
    ("rum_overproof", "Rum Overproof"),
    ("bourbon", "Bourbon"),
    ("rye", "Rye"),
    ("scotch", "Scotch"),
    ("irish_whiskey", "Irish Whiskey"),
    ("japanese_whisky", "Japanese Whisky"),
    ("tequila", "Tequila"),
    ("mezcal", "Mezcal"),
    ("cognac", "Cognac"),
    ("armagnac", "Armagnac"),
    ("pisco", "Pisco"),
    ("calvados", "Calvados"),
    ("brandy_other", "Brandy Other"),
    ("liqueur", "Liqueur"),
    ("aperitif", "Aperitif"),
    ("amaro", "Amaro"),
    ("vermouth", "Vermouth"),
    ("sherry", "Sherry"),
    ("port", "Port"),
    ("other", "Other"),
    ("non_alcoholic", "Non Alcoholic"),
]


def upgrade() -> None:
    connection = op.get_bind()

    # Seed category_templates
    for i, (value, label, description) in enumerate(TEMPLATES):
        connection.execute(sa.text("""
            INSERT INTO category_templates (id, value, label, description, sort_order, is_active)
            VALUES (:id, :value, :label, :description, :sort_order, 1)
        """), {
            "id": str(uuid.uuid4()),
            "value": value,
            "label": label,
            "description": description,
            "sort_order": i,
        })

    # Seed category_glassware
    for i, (value, label, category) in enumerate(GLASSWARE):
        connection.execute(sa.text("""
            INSERT INTO category_glassware (id, value, label, category, sort_order, is_active)
            VALUES (:id, :value, :label, :category, :sort_order, 1)
        """), {
            "id": str(uuid.uuid4()),
            "value": value,
            "label": label,
            "category": category,
            "sort_order": i,
        })

    # Seed category_serving_styles
    for i, (value, label, description) in enumerate(SERVING_STYLES):
        connection.execute(sa.text("""
            INSERT INTO category_serving_styles (id, value, label, description, sort_order, is_active)
            VALUES (:id, :value, :label, :description, :sort_order, 1)
        """), {
            "id": str(uuid.uuid4()),
            "value": value,
            "label": label,
            "description": description,
            "sort_order": i,
        })

    # Seed category_methods
    for i, (value, label, description) in enumerate(METHODS):
        connection.execute(sa.text("""
            INSERT INTO category_methods (id, value, label, description, sort_order, is_active)
            VALUES (:id, :value, :label, :description, :sort_order, 1)
        """), {
            "id": str(uuid.uuid4()),
            "value": value,
            "label": label,
            "description": description,
            "sort_order": i,
        })

    # Seed category_spirits
    for i, (value, label) in enumerate(SPIRITS):
        connection.execute(sa.text("""
            INSERT INTO category_spirits (id, value, label, sort_order, is_active)
            VALUES (:id, :value, :label, :sort_order, 1)
        """), {
            "id": str(uuid.uuid4()),
            "value": value,
            "label": label,
            "sort_order": i,
        })


def downgrade() -> None:
    connection = op.get_bind()
    # Truncate all seed data (delete all rows)
    connection.execute(sa.text("DELETE FROM category_templates"))
    connection.execute(sa.text("DELETE FROM category_glassware"))
    connection.execute(sa.text("DELETE FROM category_serving_styles"))
    connection.execute(sa.text("DELETE FROM category_methods"))
    connection.execute(sa.text("DELETE FROM category_spirits"))
