# Admin Panel PRD

**Product**: Cocktail Library - Admin Panel Feature
**Author**: Mary (Business Analyst) with Deemo
**Date**: 2026-01-08
**Status**: Ready for Architecture Review

---

## 1. Overview

### 1.1 Problem Statement

The Cocktail Library app currently has no way for the owner to:
- Add or modify category options (spirits, glassware, templates, etc.)
- Edit recipes with incorrect data from AI extraction
- Manage user accounts
- Perform administrative maintenance

### 1.2 Solution Summary

Add inline administrative capabilities that appear contextually when logged in as admin, avoiding a separate admin portal. This keeps the UX seamless while enabling full content management.

### 1.3 Success Criteria

- Admin can add/edit/delete all category values
- Admin can edit any recipe inline
- Admin can view and manage user accounts
- Changes reflect immediately in filter dropdowns
- No disruption to existing user experience

---

## 2. Current State Analysis

### 2.1 Existing Infrastructure

| Component | Status | Notes |
|-----------|--------|-------|
| User Authentication | ✅ Complete | JWT access/refresh tokens, bcrypt passwords |
| User Model | ⚠️ Partial | Has `is_active`, missing `is_admin` |
| Admin Router | ⚠️ Partial | Exists at `/api/admin`, only has cleanup endpoint |
| Category Enums | ✅ Complete | 8 enum types with display names |
| Recipe Model | ✅ Ready | Stores categories as strings (not FK) |

### 2.2 Technical Debt to Address

1. **User.is_admin field** — Must be added via Alembic migration
2. **Admin authorization** — Current admin endpoints only require authentication, not admin check
3. **Category tables** — Need new database tables for dynamic categories

---

## 3. Functional Requirements

### 3.1 Admin Role Management

#### FR-3.1.1: Admin Flag
- Add `is_admin: bool` field to User model (default: False)
- First registered user becomes admin automatically (owner scenario)
- Only admins can grant/revoke admin status

#### FR-3.1.2: Admin Authorization Dependency
```python
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### 3.2 Category Management

#### FR-3.2.1: Database-Driven Categories

Create tables for each category type:

| Table | Fields | Seeded From |
|-------|--------|-------------|
| `category_templates` | id, value, display_name, description, sort_order, is_active | CocktailTemplate enum |
| `category_glassware` | id, value, display_name, category (stemmed/short/tall/specialty), sort_order, is_active | Glassware enum |
| `category_serving_styles` | id, value, display_name, description, sort_order, is_active | ServingStyle enum |
| `category_methods` | id, value, display_name, description, sort_order, is_active | Method enum |
| `category_spirits` | id, value, display_name, sort_order, is_active | SpiritCategory enum |

#### FR-3.2.2: Category CRUD Endpoints

```
GET    /api/admin/categories/{type}           - List all (including inactive)
POST   /api/admin/categories/{type}           - Create new category value
PUT    /api/admin/categories/{type}/{id}      - Update category
DELETE /api/admin/categories/{type}/{id}      - Soft delete (set is_active=false)
POST   /api/admin/categories/{type}/reorder   - Update sort_order
```

Where `{type}` is one of: `templates`, `glassware`, `serving-styles`, `methods`, `spirits`

#### FR-3.2.3: Public Category Endpoints (Updated)

Modify existing `/api/categories/*` endpoints to:
- Query database tables instead of enums
- Filter by `is_active=true`
- Order by `sort_order`

#### FR-3.2.4: Category Value Constraints
- `value` field: snake_case, unique per table, immutable after creation
- `display_name`: User-facing label, editable
- Cannot delete categories that are in use (show count of recipes using it)

### 3.3 Recipe Management

#### FR-3.3.1: Recipe Edit Capabilities

Admin can edit ANY recipe (not just their own):

```
PUT /api/recipes/{id}  - Existing endpoint, add admin bypass for ownership check
```

Fields editable by admin:
- All text fields (name, description, instructions, notes, garnish)
- All category assignments (template, glassware, method, serving_style, main_spirit)
- Ingredients (add/remove/modify)
- Visibility setting
- User assignment (transfer ownership)

#### FR-3.3.2: Recipe Delete

```
DELETE /api/recipes/{id}  - Existing endpoint, add admin bypass
```

- Requires confirmation modal on frontend
- Hard delete (cascades to recipe_ingredients)
- Deletes associated image file

#### FR-3.3.3: Bulk Operations (Phase 2)

Deferred to future release:
- Bulk delete selected recipes
- Bulk export to JSON/CSV
- Bulk reassign categories

### 3.4 User Management

#### FR-3.4.1: User List Endpoint

```
GET /api/admin/users
```

Returns:
```json
{
  "users": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "display_name": "Display Name",
      "is_active": true,
      "is_admin": false,
      "recipe_count": 42,
      "created_at": "2026-01-01T00:00:00Z",
      "last_login_at": "2026-01-08T12:00:00Z"
    }
  ],
  "total": 15
}
```

#### FR-3.4.2: User Status Management

```
PATCH /api/admin/users/{id}
```

Body:
```json
{
  "is_active": false,      // Deactivate account
  "is_admin": true         // Grant admin (only if requester is admin)
}
```

Constraints:
- Cannot deactivate self
- Cannot remove own admin status
- Deactivated users cannot log in (existing tokens fail)

#### FR-3.4.3: User Invite (Phase 2)

Deferred: Email invitation system for new users.

### 3.5 Ingredient Management

#### FR-3.5.1: Ingredient CRUD

Admin can manage the ingredient master list (table already exists):

```
GET    /api/admin/ingredients           - List all ingredients (paginated, searchable)
POST   /api/admin/ingredients           - Create new ingredient
PUT    /api/admin/ingredients/{id}      - Update ingredient
DELETE /api/admin/ingredients/{id}      - Delete ingredient (with usage check)
```

#### FR-3.5.2: Ingredient Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Ingredient name (e.g., "Raspberry Liqueur") |
| `type` | enum | spirit, liqueur, wine_fortified, bitter, syrup, juice, mixer, dairy, egg, garnish, other |
| `spirit_category` | enum? | If type=spirit, which category (gin, vodka, rum_light, etc.) |
| `description` | text | Optional description |
| `common_brands` | text | Optional brand suggestions |

#### FR-3.5.3: Ingredient Constraints

- Cannot delete ingredients that are used in recipes (show usage count)
- Name must be unique (case-insensitive)
- Searchable by name and type for admin list

#### FR-3.5.4: Duplicate Detection

```
GET /api/admin/ingredients/duplicates
```

Returns groups of potential duplicate ingredients detected via:
- Case-insensitive exact match (e.g., "Lime Juice" vs "lime juice")
- Fuzzy matching with >80% similarity (Levenshtein distance)
- Common variation patterns (e.g., "Fresh X" vs "X", "X (fresh)" vs "X")

Each group includes:
- Suggested target (highest usage count)
- List of potential duplicates with similarity scores
- Detection reason for each match

#### FR-3.5.5: Ingredient Merge

```
POST /api/admin/ingredients/merge
Body: { source_ids: [...], target_id: "..." }
```

Merges duplicate ingredients:
- Updates all `recipe_ingredients` from sources to target
- Deletes source ingredients
- Returns count of recipes affected
- Audit log entry captures merge with source names and affected recipe count

### 3.6 Audit Logging

#### FR-3.6.1: Admin Action Log Table

```sql
CREATE TABLE admin_audit_log (
    id VARCHAR(36) PRIMARY KEY,
    admin_user_id VARCHAR(36) NOT NULL,
    action VARCHAR(50) NOT NULL,           -- 'category_create', 'recipe_delete', etc.
    entity_type VARCHAR(50) NOT NULL,      -- 'recipe', 'category', 'user'
    entity_id VARCHAR(36),
    details JSON,                          -- Old/new values for auditing
    created_at TIMESTAMP NOT NULL
);
```

#### FR-3.5.2: Actions to Log

| Action | Entity Type | Details |
|--------|-------------|---------|
| `category_create` | category | {type, value, display_name} |
| `category_update` | category | {type, changes: {field: [old, new]}} |
| `category_delete` | category | {type, value} |
| `recipe_update` | recipe | {changes: {field: [old, new]}} |
| `recipe_delete` | recipe | {name, user_id} |
| `user_deactivate` | user | {email} |
| `user_grant_admin` | user | {email} |
| `ingredient_create` | ingredient | {name, type} |
| `ingredient_update` | ingredient | {changes: {field: [old, new]}} |
| `ingredient_delete` | ingredient | {name, type} |
| `ingredient_merge` | ingredient | {source_ids, source_names, target_id, target_name, recipes_updated} |

---

## 4. Non-Functional Requirements

### 4.1 Security

- All admin endpoints require `is_admin=true`
- Rate limiting on admin endpoints (10 req/min)
- Audit log for compliance
- Admin cannot delete self or remove own admin

### 4.2 Performance

- Category list queries cached (invalidate on admin changes)
- Filter dropdowns load in <200ms
- Pagination for user list (>100 users)

### 4.3 Data Integrity

- Soft delete for categories (never lose data)
- Hard delete for recipes (with image cleanup)
- Foreign key constraints where appropriate

---

## 5. UX Requirements

### 5.1 Inline Edit Mode

When admin is logged in, UI shows:

| Location | Admin Control |
|----------|---------------|
| Recipe card | Edit pencil icon, Delete icon |
| Recipe detail page | "Edit" button, inline editable fields |
| Filter dropdowns | "Manage" link next to each category |
| User avatar/menu | "Admin" section with User Management link |

### 5.2 Category Management Modal

Triggered from "Manage" link on filter dropdowns:
- List view of all values (including inactive, grayed out)
- Drag-to-reorder
- Inline edit for display_name
- Add new button
- Delete with confirmation (shows recipe count using it)

### 5.3 User Management Page

New page at `/admin/users`:
- Table: Email, Display Name, Status, Recipe Count, Created, Last Login
- Actions: Activate/Deactivate toggle, Grant/Revoke Admin
- Filter by status
- Search by email/name

---

## 6. Data Migration

### 6.1 Migration Steps

1. **Add User.is_admin field**
   ```
   alembic revision -m "add_user_is_admin"
   ALTER TABLE users ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT FALSE;
   ```

2. **Add User.last_login_at field**
   ```
   ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP;
   ```

3. **Create category tables**
   - One migration per table
   - Seed with enum values preserving order

4. **Create audit_log table**

5. **Set first user as admin** (data migration)
   ```sql
   UPDATE users SET is_admin = TRUE
   WHERE id = (SELECT id FROM users ORDER BY created_at LIMIT 1);
   ```

### 6.2 Backward Compatibility

- Existing `/api/categories/*` endpoints continue working
- Recipes with category values not in new tables still display (graceful degradation)
- No changes to recipe creation/extraction flow

---

## 7. API Summary

### New Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/categories/{type}` | List all category values |
| POST | `/api/admin/categories/{type}` | Create category value |
| PUT | `/api/admin/categories/{type}/{id}` | Update category |
| DELETE | `/api/admin/categories/{type}/{id}` | Soft delete category |
| POST | `/api/admin/categories/{type}/reorder` | Reorder categories |
| GET | `/api/admin/users` | List all users |
| PATCH | `/api/admin/users/{id}` | Update user status |
| GET | `/api/admin/audit-log` | View audit log (filtered) |

### Modified Existing Endpoints

| Endpoint | Change |
|----------|--------|
| `GET /api/categories/*` | Query DB instead of enums |
| `PUT /api/recipes/{id}` | Admin bypass for ownership |
| `DELETE /api/recipes/{id}` | Admin bypass for ownership |

---

## 8. Implementation Phases

### Phase 1: Foundation (MVP)
- [ ] Add `is_admin` and `last_login_at` to User model
- [ ] Create `require_admin` dependency
- [ ] Create category database tables with seed migration
- [ ] Implement category CRUD endpoints
- [ ] Update public category endpoints to use DB
- [ ] Add admin bypass to recipe edit/delete

### Phase 2: User Management
- [ ] User list endpoint with pagination
- [ ] User status management (activate/deactivate)
- [ ] Admin grant/revoke functionality
- [ ] Frontend user management page

### Phase 3: UX Polish
- [ ] Inline edit UI for recipes
- [ ] Category management modal
- [ ] Drag-to-reorder categories
- [ ] Admin indicator in UI

### Phase 4: Audit & Operations
- [ ] Audit log table and service
- [ ] Audit log viewer for admin
- [ ] Bulk operations (if needed)

---

## 9. Design Decisions (Resolved)

### 9.1 Category Table Design: Separate Tables

**Decision**: Use separate tables per category type (not a single polymorphic table).

**Rationale**:
- Each category type has different fields (e.g., glassware has `category` for stemmed/short/tall)
- Simpler queries without `WHERE type = 'x'` everywhere
- Database-level type safety
- Clearer schema for developers

**Tables**: `category_templates`, `category_glassware`, `category_serving_styles`, `category_methods`, `category_spirits`

### 9.2 First User = Admin

**Decision**: The first registered user (earliest `created_at`) automatically becomes admin.

**Rationale**:
- Single-owner application model
- No need for manual database intervention
- Handled via data migration

**Implementation**: Migration script sets `is_admin = TRUE` for user with `MIN(created_at)`.

---

## 10. Open Items for Architecture

1. **Caching strategy** — Redis vs. in-memory for category lists?
2. **Real-time updates** — WebSocket for multi-admin scenarios? (Likely overkill for single admin)
3. **Image handling** — Keep current file-based or move to object storage?

---

## 10. Acceptance Criteria Summary

### Must Have (Phase 1)
- [ ] Admin can add new category values
- [ ] Admin can edit category display names
- [ ] Admin can soft-delete unused categories
- [ ] Admin can edit any recipe
- [ ] Admin can delete any recipe
- [ ] Filter dropdowns reflect category changes immediately

### Should Have (Phase 2)
- [ ] Admin can view all users
- [ ] Admin can deactivate users
- [ ] Admin can grant admin to other users
- [ ] Audit log captures admin actions

### Nice to Have (Phase 3+)
- [ ] Drag-to-reorder categories
- [ ] Bulk recipe operations
- [ ] User invitation system
- [ ] Admin dashboard with stats

---

**Next Step**: Architecture review to finalize database design and caching strategy.
