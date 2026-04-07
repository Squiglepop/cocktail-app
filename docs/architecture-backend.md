# Backend Architecture

**Stack:** Python 3.9+ | FastAPI | SQLAlchemy 2.0 | PostgreSQL/SQLite

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (Routers)                      │
│  recipes.py │ upload.py │ categories.py │ auth.py │ etc.   │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   Services Layer                            │
│  extractor.py │ database.py │ auth.py │ duplicates.py      │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   Data Layer (Models)                       │
│  Recipe │ Ingredient │ RecipeIngredient │ User │ etc.      │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                      Database                               │
│              SQLite (dev) │ PostgreSQL (prod)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Request Flow Example: Create Recipe from Image

```python
# 1. Request comes in to router
POST /api/upload/extract-immediate
Body: FormData with image file

# 2. Router validates and saves file
@router.post("/extract-immediate")
async def upload_and_extract(file: UploadFile, db: Session = Depends(get_db)):
    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400)

    # Save to filesystem
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

# 3. Service layer extracts recipe using Claude
    extractor = RecipeExtractor()
    extracted = extractor.extract_from_file(file_path)

# 4. Map to database model and save
    recipe = Recipe(
        name=extracted.name,
        ingredients=...,
        template=extracted.template,
    )
    db.add(recipe)
    db.commit()

# 5. Return response
    return recipe  # Automatically serialized via Pydantic
```

---

## Key Components

### 1. FastAPI Application (`main.py`)

The app uses a **lifespan handler** for startup/shutdown:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    validate_production_config()  # Check env vars
    if production:
        run_migrations()  # Alembic migrations
    else:
        create_tables()   # Dev: just create tables
    yield
    # SHUTDOWN (cleanup if needed)
```

### 2. Dependency Injection (`get_db`)

FastAPI uses dependency injection for database sessions:

```python
# In services/database.py
def get_db() -> Generator[Session, None, None]:
    """Yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Used in routers
@router.get("/recipes")
def list_recipes(db: Session = Depends(get_db)):
    # db is automatically injected
    return db.query(Recipe).all()
```

### 3. SQLAlchemy Models (`models/recipe.py`)

Modern SQLAlchemy 2.0 style with type annotations:

```python
class Recipe(Base):
    __tablename__ = "recipes"

    # Primary key
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)

    # Required fields
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Optional fields
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        "RecipeIngredient",
        back_populates="recipe",
        cascade="all, delete-orphan"  # Delete ingredients when recipe deleted
    )
```

### 4. Pydantic Schemas (`schemas/recipe.py`)

Request/response validation:

```python
# For creating recipes (request body)
class RecipeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    ingredients: List[RecipeIngredientCreate] = []

    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models

# For responses (what clients see)
class RecipeResponse(RecipeCreate):
    id: str
    created_at: datetime
    has_image: bool
```

### 5. Recipe Extractor (`services/extractor.py`)

The AI integration:

```python
class RecipeExtractor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def extract_from_file(self, image_path: Path) -> ExtractedRecipe:
        # Load and encode image
        image_data, media_type = self._load_image_from_file(image_path)

        # Call Claude Vision
        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", ...}},
                    {"type": "text", "text": EXTRACTION_PROMPT}
                ]
            }]
        )

        # Parse JSON response
        return self._parse_response(message.content[0].text)
```

---

## Enums System

The app uses a rich categorization system for cocktails:

```python
class CocktailTemplate(str, Enum):
    """Cocktail family/template classification."""
    SOUR = "sour"              # Spirit + citrus + sweet
    OLD_FASHIONED = "old_fashioned"  # Spirit + sugar + bitters
    MARTINI = "martini"        # Spirit + vermouth
    NEGRONI = "negroni"        # Spirit + bitter liqueur + vermouth
    HIGHBALL = "highball"      # Spirit + lengthener
    TIKI = "tiki"              # Complex, tropical
    # ... 20+ more

class Glassware(str, Enum):
    COUPE = "coupe"
    ROCKS = "rocks"
    HIGHBALL = "highball"
    # ... 20+ more
```

---

## Authentication Flow

1. **Register**: User provides email + password
2. **Login**: Returns JWT token
3. **Authenticated requests**: Include `Authorization: Bearer <token>` header
4. **Token validation**: `get_current_user()` dependency decodes JWT

```python
# Dependency for protected endpoints
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except JWTError:
        raise HTTPException(status_code=401)

# Usage in router
@router.delete("/recipes/{id}")
def delete_recipe(id: str, current_user: User = Depends(get_current_user)):
    # Only authenticated users can delete
```

---

## Database Migrations (Alembic)

When you change models, you need to migrate the database:

```bash
# Generate migration
alembic revision --autogenerate -m "Add user ratings table"

# Apply migrations
alembic upgrade head
```

Migration files are in `alembic/versions/` and track schema changes over time.

---

## Error Handling

FastAPI uses `HTTPException` for API errors:

```python
@router.get("/recipes/{id}")
def get_recipe(id: str, db: Session = Depends(get_db)):
    recipe = db.query(Recipe).filter(Recipe.id == id).first()
    if not recipe:
        raise HTTPException(
            status_code=404,
            detail="Recipe not found"
        )
    return recipe
```

---

## Testing

Tests use pytest with fixtures:

```python
# conftest.py
@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield SessionLocal(bind=engine)

@pytest.fixture
def client(test_db):
    """Create test client with test database."""
    app.dependency_overrides[get_db] = lambda: test_db
    return TestClient(app)

# test_recipes.py
def test_create_recipe(client):
    response = client.post("/api/recipes", json={
        "name": "Margarita",
        "ingredients": [...]
    })
    assert response.status_code == 200
```
