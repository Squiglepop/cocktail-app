# Data Models

Database schema and entity relationships.

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────────┐       ┌─────────────────┐
│     users       │       │       recipes           │       │   ingredients   │
├─────────────────┤       ├─────────────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)                 │    ┌──│ id (PK)         │
│ email           │  │    │ name                    │    │  │ name            │
│ password_hash   │  │    │ description             │    │  │ type            │
│ display_name    │  │    │ instructions            │    │  │ spirit_category │
│ created_at      │  │    │ template                │    │  │ description     │
└─────────────────┘  │    │ main_spirit             │    │  └─────────────────┘
                     │    │ glassware               │    │
                     │    │ serving_style           │    │
                     │    │ method                  │    │
                     │    │ garnish                 │    │
                     │    │ notes                   │    │
                     │    │ source_image_path       │    │
                     │    │ user_id (FK)────────────┼────┤
                     │    │ visibility              │    │
                     │    │ created_at              │    │
                     │    │ updated_at              │    │
                     │    └────────────┬────────────┘    │
                     │                 │                 │
                     │                 │ 1:many          │
                     │                 ▼                 │
                     │    ┌─────────────────────────┐    │
                     │    │   recipe_ingredients    │    │
                     │    ├─────────────────────────┤    │
                     │    │ id (PK)                 │    │
                     │    │ recipe_id (FK)──────────┘    │
                     │    │ ingredient_id (FK)───────────┘
                     │    │ amount                  │
                     │    │ unit                    │
                     │    │ notes                   │
                     │    │ optional                │
                     │    │ order                   │
                     │    └─────────────────────────┘
                     │
                     │    ┌─────────────────────────┐
                     │    │     user_ratings        │
                     │    ├─────────────────────────┤
                     └───▶│ id (PK)                 │
                          │ user_id (FK)            │
                          │ recipe_id (FK)          │
                          │ rating (1-5)            │
                          │ created_at              │
                          └─────────────────────────┘
```

---

## Table Definitions

### recipes

The main table storing cocktail recipes.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | UUID primary key |
| name | VARCHAR(255) | No | Recipe name (indexed) |
| description | TEXT | Yes | Brief description |
| instructions | TEXT | Yes | Preparation steps |
| template | VARCHAR(50) | Yes | Cocktail family (sour, martini, etc.) |
| main_spirit | VARCHAR(50) | Yes | Primary spirit (gin, vodka, etc.) |
| glassware | VARCHAR(50) | Yes | Glass type (coupe, rocks, etc.) |
| serving_style | VARCHAR(50) | Yes | How served (up, rocks, etc.) |
| method | VARCHAR(50) | Yes | Prep method (shaken, stirred, etc.) |
| garnish | VARCHAR(255) | Yes | Garnish description |
| notes | TEXT | Yes | Additional notes |
| source_image_path | VARCHAR(512) | Yes | Path to uploaded image |
| source_image_mime | VARCHAR(50) | Yes | Image MIME type |
| source_type | VARCHAR(50) | Yes | "screenshot" or "manual" |
| image_content_hash | VARCHAR(64) | Yes | SHA256 for duplicate detection |
| image_perceptual_hash | VARCHAR(16) | Yes | pHash for similar images |
| recipe_fingerprint | VARCHAR(32) | Yes | Hash of name + ingredients |
| user_id | VARCHAR(36) | Yes | Owner (FK to users) |
| visibility | VARCHAR(20) | No | "public", "private", "group" |
| created_at | DATETIME | No | Creation timestamp |
| updated_at | DATETIME | No | Last update timestamp |

### ingredients

Master list of ingredients.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | UUID primary key |
| name | VARCHAR(255) | No | Ingredient name (unique, indexed) |
| type | VARCHAR(50) | No | Type (spirit, juice, syrup, etc.) |
| spirit_category | VARCHAR(50) | Yes | Spirit subcategory (gin, bourbon, etc.) |
| description | TEXT | Yes | Description |
| common_brands | TEXT | Yes | Popular brand examples |

### recipe_ingredients

Junction table linking recipes to ingredients with amounts.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | UUID primary key |
| recipe_id | VARCHAR(36) | No | FK to recipes (CASCADE delete) |
| ingredient_id | VARCHAR(36) | No | FK to ingredients |
| amount | FLOAT | Yes | Quantity (2.0, 0.5, etc.) |
| unit | VARCHAR(20) | Yes | Unit (oz, ml, dash, etc.) |
| notes | VARCHAR(255) | Yes | Notes ("muddled", "fresh", etc.) |
| optional | BOOLEAN | No | Is ingredient optional? |
| order | INTEGER | No | Display order in recipe |

### users

User accounts for authentication.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | UUID primary key |
| email | VARCHAR(255) | No | Email address (unique) |
| password_hash | VARCHAR(255) | No | bcrypt hashed password |
| display_name | VARCHAR(100) | Yes | Display name |
| created_at | DATETIME | No | Registration timestamp |

### user_ratings

Personal ratings for recipes (per-user).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | UUID primary key |
| user_id | VARCHAR(36) | No | FK to users |
| recipe_id | VARCHAR(36) | No | FK to recipes |
| rating | INTEGER | No | Rating 1-5 |
| created_at | DATETIME | No | Rating timestamp |

Unique constraint: (user_id, recipe_id)

### collections

Recipe playlists/collections.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | UUID primary key |
| name | VARCHAR(255) | No | Collection name |
| description | TEXT | Yes | Description |
| user_id | VARCHAR(36) | No | Owner (FK to users) |
| is_public | BOOLEAN | No | Publicly viewable? |
| created_at | DATETIME | No | Creation timestamp |
| updated_at | DATETIME | No | Last update |

### extraction_jobs

Tracks image extraction jobs for async processing.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | VARCHAR(36) | No | UUID primary key |
| image_path | VARCHAR(512) | No | Path to uploaded image |
| status | VARCHAR(50) | No | "pending", "processing", "completed", "failed" |
| recipe_id | VARCHAR(36) | Yes | FK to created recipe |
| error_message | TEXT | Yes | Error details if failed |
| raw_extraction | TEXT | Yes | Raw Claude response JSON |
| created_at | DATETIME | No | Job creation time |
| completed_at | DATETIME | Yes | Completion time |

---

## Enum Values

### CocktailTemplate (template)
```
sour, old_fashioned, martini, negroni, highball, collins, fizz, spritz,
buck_mule, julep, smash, swizzle, cobbler, punch, clarified_punch,
flip, nog, tiki, rickey, toddy, sling, frozen, duo_trio, scaffa, other
```

### SpiritCategory (main_spirit)
```
gin, vodka, rum_light, rum_dark, rum_aged, rum_overproof, bourbon, rye,
scotch, irish_whiskey, japanese_whisky, tequila, mezcal, cognac, armagnac,
pisco, calvados, brandy_other, liqueur, aperitif, amaro, vermouth, sherry,
port, other, non_alcoholic
```

### Glassware
```
coupe, nick_and_nora, martini, flute, saucer, rocks, double_rocks,
julep_cup, highball, collins, copper_mug, pilsner, tiki_mug, hurricane,
goblet, poco_grande, margarita, snifter, wine_glass, irish_coffee,
fizz_glass, punch_cup, glencairn, shot_glass
```

### ServingStyle
```
up, rocks, large_cube, long, crushed_ice, frozen, neat, hot
```

### Method
```
shaken, stirred, built, thrown, swizzled, blended, dry_shake, whip_shake
```

### IngredientType
```
spirit, liqueur, wine_fortified, bitter, syrup, juice, mixer,
dairy, egg, garnish, other
```

### Unit
```
oz, ml, cl, dash, drop, barspoon, tsp, tbsp, rinse, float, top,
whole, half, wedge, slice, peel, sprig, leaf
```

### Visibility
```
public, private, group
```

---

## SQLAlchemy Model Example

```python
class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    template: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )

    # Relationship to ingredients (through junction table)
    ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan"
    )

    # Property to check if recipe has image
    @property
    def has_image(self) -> bool:
        return self.source_image_path is not None
```
