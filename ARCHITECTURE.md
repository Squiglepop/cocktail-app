# Cocktail Recipe Extractor - Architecture

## Overview

An application that extracts cocktail recipes from screenshots using AI vision, stores them in a database, and provides a browsable frontend with filtering by template/family, spirit, serving style, and glassware.

## Data Model

### Enums/Categories

#### Cocktail Templates (Families)

| Template | Structure | Classic Examples |
|----------|-----------|------------------|
| Sour | Spirit + citrus + sweet | Whiskey Sour, Daiquiri, Margarita, Sidecar |
| Old Fashioned | Spirit + sugar + bitters | Old Fashioned, Sazerac |
| Martini | Spirit + vermouth | Martini, Manhattan, Martinez |
| Negroni | Spirit + bitter liqueur + vermouth | Negroni, Boulevardier |
| Highball | Spirit + lengthener | G&T, Whiskey & Soda |
| Collins | Sour + soda (on ice) | Tom Collins |
| Fizz | Sour + soda (no ice in glass) | Gin Fizz, Ramos |
| Spritz | Aperitif + sparkling wine + soda | Aperol Spritz, Hugo |
| Buck/Mule | Spirit + ginger beer + citrus | Moscow Mule, Dark 'n' Stormy |
| Julep | Spirit + sugar + mint (crushed ice) | Mint Julep |
| Smash | Julep + citrus | Whiskey Smash |
| Swizzle | Spirit + citrus + sweet + bitters (crushed ice, swizzled) | Queen's Park Swizzle |
| Cobbler | Wine/spirit + sugar + fruit (crushed ice) | Sherry Cobbler |
| Punch | Spirit + citrus + sweet + tea/water + spice | Planter's Punch |
| Clarified Punch | Milk-clarified punch | Milk Punch |
| Flip | Spirit + whole egg + sugar | Brandy Flip |
| Nog | Spirit + egg + dairy | Eggnog |
| Tiki | Complex, often multi-rum, tropical | Zombie, Mai Tai, Jungle Bird |
| Rickey | Spirit + citrus + soda (no sugar) | Gin Rickey |
| Toddy | Spirit + hot water + sweet | Hot Toddy |
| Sling | Spirit + citrus + sweet + soda + liqueur | Singapore Sling |
| Frozen | Blended with ice | Frozen Margarita, Piña Colada |
| Duo/Trio | Spirit + liqueur (optionally + cream) | Espresso Martini, Rusty Nail |
| Scaffa | Room temp spirit + liqueur + bitters | Classic Scaffa |
| Other | Catch-all for oddballs | — |

#### Glassware

**Stemmed (for drinks served "up"):**
- Coupe
- Nick & Nora
- Martini/Cocktail glass
- Flute
- Saucer/Champagne coupe

**Short (for rocks/built drinks):**
- Rocks / Old Fashioned
- Double Rocks / DOF
- Julep Cup (metal)

**Tall (for long drinks):**
- Highball
- Collins
- Copper Mug
- Pilsner

**Specialty:**
- Tiki Mug
- Hurricane
- Goblet / Copa
- Poco Grande
- Margarita glass
- Snifter
- Wine glass
- Irish Coffee glass
- Fizz glass
- Punch cup
- Glencairn
- Shot glass

#### Serving Styles

| Style | Description |
|-------|-------------|
| Up | Chilled, strained, no ice in glass |
| Rocks | Over ice cubes |
| Large Cube | Over a single large ice cube |
| Long | Tall glass, topped with mixer, lots of ice |
| Crushed Ice | Packed crushed/pebble ice |
| Frozen | Blended with ice |
| Neat | Room temperature, no ice |
| Hot | Heated, served warm |

#### Methods

| Method | Description |
|--------|-------------|
| Shaken | With ice in shaker, strained |
| Stirred | With ice in mixing glass, strained |
| Built | Made directly in serving glass |
| Thrown | Poured between vessels (Cuban style) |
| Swizzled | Spun with swizzle stick in crushed ice |
| Blended | In a blender with ice |
| Dry Shake | Shaken without ice first (for egg drinks) |
| Whip Shake | Quick shake with just a little crushed ice |

#### Spirit Categories

- Gin
- Vodka
- Rum (Light, Dark, Aged, Overproof)
- Whiskey (Bourbon, Rye, Scotch, Irish, Japanese)
- Tequila
- Mezcal
- Brandy (Cognac, Armagnac, Pisco, Calvados)
- Liqueur
- Aperitif/Amaro
- Wine/Fortified Wine (Vermouth, Sherry, Port)
- Other

## Tech Stack

- **Frontend**: Next.js 14+ (App Router)
- **Backend**: Python FastAPI
- **Database**: PostgreSQL
- **AI**: Claude Vision API (claude-sonnet-4-5-20250929)
- **Storage**: Local filesystem (S3-compatible for production)
- **Queue**: Redis + Celery (for async extraction)

## Directory Structure

```
cocktail-app/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── recipe.py
│   │   │   └── enums.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── recipes.py
│   │   │   ├── upload.py
│   │   │   └── categories.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── extractor.py
│   │   │   └── database.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── recipe.py
│   ├── alembic/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Recipes
- `GET /api/recipes` - List recipes with filters
- `GET /api/recipes/{id}` - Get single recipe
- `POST /api/recipes` - Create recipe manually
- `PUT /api/recipes/{id}` - Update recipe
- `DELETE /api/recipes/{id}` - Delete recipe

### Upload & Extraction
- `POST /api/upload` - Upload image, trigger extraction
- `GET /api/extraction/{job_id}` - Check extraction status

### Categories
- `GET /api/categories/templates` - List all templates
- `GET /api/categories/glassware` - List all glassware
- `GET /api/categories/serving-styles` - List serving styles
- `GET /api/categories/methods` - List methods
- `GET /api/categories/spirits` - List spirit categories

## Future: Social Media Integration

For Instagram/Facebook integration:
1. Use official APIs with OAuth
2. Download video/story content
3. Extract key frames using FFmpeg
4. Process multiple frames to reconstruct recipe
5. Handle OCR for text overlays
