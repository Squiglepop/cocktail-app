# Cocktail Recipe Library - Project Overview

**Generated:** 2025-12-30 | **Scan Level:** Deep | **For:** Novice Developers

---

## What Does This App Actually Do?

The Cocktail Recipe Library is a web application that:

1. **Extracts recipes from screenshots** - Upload a photo of a cocktail recipe (from a book, website, or menu), and AI reads it and extracts all the details
2. **Organizes recipes** - Categorizes drinks by type (Sour, Old Fashioned, Tiki, etc.), spirit, glassware, and more
3. **Searchable library** - Filter and browse your collection
4. **Works offline** - Save favorites for when you don't have internet

---

## The Big Picture: How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER'S BROWSER                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              FRONTEND (Next.js - TypeScript)                 │   │
│  │                                                              │   │
│  │   [Upload Page] ──┐                                          │   │
│  │                   │   ┌────────────────┐                     │   │
│  │   [Home Page]─────┼──▶│   API Client   │◀───▶ IndexedDB      │   │
│  │                   │   │  (lib/api.ts)  │     (offline cache) │   │
│  │   [Recipe Page] ──┘   └───────┬────────┘                     │   │
│  └───────────────────────────────┼──────────────────────────────┘   │
└──────────────────────────────────┼──────────────────────────────────┘
                                   │ HTTP/REST
                                   ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI - Python)                       │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                        API Routers                              │ │
│  │   /api/recipes  ─────▶ Recipe CRUD                              │ │
│  │   /api/upload   ─────▶ Image Upload + Extraction                │ │
│  │   /api/categories ───▶ Enum Values (templates, spirits, etc.)   │ │
│  │   /api/auth     ─────▶ User Login/Register                      │ │
│  │   /api/collections ──▶ Recipe Playlists                         │ │
│  └──────────────────────────┬──────────────────────────────────────┘ │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────────────────┐ │
│  │                       Services Layer                            │ │
│  │   RecipeExtractor ────▶ Claude Vision API ────▶ AI reads image  │ │
│  │   Database Service ───▶ SQLAlchemy ORM ───────▶ CRUD operations │ │
│  │   Image Storage ──────▶ Filesystem ───────────▶ Save uploads    │ │
│  └──────────────────────────┬──────────────────────────────────────┘ │
│                             │                                        │
│  ┌──────────────────────────▼──────────────────────────────────────┐ │
│  │                       SQLite / PostgreSQL                       │ │
│  │   recipes, ingredients, recipe_ingredients, users, etc.        │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## What Happens When You Upload a Photo?

Let's trace through the most important flow in the app:

### Step 1: User Uploads Image
**File:** `frontend/app/upload/page.tsx`
- User drags/drops or selects an image file
- Frontend validates file type (jpg, png, gif, webp)

### Step 2: Send to Backend
**File:** `frontend/lib/api.ts` → `uploadAndExtract()`
- Creates FormData with the image
- POSTs to `/api/upload/extract-immediate`

### Step 3: Backend Receives Upload
**File:** `backend/app/routers/upload.py` → `upload_and_extract()`
- Saves image to `uploads/` folder with unique filename
- Creates an ExtractionJob record in database

### Step 4: AI Extracts Recipe
**File:** `backend/app/services/extractor.py` → `RecipeExtractor`
- Loads image, converts to base64
- Sends to Claude Vision API with extraction prompt
- Claude reads the image and returns JSON with:
  - Recipe name
  - Ingredients with amounts
  - Instructions
  - Template (Sour, Martini, etc.)
  - Glassware, method, garnish

### Step 5: Save to Database
**File:** `backend/app/routers/upload.py` → creates Recipe model
- Maps extracted data to database models
- Creates Recipe, Ingredient, and RecipeIngredient records
- Returns the complete recipe to frontend

### Step 6: Show to User
**File:** `frontend/app/page.tsx`
- Recipe appears in the grid
- User can click to view, edit, or delete

---

## Repository Structure

```
cocktail-app/
├── backend/                 # Python FastAPI server
│   ├── app/
│   │   ├── main.py          # App entry point, CORS, routers
│   │   ├── config.py        # Environment variables
│   │   ├── models/          # SQLAlchemy database models
│   │   │   ├── recipe.py    # Recipe, Ingredient, RecipeIngredient
│   │   │   └── enums.py     # All the enum types
│   │   ├── routers/         # API endpoint handlers
│   │   │   ├── recipes.py   # CRUD for recipes
│   │   │   ├── upload.py    # Image upload + extraction
│   │   │   └── categories.py # Enum value endpoints
│   │   ├── services/        # Business logic
│   │   │   ├── extractor.py # Claude Vision integration
│   │   │   └── database.py  # DB session management
│   │   └── schemas/         # Pydantic request/response models
│   ├── alembic/             # Database migrations
│   ├── tests/               # pytest tests
│   └── requirements.txt     # Python dependencies
│
├── frontend/                # Next.js React app
│   ├── app/                 # Next.js App Router pages
│   │   ├── layout.tsx       # Root layout with providers
│   │   ├── page.tsx         # Home page with recipe grid
│   │   ├── upload/          # Image upload page
│   │   └── recipes/[id]/    # Recipe detail pages
│   ├── components/          # React components
│   │   ├── Header.tsx       # Navigation header
│   │   └── recipes/         # Recipe-related components
│   ├── lib/                 # Utilities
│   │   ├── api.ts           # Backend API client
│   │   ├── auth-context.tsx # Authentication state
│   │   └── offline-context.tsx # Offline/PWA support
│   └── package.json
│
├── ARCHITECTURE.md          # Domain model documentation
├── DEPLOY.md                # Railway deployment guide
└── docker-compose.yml       # Local development with Docker
```

---

## Tech Stack Explained

### Backend (Python)

| Technology | What It Does | Why It's Used |
|------------|--------------|---------------|
| **FastAPI** | Web framework for building APIs | Fast, modern, automatic API docs |
| **SQLAlchemy** | Database toolkit (ORM) | Maps Python objects to database tables |
| **Pydantic** | Data validation | Validates API requests/responses |
| **Anthropic SDK** | Claude AI client | Calls Claude Vision API |
| **Alembic** | Database migrations | Manages schema changes |

### Frontend (TypeScript)

| Technology | What It Does | Why It's Used |
|------------|--------------|---------------|
| **Next.js 14** | React framework | App Router, server components |
| **React** | UI library | Component-based UI |
| **Tailwind CSS** | Styling | Utility-first CSS |
| **React Query** | Server state management | Caching, refetching, mutations |
| **idb** | IndexedDB wrapper | Offline storage |

---

## Key Concepts for Beginners

### What's an API?
The backend exposes "endpoints" (URLs) that the frontend can call. For example:
- `GET /api/recipes` - Get list of recipes
- `POST /api/upload` - Upload an image
- `DELETE /api/recipes/123` - Delete a specific recipe

### What's an ORM?
SQLAlchemy lets you work with database tables using Python classes instead of writing SQL. The `Recipe` class maps to the `recipes` table.

### What's a Context in React?
Contexts share state across components without passing props. This app uses:
- `AuthContext` - Current user and token
- `FavouritesContext` - Favorited recipe IDs
- `OfflineContext` - Online/offline status and cached data

### What's a Router?
In FastAPI, routers group related endpoints. Each file in `routers/` handles a different part of the API.

---

## Next Steps

- **[Source Tree Analysis](./source-tree-analysis.md)** - Detailed file breakdown
- **[Backend Architecture](./architecture-backend.md)** - How the Python code works
- **[Frontend Architecture](./architecture-frontend.md)** - How the React code works
- **[API Contracts](./api-contracts.md)** - All API endpoints
- **[Data Models](./data-models.md)** - Database schema
- **[Development Guide](./development-guide.md)** - How to run locally
