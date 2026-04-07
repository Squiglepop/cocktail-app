# Development Guide

How to run the project locally and start developing.

---

## Prerequisites

- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **Anthropic API Key** (for AI extraction)

---

## Quick Start

### 1. Clone and Setup Backend

```bash
cd cocktail-app/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env

# Run the server
uvicorn app.main:app --reload
```

Backend runs at: **http://localhost:8000**
API docs at: **http://localhost:8000/docs**

### 2. Setup Frontend

```bash
cd cocktail-app/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend runs at: **http://localhost:3000**

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Optional (defaults shown)
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///./cocktails.db
CORS_ORIGINS=http://localhost:3000
UPLOAD_DIR=./data/uploads
```

### Frontend

```env
# Optional - defaults to production API
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

---

## Project Commands

### Backend

```bash
# Run server
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Create database migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Format code
black app/
isort app/
```

### Frontend

```bash
# Development server
npm run dev

# Production build
npm run build

# Start production server
npm start

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

---

## Development Workflow

### Adding a New Feature

1. **Backend first** - Add models, schemas, services, and routes
2. **Test it** - Use the FastAPI docs at `/docs` to test endpoints
3. **Frontend** - Add API function, hook, and components
4. **Test E2E** - Verify full flow works

### Example: Adding a "Notes" Field to Recipes

**Step 1: Update Model** (`backend/app/models/recipe.py`)
```python
class Recipe(Base):
    # ... existing fields ...
    tasting_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

**Step 2: Create Migration**
```bash
alembic revision --autogenerate -m "Add tasting_notes to recipes"
alembic upgrade head
```

**Step 3: Update Schemas** (`backend/app/schemas/recipe.py`)
```python
class RecipeCreate(BaseModel):
    tasting_notes: Optional[str] = None

class RecipeResponse(RecipeCreate):
    tasting_notes: Optional[str]
```

**Step 4: Update API Types** (`frontend/lib/api.ts`)
```typescript
export interface Recipe {
  tasting_notes?: string;
}
```

**Step 5: Update UI** (`frontend/app/recipes/[id]/page.tsx`)
```tsx
{recipe.tasting_notes && (
  <div>
    <h3>Tasting Notes</h3>
    <p>{recipe.tasting_notes}</p>
  </div>
)}
```

---

## Database

### SQLite (Development)

Database file: `backend/cocktails.db`

View with any SQLite tool:
```bash
sqlite3 cocktails.db
.tables
SELECT * FROM recipes LIMIT 5;
```

### PostgreSQL (Production)

Railway provides PostgreSQL. Connection string is in `DATABASE_URL` env var.

---

## Testing

### Backend Tests

```bash
cd backend
pytest                           # Run all tests
pytest tests/test_recipes.py     # Run specific file
pytest -k "test_create"          # Run tests matching pattern
pytest --cov=app --cov-report=html  # Coverage report
```

Test fixtures in `conftest.py` provide:
- `test_db` - In-memory SQLite database
- `client` - TestClient with test database
- `auth_token` - Valid JWT for authenticated tests

### Frontend Tests

```bash
cd frontend
npm test                         # Run all tests
npm test -- --watch              # Watch mode
npm run test:coverage            # With coverage
```

Tests use:
- **Vitest** - Test runner
- **React Testing Library** - Component testing
- **MSW** (optional) - API mocking

---

## Debugging

### Backend

**FastAPI auto-reload:** The `--reload` flag restarts on file changes.

**Interactive docs:** http://localhost:8000/docs lets you test endpoints.

**Print debugging:**
```python
import logging
logging.info(f"Debug: {variable}")
```

**Python debugger:**
```python
import pdb; pdb.set_trace()
```

### Frontend

**React DevTools:** Browser extension for inspecting components.

**React Query DevTools:** Add to see query cache:
```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
// In QueryProvider
<ReactQueryDevtools initialIsOpen={false} />
```

**Console logging:**
```tsx
console.log('Debug:', variable);
```

---

## Code Style

### Backend

- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking (optional)

```bash
black app/
isort app/
flake8 app/
```

### Frontend

- **ESLint** - Linting
- **Prettier** - Formatting (via ESLint)
- **TypeScript** - Type checking

```bash
npm run lint
npx tsc --noEmit
```

---

## Common Issues

### "CORS error"

Backend isn't allowing frontend origin. Check `CORS_ORIGINS` in backend `.env`:
```env
CORS_ORIGINS=http://localhost:3000
```

### "ANTHROPIC_API_KEY not set"

Create `backend/.env` with your API key:
```env
ANTHROPIC_API_KEY=sk-ant-...
```

### "Module not found"

Backend: Make sure virtualenv is activated:
```bash
source venv/bin/activate
```

Frontend: Install dependencies:
```bash
npm install
```

### Database errors after model changes

Run migrations:
```bash
cd backend
alembic upgrade head
```

Or delete `cocktails.db` and restart (loses data!).

---

## Deployment

See [DEPLOY.md](../cocktail-app/DEPLOY.md) for Railway deployment instructions.

Quick summary:
1. Push to GitHub
2. Create Railway project
3. Add PostgreSQL database
4. Deploy backend with `ROOT_DIRECTORY=backend`
5. Deploy frontend with `ROOT_DIRECTORY=frontend`
6. Set environment variables
