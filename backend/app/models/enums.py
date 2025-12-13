"""
Enumeration types for cocktail categorization.
"""
from enum import Enum


class CocktailTemplate(str, Enum):
    """Cocktail family/template classification."""
    SOUR = "sour"
    OLD_FASHIONED = "old_fashioned"
    MARTINI = "martini"
    NEGRONI = "negroni"
    HIGHBALL = "highball"
    COLLINS = "collins"
    FIZZ = "fizz"
    SPRITZ = "spritz"
    BUCK_MULE = "buck_mule"
    JULEP = "julep"
    SMASH = "smash"
    SWIZZLE = "swizzle"
    COBBLER = "cobbler"
    PUNCH = "punch"
    CLARIFIED_PUNCH = "clarified_punch"
    FLIP = "flip"
    NOG = "nog"
    TIKI = "tiki"
    RICKEY = "rickey"
    TODDY = "toddy"
    SLING = "sling"
    FROZEN = "frozen"
    DUO_TRIO = "duo_trio"
    SCAFFA = "scaffa"
    OTHER = "other"


class GlasswareCategory(str, Enum):
    """Glassware category groupings."""
    STEMMED = "stemmed"
    SHORT = "short"
    TALL = "tall"
    SPECIALTY = "specialty"


class Glassware(str, Enum):
    """Specific glassware types."""
    # Stemmed
    COUPE = "coupe"
    NICK_AND_NORA = "nick_and_nora"
    MARTINI = "martini"
    FLUTE = "flute"
    SAUCER = "saucer"
    # Short
    ROCKS = "rocks"
    DOUBLE_ROCKS = "double_rocks"
    JULEP_CUP = "julep_cup"
    # Tall
    HIGHBALL = "highball"
    COLLINS = "collins"
    COPPER_MUG = "copper_mug"
    PILSNER = "pilsner"
    # Specialty
    TIKI_MUG = "tiki_mug"
    HURRICANE = "hurricane"
    GOBLET = "goblet"
    POCO_GRANDE = "poco_grande"
    MARGARITA = "margarita"
    SNIFTER = "snifter"
    WINE_GLASS = "wine_glass"
    IRISH_COFFEE = "irish_coffee"
    FIZZ_GLASS = "fizz_glass"
    PUNCH_CUP = "punch_cup"
    GLENCAIRN = "glencairn"
    SHOT_GLASS = "shot_glass"


# Mapping of glassware to their categories
GLASSWARE_CATEGORIES = {
    Glassware.COUPE: GlasswareCategory.STEMMED,
    Glassware.NICK_AND_NORA: GlasswareCategory.STEMMED,
    Glassware.MARTINI: GlasswareCategory.STEMMED,
    Glassware.FLUTE: GlasswareCategory.STEMMED,
    Glassware.SAUCER: GlasswareCategory.STEMMED,
    Glassware.ROCKS: GlasswareCategory.SHORT,
    Glassware.DOUBLE_ROCKS: GlasswareCategory.SHORT,
    Glassware.JULEP_CUP: GlasswareCategory.SHORT,
    Glassware.HIGHBALL: GlasswareCategory.TALL,
    Glassware.COLLINS: GlasswareCategory.TALL,
    Glassware.COPPER_MUG: GlasswareCategory.TALL,
    Glassware.PILSNER: GlasswareCategory.TALL,
    Glassware.TIKI_MUG: GlasswareCategory.SPECIALTY,
    Glassware.HURRICANE: GlasswareCategory.SPECIALTY,
    Glassware.GOBLET: GlasswareCategory.SPECIALTY,
    Glassware.POCO_GRANDE: GlasswareCategory.SPECIALTY,
    Glassware.MARGARITA: GlasswareCategory.SPECIALTY,
    Glassware.SNIFTER: GlasswareCategory.SPECIALTY,
    Glassware.WINE_GLASS: GlasswareCategory.SPECIALTY,
    Glassware.IRISH_COFFEE: GlasswareCategory.SPECIALTY,
    Glassware.FIZZ_GLASS: GlasswareCategory.SPECIALTY,
    Glassware.PUNCH_CUP: GlasswareCategory.SPECIALTY,
    Glassware.GLENCAIRN: GlasswareCategory.SPECIALTY,
    Glassware.SHOT_GLASS: GlasswareCategory.SPECIALTY,
}


class ServingStyle(str, Enum):
    """How the drink is served."""
    UP = "up"
    ROCKS = "rocks"
    LARGE_CUBE = "large_cube"
    LONG = "long"
    CRUSHED_ICE = "crushed_ice"
    FROZEN = "frozen"
    NEAT = "neat"
    HOT = "hot"


class Method(str, Enum):
    """Preparation method."""
    SHAKEN = "shaken"
    STIRRED = "stirred"
    BUILT = "built"
    THROWN = "thrown"
    SWIZZLED = "swizzled"
    BLENDED = "blended"
    DRY_SHAKE = "dry_shake"
    WHIP_SHAKE = "whip_shake"


class SpiritCategory(str, Enum):
    """Main spirit categories."""
    GIN = "gin"
    VODKA = "vodka"
    RUM_LIGHT = "rum_light"
    RUM_DARK = "rum_dark"
    RUM_AGED = "rum_aged"
    RUM_OVERPROOF = "rum_overproof"
    BOURBON = "bourbon"
    RYE = "rye"
    SCOTCH = "scotch"
    IRISH_WHISKEY = "irish_whiskey"
    JAPANESE_WHISKY = "japanese_whisky"
    TEQUILA = "tequila"
    MEZCAL = "mezcal"
    COGNAC = "cognac"
    ARMAGNAC = "armagnac"
    PISCO = "pisco"
    CALVADOS = "calvados"
    BRANDY_OTHER = "brandy_other"
    LIQUEUR = "liqueur"
    APERITIF = "aperitif"
    AMARO = "amaro"
    VERMOUTH = "vermouth"
    SHERRY = "sherry"
    PORT = "port"
    OTHER = "other"
    NON_ALCOHOLIC = "non_alcoholic"


class IngredientType(str, Enum):
    """Types of ingredients."""
    SPIRIT = "spirit"
    LIQUEUR = "liqueur"
    WINE_FORTIFIED = "wine_fortified"
    BITTER = "bitter"
    SYRUP = "syrup"
    JUICE = "juice"
    MIXER = "mixer"
    DAIRY = "dairy"
    EGG = "egg"
    GARNISH = "garnish"
    OTHER = "other"


class Unit(str, Enum):
    """Measurement units."""
    OZ = "oz"
    ML = "ml"
    CL = "cl"
    DASH = "dash"
    DROP = "drop"
    BARSPOON = "barspoon"
    TSP = "tsp"
    TBSP = "tbsp"
    RINSE = "rinse"
    FLOAT = "float"
    TOP = "top"
    WHOLE = "whole"
    HALF = "half"
    WEDGE = "wedge"
    SLICE = "slice"
    PEEL = "peel"
    SPRIG = "sprig"
    LEAF = "leaf"


# Human-readable display names
TEMPLATE_DISPLAY_NAMES = {
    CocktailTemplate.SOUR: "Sour",
    CocktailTemplate.OLD_FASHIONED: "Old Fashioned",
    CocktailTemplate.MARTINI: "Martini",
    CocktailTemplate.NEGRONI: "Negroni",
    CocktailTemplate.HIGHBALL: "Highball",
    CocktailTemplate.COLLINS: "Collins",
    CocktailTemplate.FIZZ: "Fizz",
    CocktailTemplate.SPRITZ: "Spritz",
    CocktailTemplate.BUCK_MULE: "Buck/Mule",
    CocktailTemplate.JULEP: "Julep",
    CocktailTemplate.SMASH: "Smash",
    CocktailTemplate.SWIZZLE: "Swizzle",
    CocktailTemplate.COBBLER: "Cobbler",
    CocktailTemplate.PUNCH: "Punch",
    CocktailTemplate.CLARIFIED_PUNCH: "Clarified Punch",
    CocktailTemplate.FLIP: "Flip",
    CocktailTemplate.NOG: "Nog",
    CocktailTemplate.TIKI: "Tiki",
    CocktailTemplate.RICKEY: "Rickey",
    CocktailTemplate.TODDY: "Toddy",
    CocktailTemplate.SLING: "Sling",
    CocktailTemplate.FROZEN: "Frozen",
    CocktailTemplate.DUO_TRIO: "Duo/Trio",
    CocktailTemplate.SCAFFA: "Scaffa",
    CocktailTemplate.OTHER: "Other",
}

TEMPLATE_DESCRIPTIONS = {
    CocktailTemplate.SOUR: "Spirit + citrus + sweet",
    CocktailTemplate.OLD_FASHIONED: "Spirit + sugar + bitters",
    CocktailTemplate.MARTINI: "Spirit + vermouth",
    CocktailTemplate.NEGRONI: "Spirit + bitter liqueur + vermouth",
    CocktailTemplate.HIGHBALL: "Spirit + lengthener",
    CocktailTemplate.COLLINS: "Sour + soda (on ice)",
    CocktailTemplate.FIZZ: "Sour + soda (no ice in glass)",
    CocktailTemplate.SPRITZ: "Aperitif + sparkling wine + soda",
    CocktailTemplate.BUCK_MULE: "Spirit + ginger beer + citrus",
    CocktailTemplate.JULEP: "Spirit + sugar + mint (crushed ice)",
    CocktailTemplate.SMASH: "Julep + citrus",
    CocktailTemplate.SWIZZLE: "Spirit + citrus + sweet + bitters (crushed ice, swizzled)",
    CocktailTemplate.COBBLER: "Wine/spirit + sugar + fruit (crushed ice)",
    CocktailTemplate.PUNCH: "Spirit + citrus + sweet + tea/water + spice",
    CocktailTemplate.CLARIFIED_PUNCH: "Milk-clarified punch",
    CocktailTemplate.FLIP: "Spirit + whole egg + sugar",
    CocktailTemplate.NOG: "Spirit + egg + dairy",
    CocktailTemplate.TIKI: "Complex, often multi-rum, tropical",
    CocktailTemplate.RICKEY: "Spirit + citrus + soda (no sugar)",
    CocktailTemplate.TODDY: "Spirit + hot water + sweet",
    CocktailTemplate.SLING: "Spirit + citrus + sweet + soda + liqueur",
    CocktailTemplate.FROZEN: "Blended with ice",
    CocktailTemplate.DUO_TRIO: "Spirit + liqueur (optionally + cream)",
    CocktailTemplate.SCAFFA: "Room temp spirit + liqueur + bitters",
    CocktailTemplate.OTHER: "Catch-all for oddballs",
}

GLASSWARE_DISPLAY_NAMES = {
    Glassware.COUPE: "Coupe",
    Glassware.NICK_AND_NORA: "Nick & Nora",
    Glassware.MARTINI: "Martini Glass",
    Glassware.FLUTE: "Flute",
    Glassware.SAUCER: "Champagne Saucer",
    Glassware.ROCKS: "Rocks Glass",
    Glassware.DOUBLE_ROCKS: "Double Rocks",
    Glassware.JULEP_CUP: "Julep Cup",
    Glassware.HIGHBALL: "Highball",
    Glassware.COLLINS: "Collins Glass",
    Glassware.COPPER_MUG: "Copper Mug",
    Glassware.PILSNER: "Pilsner",
    Glassware.TIKI_MUG: "Tiki Mug",
    Glassware.HURRICANE: "Hurricane",
    Glassware.GOBLET: "Goblet/Copa",
    Glassware.POCO_GRANDE: "Poco Grande",
    Glassware.MARGARITA: "Margarita Glass",
    Glassware.SNIFTER: "Snifter",
    Glassware.WINE_GLASS: "Wine Glass",
    Glassware.IRISH_COFFEE: "Irish Coffee Glass",
    Glassware.FIZZ_GLASS: "Fizz Glass",
    Glassware.PUNCH_CUP: "Punch Cup",
    Glassware.GLENCAIRN: "Glencairn",
    Glassware.SHOT_GLASS: "Shot Glass",
}

SERVING_STYLE_DESCRIPTIONS = {
    ServingStyle.UP: "Chilled, strained, no ice in glass",
    ServingStyle.ROCKS: "Over ice cubes",
    ServingStyle.LARGE_CUBE: "Over a single large ice cube",
    ServingStyle.LONG: "Tall glass, topped with mixer, lots of ice",
    ServingStyle.CRUSHED_ICE: "Packed crushed/pebble ice",
    ServingStyle.FROZEN: "Blended with ice",
    ServingStyle.NEAT: "Room temperature, no ice",
    ServingStyle.HOT: "Heated, served warm",
}

METHOD_DESCRIPTIONS = {
    Method.SHAKEN: "With ice in shaker, strained",
    Method.STIRRED: "With ice in mixing glass, strained",
    Method.BUILT: "Made directly in serving glass",
    Method.THROWN: "Poured between vessels (Cuban style)",
    Method.SWIZZLED: "Spun with swizzle stick in crushed ice",
    Method.BLENDED: "In a blender with ice",
    Method.DRY_SHAKE: "Shaken without ice first (for egg drinks)",
    Method.WHIP_SHAKE: "Quick shake with just a little crushed ice",
}


class Visibility(str, Enum):
    """Recipe visibility settings."""
    PUBLIC = "public"
    PRIVATE = "private"
    GROUP = "group"  # Placeholder for future group sharing feature
