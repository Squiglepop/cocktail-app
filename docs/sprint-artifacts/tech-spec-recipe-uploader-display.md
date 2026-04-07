# Tech-Spec: Recipe Uploader Display

**Created:** 2025-01-07
**Status:** Ready for Development

## Overview

### Problem Statement

Users cannot see who uploaded a recipe. While the database already tracks `user_id` on recipes, this information isn't exposed in a user-friendly way (only raw UUID) and the frontend doesn't display it.

### Solution

1. Add `uploader_name` to API responses (display_name from User, with email-prefix fallback)
2. Capture uploader on upload/extract endpoints (optional auth - anonymous still allowed)
3. Display "Uploaded by [name]" on recipe cards and detail pages (hide if null)

### Scope

**In Scope:**
- Add `uploader_name` field to recipe API responses
- Update upload endpoints to capture current user
- Display uploader on RecipeCard and RecipeDetail
- Handle null uploaders gracefully (hide completely - no "Unknown")

**Out of Scope:**
- Backfilling existing recipes with uploader (they stay null)
- User profile pages
- Filtering recipes by uploader (future feature)

## Context for Development

### Codebase Patterns

**Existing FK pattern (already in place):**
```python
# Recipe model - backend/app/models/recipe.py
user_id: Mapped[Optional[str]] = mapped_column(
    String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
)
user: Mapped[Optional["User"]] = relationship("User", back_populates="recipes")
```

**Auth dependency pattern:**
```python
from app.routers.auth import get_current_user, get_current_user_optional
current_user: User = Depends(get_current_user)  # Required
current_user: Optional[User] = Depends(get_current_user_optional)  # Optional
```

### Files to Reference

| File | Purpose |
|------|---------|
| `backend/app/models/recipe.py` | Recipe model (already has user_id) |
| `backend/app/schemas/recipe.py` | Add uploader_name to responses |
| `backend/app/routers/upload.py` | Add auth to extract endpoints |
| `backend/app/routers/recipes.py` | Reference for auth pattern |
| `frontend/components/recipes/RecipeCard.tsx` | Add uploader display |
| `frontend/app/recipes/[id]/page.tsx` | Add uploader display |
| `frontend/lib/api.ts` | Update TypeScript types |

### Technical Decisions

1. **uploader_name vs uploader object**: Simple string field, not nested object (less complexity)
2. **Null handling**: Hide uploader section completely when null (not "Unknown")
3. **Auth on upload**: Use `get_current_user_optional` - capture user if logged in, allow anonymous uploads (NO breaking change)
4. **Email fallback**: When `display_name` is null, use email prefix - compute this in Pydantic schema (single source of truth)
5. **N+1 prevention**: Use `selectinload(Recipe.user)` on list queries to eager-load user relationship

## Implementation Plan

### Tasks

- [ ] Task 1: Add `uploader_name` computed property to recipe schemas (with email-prefix fallback logic)
- [ ] Task 2: Update recipe queries to use `selectinload(Recipe.user)` for eager loading (prevent N+1)
- [ ] Task 3: Add optional auth to upload endpoints (get_current_user_optional)
- [ ] Task 4: Capture user_id on recipe creation if user is authenticated
- [ ] Task 5: Update frontend TypeScript types (Recipe, RecipeListItem)
- [ ] Task 6: Display uploader on RecipeCard component
- [ ] Task 7: Display uploader on RecipeDetail page
- [ ] Task 8: Add tests for new functionality

### Acceptance Criteria

- [ ] AC1: When viewing a recipe card, the uploader's name is shown (hidden completely if null)
- [ ] AC2: When viewing recipe details, "Uploaded by [name]" appears in metadata
- [ ] AC3: When uploading a new recipe (authenticated), the recipe is linked to current user
- [ ] AC4: Existing recipes without uploader display gracefully (no errors)
- [ ] AC5: API responses include `uploader_name` field (string or null)

## Additional Context

### Dependencies

- No new packages required
- No database migration needed (column exists)

### Testing Strategy

**Backend:**

- Test upload WITH token → recipe.user_id = current user's ID
- Test upload WITHOUT token → recipe.user_id = null (NOT 401 - anonymous allowed)
- Test recipe response includes uploader_name when user_id present
- Test recipe response has null uploader_name when user_id null
- Test uploader_name fallback: user with null display_name → returns email prefix

**Frontend:**

- Test RecipeCard displays uploader when present
- Test RecipeCard hides uploader section when null (no "Unknown" text)
- Test RecipeCard with email-prefix fallback (user has no display_name)
- Test RecipeDetail displays uploader

### Notes

- Upload endpoints continue to allow anonymous uploads (no breaking change)
- Authenticated users get their name attached; anonymous uploads have null uploader
- The `display_name` field on User is optional - fall back to email prefix if null
