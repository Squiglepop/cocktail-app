# Source Tree Analysis

Annotated directory structure with explanations for each file.

---

## Backend (`cocktail-app/backend/`)

```
backend/
├── app/                          # Main application package
│   ├── __init__.py               # Makes this a Python package
│   ├── main.py                   # FastAPI app instance, startup/shutdown
│   ├── config.py                 # Loads environment variables (Settings class)
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── __init__.py           # Exports all models
│   │   ├── recipe.py             # Recipe, Ingredient, RecipeIngredient, ExtractionJob
│   │   ├── enums.py              # CocktailTemplate, Glassware, ServingStyle, etc.
│   │   ├── user.py               # User model (authentication)
│   │   ├── user_rating.py        # Personal ratings (many-to-many)
│   │   └── collection.py         # Recipe playlists
│   │
│   ├── routers/                  # API endpoint handlers (controllers)
│   │   ├── __init__.py           # Exports all routers
│   │   ├── recipes.py            # GET/POST/PUT/DELETE /api/recipes
│   │   ├── upload.py             # POST /api/upload (image extraction)
│   │   ├── categories.py         # GET /api/categories (enum values)
│   │   ├── auth.py               # POST /api/auth/register, /login
│   │   ├── collections.py        # Recipe playlist CRUD
│   │   └── admin.py              # Admin endpoints (stats, cleanup)
│   │
│   ├── services/                 # Business logic layer
│   │   ├── __init__.py           # Exports services
│   │   ├── database.py           # get_db() dependency, create_tables()
│   │   ├── extractor.py          # RecipeExtractor - Claude Vision integration
│   │   ├── auth.py               # JWT token handling, password hashing
│   │   ├── duplicates.py         # Image hash comparison for duplicate detection
│   │   ├── image_storage.py      # Save/retrieve images from filesystem
│   │   └── image_preprocessor.py # Resize images for Claude (token savings)
│   │
│   └── schemas/                  # Pydantic models for request/response
│       ├── __init__.py           # Exports schemas
│       ├── recipe.py             # RecipeCreate, RecipeUpdate, RecipeResponse
│       ├── ingredient.py         # IngredientCreate, IngredientResponse
│       ├── extraction.py         # ExtractedRecipe, ExtractedIngredient
│       └── auth.py               # LoginRequest, TokenResponse
│
├── alembic/                      # Database migration tool
│   ├── alembic.ini               # Alembic config
│   ├── env.py                    # Migration environment setup
│   └── versions/                 # Migration scripts (timestamped)
│       ├── xxx_initial.py        # Creates initial tables
│       └── xxx_add_users.py      # Adds user tables, etc.
│
├── tests/                        # pytest test suite
│   ├── conftest.py               # Test fixtures (test database, client)
│   ├── test_recipes.py           # Recipe CRUD tests
│   └── test_upload.py            # Upload endpoint tests
│
├── data/                         # Static data files
│   └── uploads/                  # Uploaded images stored here
│
├── requirements.txt              # Python dependencies
└── pyproject.toml                # Python project config
```

---

## Frontend (`cocktail-app/frontend/`)

```
frontend/
├── app/                          # Next.js App Router (pages)
│   ├── layout.tsx                # Root layout - wraps all pages with providers
│   ├── page.tsx                  # Home page (/) - recipe grid with filters
│   ├── globals.css               # Global Tailwind styles
│   │
│   ├── upload/                   # /upload route
│   │   └── page.tsx              # Image upload with drag-drop
│   │
│   ├── recipes/                  # /recipes routes
│   │   ├── new/
│   │   │   └── page.tsx          # Manual recipe creation form
│   │   └── [id]/                 # Dynamic route for recipe ID
│   │       ├── page.tsx          # Recipe detail view
│   │       └── edit/
│   │           └── page.tsx      # Edit existing recipe
│   │
│   ├── collections/              # /collections routes (playlists)
│   │   ├── page.tsx              # List of collections
│   │   ├── new/page.tsx          # Create collection
│   │   └── [id]/                 # Collection detail/edit
│   │
│   ├── login/page.tsx            # Login form
│   ├── register/page.tsx         # Registration form
│   └── profile/page.tsx          # User profile
│
├── components/                   # Reusable React components
│   ├── Header.tsx                # Navigation bar
│   ├── OfflineIndicator.tsx      # "You're offline" banner
│   ├── ServiceWorkerRegistration.tsx  # PWA service worker init
│   │
│   ├── recipes/                  # Recipe-related components
│   │   ├── RecipeGrid.tsx        # Grid of recipe cards
│   │   ├── RecipeCard.tsx        # Single recipe card
│   │   ├── RecipeForm.tsx        # Create/edit form
│   │   └── FilterSidebar.tsx     # Filter controls
│   │
│   ├── playlists/                # Collection components
│   │   └── CollectionCard.tsx
│   │
│   ├── upload/                   # Upload components
│   │   └── UploadZone.tsx        # Drag-drop area
│   │
│   └── ui/                       # Generic UI components
│       └── (buttons, modals, etc.)
│
├── lib/                          # Utilities and shared logic
│   ├── api.ts                    # Backend API client (fetch wrappers)
│   ├── auth-context.tsx          # AuthProvider - login state
│   ├── favourites-context.tsx    # Favorite recipes (local storage)
│   ├── offline-context.tsx       # Online status + cached recipes
│   ├── offline-storage.ts        # IndexedDB helpers
│   ├── query-client.ts           # React Query config
│   ├── query-provider.tsx        # React Query provider
│   └── hooks/                    # Custom React hooks
│       ├── index.ts              # Exports hooks
│       ├── use-recipes.ts        # useInfiniteRecipes, useRecipe
│       └── use-categories.ts     # useCategories
│
├── public/                       # Static assets
│   ├── manifest.json             # PWA manifest
│   ├── sw.js                     # Service worker for offline
│   └── icons/                    # App icons
│
├── tests/                        # vitest tests
│   ├── utils/                    # Test utilities
│   ├── components/               # Component tests
│   └── pages/                    # Page tests
│
├── package.json                  # Node dependencies
├── next.config.ts                # Next.js config
├── tailwind.config.ts            # Tailwind CSS config
└── tsconfig.json                 # TypeScript config
```

---

## Key Files Explained

### Backend Entry Point: `main.py`

```python
# Creates the FastAPI application
app = FastAPI(
    title="Cocktail Recipe Extractor",
    lifespan=lifespan,  # Startup/shutdown handlers
)

# Adds CORS middleware (allows frontend to call API)
app.add_middleware(CORSMiddleware, ...)

# Mounts static files (uploaded images)
app.mount("/uploads", StaticFiles(...))

# Includes all routers under /api prefix
app.include_router(recipes_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
# etc.
```

### Frontend Entry Point: `layout.tsx`

```tsx
// Wraps entire app with providers
<QueryProvider>           {/* React Query for server state */}
  <AuthProvider>          {/* Authentication context */}
    <FavouritesProvider>  {/* Local favorites */}
      <OfflineProvider>   {/* Offline detection */}
        <Header />
        {children}        {/* Page content goes here */}
      </OfflineProvider>
    </FavouritesProvider>
  </AuthProvider>
</QueryProvider>
```

### The AI Brain: `extractor.py`

```python
class RecipeExtractor:
    def extract_from_file(self, image_path: Path) -> ExtractedRecipe:
        # 1. Load and encode image
        image_data = base64.encode(...)

        # 2. Send to Claude Vision with extraction prompt
        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {...}},
                    {"type": "text", "text": EXTRACTION_PROMPT}
                ]
            }]
        )

        # 3. Parse JSON response
        return self._parse_response(message.content[0].text)
```

---

## Configuration Files

| File | Purpose |
|------|---------|
| `backend/requirements.txt` | Python package dependencies |
| `frontend/package.json` | Node package dependencies |
| `frontend/tailwind.config.ts` | Tailwind CSS customization |
| `frontend/tsconfig.json` | TypeScript compiler options |
| `frontend/next.config.ts` | Next.js settings |
| `docker-compose.yml` | Local development containers |
