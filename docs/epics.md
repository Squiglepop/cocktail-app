---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - docs/admin-panel-prd.md
  - docs/admin-panel-architecture.md
workflowType: 'epics-stories'
lastStep: 4
status: 'complete'
completedAt: '2026-01-08'
project_name: 'Cocktail Shots - Admin Panel'
user_name: 'Deemo'
date: '2026-01-08'
---

# Cocktail Shots - Admin Panel - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Cocktail Shots - Admin Panel, decomposing the requirements from the PRD and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

| FR ID | Description |
| --- | --- |
| FR-3.1.1 | Admin Flag - Add `is_admin` field to User model (default: False), first registered user becomes admin automatically, only admins can grant/revoke admin status |
| FR-3.1.2 | Admin Authorization Dependency - `require_admin` FastAPI dependency that raises 403 if user is not admin |
| FR-3.2.1 | Database-Driven Categories - Create 5 tables (`category_templates`, `category_glassware`, `category_serving_styles`, `category_methods`, `category_spirits`) with id, value, display_name, description, sort_order, is_active fields |
| FR-3.2.2 | Category CRUD Endpoints - GET/POST/PUT/DELETE `/api/admin/categories/{type}` plus reorder endpoint |
| FR-3.2.3 | Public Category Endpoints - Modify existing `/api/categories/*` to query database tables instead of enums, filter by `is_active=true`, order by `sort_order` |
| FR-3.2.4 | Category Value Constraints - `value` field is snake_case, unique per table, immutable after creation; `display_name` is editable; cannot delete categories in use |
| FR-3.3.1 | Recipe Edit Capabilities - Admin can edit ANY recipe with bypass for ownership check, including all text fields, category assignments, ingredients, visibility, user assignment |
| FR-3.3.2 | Recipe Delete - Admin bypass for ownership, hard delete with cascade to recipe_ingredients, delete associated image file, requires confirmation modal |
| FR-3.3.3 | Bulk Operations - *Deferred to Phase 2* (bulk delete, export, reassign) |
| FR-3.4.1 | User List Endpoint - GET `/api/admin/users` returns id, email, display_name, is_active, is_admin, recipe_count, created_at, last_login_at |
| FR-3.4.2 | User Status Management - PATCH `/api/admin/users/{id}` for is_active and is_admin; cannot deactivate self or remove own admin |
| FR-3.4.3 | User Invite - *Deferred to Phase 2* (email invitation system) |
| FR-3.5.1 | Ingredient CRUD - GET/POST/PUT/DELETE `/api/admin/ingredients` with pagination and search |
| FR-3.5.2 | Ingredient Fields - name (string), type (enum), spirit_category (enum, optional), description (text), common_brands (text) |
| FR-3.5.3 | Ingredient Constraints - Cannot delete ingredients used in recipes (show usage count), name must be unique (case-insensitive) |
| FR-3.5.4 | Duplicate Detection - GET `/api/admin/ingredients/duplicates` returns groups via case-insensitive match, fuzzy matching >80% similarity, common variation patterns |
| FR-3.5.5 | Ingredient Merge - POST `/api/admin/ingredients/merge` updates all recipe_ingredients from sources to target, deletes sources, returns affected count, creates audit entry |
| FR-3.6.1 | Audit Log Table - `admin_audit_log` with id, admin_user_id, action, entity_type, entity_id, details (JSON), created_at |
| FR-3.6.2 | Actions to Log - category_create/update/delete, recipe_update/delete, user_deactivate/grant_admin, ingredient_create/update/delete/merge |

### NonFunctional Requirements

| NFR ID | Description |
| --- | --- |
| NFR-4.1.1 | All admin endpoints require `is_admin=true` |
| NFR-4.1.2 | Rate limiting on admin endpoints (10 req/min) using slowapi |
| NFR-4.1.3 | Audit log for compliance - all admin actions tracked |
| NFR-4.1.4 | Admin cannot delete self or remove own admin status |
| NFR-4.2.1 | Category list queries cached via React Query (Admin: 1min staleTime, Users: 5min) |
| NFR-4.2.2 | Filter dropdowns load in <200ms |
| NFR-4.2.3 | Pagination for user list (>100 users) |
| NFR-4.3.1 | Soft delete for categories (set is_active=false, never lose data) |
| NFR-4.3.2 | Hard delete for recipes (with image cleanup via cascade) |
| NFR-4.3.3 | Foreign key constraints where appropriate |

### Additional Requirements

**From Architecture Document:**

- **Brownfield Project**: No starter template needed - extends existing FastAPI + Next.js patterns
- **SQLAlchemy 2.0**: All new models must use `Mapped[]` syntax
- **Alembic Only**: Never use `create_all()` - all schema changes via migrations
- **Rate Limiting**: Use slowapi (Python-native decorators, Redis-upgradeable)
- **Caching Strategy**: React Query with role-based staleTime, invalidate on mutations
- **Audit Atomicity**: Fire-and-forget pattern - audit failures must not block admin operations
- **Migration Sequence**: Critical order: User fields → Category tables → Audit log
- **Breaking Change**: `categories.py` requires COMPLETE REWRITE (currently iterates Python enums)
- **Performance Index**: Add `recipe_ingredients.ingredient_id` INDEX (currently missing)
- **Fuzzy Matching**: Use `difflib.SequenceMatcher` (stdlib, no new dependencies)
- **Seed Verification**: Category seed values must match existing enum strings EXACTLY
- **Post-Migration Check**: Run verification SQL to check for orphaned recipes

**UX Requirements from PRD:**

- Inline Edit Mode: Edit pencil/delete icons on recipe cards when admin logged in
- Category Management Modal: Triggered from "Manage" link on filter dropdowns
- User Management Page: New page at `/admin/users` with table, filters, search
- Admin indicator in UI header

### FR Coverage Map

| FR | Epic | Description |
| --- | --- | --- |
| FR-3.1.1 | Epic 1 | Admin flag on User model |
| FR-3.1.2 | Epic 1 | require_admin dependency |
| FR-3.2.1 | Epic 1 | Database-driven category tables |
| FR-3.2.2 | Epic 1 | Category CRUD endpoints |
| FR-3.2.3 | Epic 1 | Public category endpoint rewrite |
| FR-3.2.4 | Epic 1 | Category value constraints |
| FR-3.3.1 | Epic 1 | Recipe edit admin bypass |
| FR-3.3.2 | Epic 1 | Recipe delete admin bypass |
| FR-3.3.3 | *Deferred* | Bulk operations (Phase 2) |
| FR-3.4.1 | Epic 3 | User list endpoint |
| FR-3.4.2 | Epic 3 | User status management |
| FR-3.4.3 | *Deferred* | User invite (Phase 2) |
| FR-3.5.1 | Epic 2 | Ingredient CRUD |
| FR-3.5.2 | Epic 2 | Ingredient fields |
| FR-3.5.3 | Epic 2 | Ingredient constraints |
| FR-3.5.4 | Epic 2 | Duplicate detection |
| FR-3.5.5 | Epic 2 | Ingredient merge |
| FR-3.6.1 | Epic 4 | Audit log table |
| FR-3.6.2 | Epic 4 | Actions to log |
| UX-5.1 | Epic 5 | Admin indicator in UI header |
| UX-5.2 | Epic 5 | Inline edit mode on recipe cards |
| UX-5.3 | Epic 5 | Category management modal |
| UX-5.4 | Epic 5 | Ingredient admin page |
| UX-5.5 | Epic 5 | User management page |
| UX-5.6 | Epic 5 | Audit log viewer |

## Epic List

### Epic 1: Admin Foundation & Content Management

Owner can access admin capabilities, fix recipe data, and manage all category options in filter dropdowns.

**FRs Covered:** FR-3.1.1, FR-3.1.2, FR-3.2.1, FR-3.2.2, FR-3.2.3, FR-3.2.4, FR-3.3.1, FR-3.3.2

### Epic 2: Ingredient Data Quality

Admin can clean up the ingredient master list, detect duplicates, and merge them to maintain data quality.

**FRs Covered:** FR-3.5.1, FR-3.5.2, FR-3.5.3, FR-3.5.4, FR-3.5.5

### Epic 3: User Account Management

Admin can view all users, activate/deactivate accounts, and grant admin privileges to trusted users.

**FRs Covered:** FR-3.4.1, FR-3.4.2

### Epic 4: Audit Trail & Compliance

Admin can track all administrative actions for accountability and troubleshooting.

**FRs Covered:** FR-3.6.1, FR-3.6.2

### Epic 5: Admin User Interface

Admin can access and use all administrative features through an intuitive inline interface.

**UX Requirements Covered:** PRD Section 5 (Inline Edit Mode, Category Management Modal, User Management Page, Admin Indicator)

---

## Epic 1: Admin Foundation & Content Management

Owner can access admin capabilities, fix recipe data, and manage all category options in filter dropdowns.

### Story 1.1: Admin User Setup

**As an** application owner,
**I want** the first registered user to automatically become an admin with special privileges,
**So that** I can manage the application without manual database intervention.

**Acceptance Criteria:**

**Given** the User model exists
**When** I run the migration
**Then** the `is_admin` boolean field is added (default: false)
**And** the `last_login_at` timestamp field is added (nullable)

**Given** there are existing users in the database
**When** the data migration runs
**Then** the user with the earliest `created_at` has `is_admin` set to true
**And** all other users have `is_admin` set to false

**Given** a user is authenticated
**When** they access an endpoint protected by `require_admin`
**And** they are NOT an admin
**Then** they receive a 403 Forbidden response with message "Admin access required"

**Given** a user is authenticated
**When** they access an endpoint protected by `require_admin`
**And** they ARE an admin
**Then** the request proceeds normally

**Given** a user successfully logs in
**When** the login completes
**Then** their `last_login_at` field is updated to the current timestamp

---

### Story 1.2: Admin Recipe Edit

**As an** admin,
**I want** to edit any recipe regardless of who created it,
**So that** I can fix incorrect data from AI extraction without needing to contact the recipe owner.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I send a PUT request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** the recipe is updated successfully
**And** I receive a 200 response with the updated recipe

**Given** I am authenticated as a regular user (not admin)
**When** I send a PUT request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** I receive a 403 Forbidden response
**And** the recipe is NOT modified

**Given** I am authenticated as an admin
**When** I edit a recipe
**Then** I can modify all text fields (name, description, instructions, notes, garnish)
**And** I can modify all category assignments (template, glassware, method, serving_style, main_spirit)
**And** I can modify ingredients (add/remove/modify)
**And** I can modify visibility setting
**And** I can transfer ownership to another user

**Given** I am authenticated as an admin
**When** I edit my OWN recipe
**Then** the edit works the same as before (existing functionality preserved)

---

### Story 1.3: Admin Recipe Delete

**As an** admin,
**I want** to delete any recipe regardless of who created it,
**So that** I can remove inappropriate or duplicate content from the library.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I send a DELETE request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** the recipe is deleted successfully
**And** I receive a 200/204 response

**Given** I am authenticated as a regular user (not admin)
**When** I send a DELETE request to `/api/recipes/{id}` for a recipe I do NOT own
**Then** I receive a 403 Forbidden response
**And** the recipe is NOT deleted

**Given** a recipe has an associated image file
**When** an admin deletes the recipe
**Then** the image file is also deleted from storage
**And** the `recipe_ingredients` junction records are cascade deleted

**Given** I am authenticated as an admin
**When** I delete my OWN recipe
**Then** the delete works the same as before (existing functionality preserved)

---

### Story 1.4: Category Database Tables

**As a** system,
**I want** category values stored in database tables instead of Python enums,
**So that** admins can add and modify categories without code deployments.

**Acceptance Criteria:**

**Given** the migration runs
**When** it completes
**Then** the following 5 tables are created:
- `category_templates` (id, value, label, description, sort_order, is_active, created_at)
- `category_glassware` (id, value, label, category, sort_order, is_active, created_at)
- `category_serving_styles` (id, value, label, description, sort_order, is_active, created_at)
- `category_methods` (id, value, label, description, sort_order, is_active, created_at)
- `category_spirits` (id, value, label, sort_order, is_active, created_at)

**Given** the seed migration runs
**When** it completes
**Then** each table is populated with values from the corresponding Python enum
**And** the `value` field matches the enum string EXACTLY (e.g., "old_fashioned", not "Old Fashioned")
**And** the `label` field contains the display name
**And** `sort_order` preserves the original enum ordering
**And** all records have `is_active = true`

**Given** the migrations complete
**When** I run the verification SQL
**Then** no recipes have orphaned category values (all recipe.template values exist in category_templates.value, etc.)

**Given** the `recipe_ingredients` table exists
**When** the index migration runs
**Then** an index is created on `recipe_ingredients.ingredient_id` for query performance

---

### Story 1.5: Public Category Endpoints Rewrite

**As a** user browsing the cocktail library,
**I want** filter dropdowns to show dynamically managed categories,
**So that** I see any new categories added by the admin immediately.

**Acceptance Criteria:**

**Given** the `categories.py` router is rewritten
**When** a user calls `GET /api/categories/templates`
**Then** it queries the `category_templates` table (not the Python enum)
**And** returns only records where `is_active = true`
**And** results are ordered by `sort_order`

**Given** the public category endpoints
**When** called for any category type (templates, glassware, serving-styles, methods, spirits)
**Then** each returns the same response format as before
**And** existing frontend code continues to work without changes

**Given** an admin has soft-deleted a category (is_active = false)
**When** a user calls the public endpoint
**Then** the deleted category is NOT included in the response

**Given** recipes exist with a now-inactive category value
**When** viewing those recipes
**Then** the category value still displays correctly (graceful degradation)

---

### Story 1.6: Admin Category Management

**As an** admin,
**I want** to add, edit, reorder, and soft-delete category values,
**So that** I can customize the filter options without deploying code changes.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/categories/{type}`
**Then** I receive ALL category values (including inactive ones)
**And** inactive values are clearly marked with `is_active: false`

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/categories/{type}` with a new category
**Then** the category is created with:
- `value`: snake_case, unique, validated
- `label`: display name provided by admin
- `sort_order`: appended to end (highest + 1)
- `is_active`: true

**Given** I try to create a category with a `value` that already exists
**When** I submit the request
**Then** I receive a 409 Conflict response
**And** the duplicate is not created

**Given** I am authenticated as an admin
**When** I call `PUT /api/admin/categories/{type}/{id}`
**Then** I can update `label`, `description`, `is_active`
**And** the `value` field is IMMUTABLE (cannot be changed)

**Given** I am authenticated as an admin
**When** I call `DELETE /api/admin/categories/{type}/{id}`
**Then** the category is soft-deleted (`is_active` set to false)
**And** the record is NOT physically removed

**Given** a category is used by existing recipes
**When** I try to delete it
**Then** I receive a response showing the count of recipes using this category
**And** I must confirm the soft-delete (or the delete proceeds with warning)

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/categories/{type}/reorder` with an array of IDs in new order
**Then** the `sort_order` values are updated to match the new sequence

**Given** I am NOT an admin
**When** I call any `/api/admin/categories/*` endpoint
**Then** I receive a 403 Forbidden response

---

## Epic 2: Ingredient Data Quality

Admin can clean up the ingredient master list, detect duplicates, and merge them to maintain data quality.

### Story 2.1: Ingredient Admin CRUD

**As an** admin,
**I want** to view, add, edit, and delete ingredients from the master list,
**So that** I can maintain a clean and accurate ingredient database.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/ingredients`
**Then** I receive a paginated list of all ingredients
**And** results include: id, name, type, spirit_category, description, common_brands
**And** pagination metadata (total, page, per_page) is included

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/ingredients?search=lime`
**Then** I receive ingredients matching the search term
**And** search works on name and type fields

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/ingredients` with valid data
**Then** a new ingredient is created with:
- `name`: required, unique (case-insensitive)
- `type`: enum (spirit, liqueur, wine_fortified, bitter, syrup, juice, mixer, dairy, egg, garnish, other)
- `spirit_category`: optional, only valid if type=spirit
- `description`: optional text
- `common_brands`: optional text

**Given** I try to create an ingredient with a name that already exists (case-insensitive)
**When** I submit the request
**Then** I receive a 409 Conflict response

**Given** I am authenticated as an admin
**When** I call `PUT /api/admin/ingredients/{id}`
**Then** I can update all fields (name, type, spirit_category, description, common_brands)

**Given** I am authenticated as an admin
**When** I call `DELETE /api/admin/ingredients/{id}` for an ingredient NOT used in any recipe
**Then** the ingredient is deleted successfully

**Given** I try to delete an ingredient that IS used in recipes
**When** I submit the request
**Then** I receive a 409 Conflict response
**And** the response includes the count of recipes using this ingredient
**And** the ingredient is NOT deleted

---

### Story 2.2: Ingredient Duplicate Detection

**As an** admin,
**I want** to see potential duplicate ingredients detected automatically,
**So that** I can identify and clean up inconsistencies from AI extraction.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/ingredients/duplicates`
**Then** I receive groups of potential duplicate ingredients

**Given** the duplicate detection runs
**When** two ingredients have case-insensitive exact match (e.g., "Lime Juice" vs "lime juice")
**Then** they are grouped as duplicates
**And** the detection reason is "exact_match_case_insensitive"

**Given** the duplicate detection runs
**When** two ingredients have >80% similarity (Levenshtein/SequenceMatcher)
**Then** they are grouped as duplicates
**And** the detection reason is "fuzzy_match" with similarity score

**Given** the duplicate detection runs
**When** two ingredients match common variation patterns (e.g., "Fresh Lime Juice" vs "Lime Juice", "Lime Juice (fresh)" vs "Lime Juice")
**Then** they are grouped as duplicates
**And** the detection reason is "variation_pattern"

**Given** a duplicate group is returned
**When** I view the group
**Then** it includes:
- Suggested target (ingredient with highest usage count)
- List of potential duplicates with similarity scores
- Detection reason for each match
- Usage count for each ingredient

---

### Story 2.3: Ingredient Merge

**As an** admin,
**I want** to merge duplicate ingredients into a single target,
**So that** recipes reference consistent ingredient names.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I call `POST /api/admin/ingredients/merge` with `{ source_ids: [...], target_id: "..." }`
**Then** all `recipe_ingredients` records referencing source ingredients are updated to reference the target
**And** the source ingredients are deleted
**And** I receive a response with the count of recipes affected

**Given** a merge operation is performed
**When** it completes
**Then** no recipes lose their ingredient associations
**And** the target ingredient's usage count increases by the sum of source usage counts

**Given** a source ingredient appears multiple times in the same recipe (edge case)
**When** the merge runs
**Then** duplicate references to the same target are handled gracefully (no constraint violations)

**Given** a merge operation fails mid-transaction
**When** the error occurs
**Then** the entire operation rolls back
**And** no data is modified

**Given** I try to merge with a target_id that doesn't exist
**When** I submit the request
**Then** I receive a 404 Not Found response

**Given** I try to merge with source_ids that include the target_id
**When** I submit the request
**Then** I receive a 400 Bad Request response (cannot merge ingredient into itself)

---

## Epic 3: User Account Management

Admin can view all users, activate/deactivate accounts, and grant admin privileges to trusted users.

### Story 3.1: User List & Search

**As an** admin,
**I want** to view all users with their account details and activity,
**So that** I can understand who is using the application.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/users`
**Then** I receive a paginated list of all users
**And** each user includes:
- `id`: UUID
- `email`: string
- `display_name`: string
- `is_active`: boolean
- `is_admin`: boolean
- `recipe_count`: number (count of recipes owned)
- `created_at`: timestamp
- `last_login_at`: timestamp (nullable)

**Given** I call `GET /api/admin/users?page=2&per_page=20`
**When** the response is returned
**Then** pagination is applied correctly
**And** response includes `total` count for UI pagination

**Given** I call `GET /api/admin/users?search=john`
**When** the response is returned
**Then** results are filtered by email OR display_name containing the search term

**Given** I call `GET /api/admin/users?status=active`
**When** the response is returned
**Then** only users with `is_active=true` are included

**Given** I call `GET /api/admin/users?status=inactive`
**When** the response is returned
**Then** only users with `is_active=false` are included

**Given** I am NOT an admin
**When** I call `GET /api/admin/users`
**Then** I receive a 403 Forbidden response

---

### Story 3.2: User Status Management

**As an** admin,
**I want** to activate/deactivate user accounts and manage admin privileges,
**So that** I can control access to the application.

**Acceptance Criteria:**

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_active": false }`
**Then** the user is deactivated
**And** the user's existing sessions/tokens become invalid
**And** the user cannot log in until reactivated

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_active": true }`
**Then** the user is reactivated
**And** the user can log in again

**Given** I am authenticated as an admin
**When** I try to deactivate MY OWN account
**Then** I receive a 400 Bad Request response with message "Cannot deactivate your own account"
**And** my account remains active

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_admin": true }`
**Then** the target user is granted admin privileges

**Given** I am authenticated as an admin
**When** I call `PATCH /api/admin/users/{id}` with `{ "is_admin": false }`
**Then** the target user's admin privileges are revoked

**Given** I am authenticated as an admin
**When** I try to remove MY OWN admin status
**Then** I receive a 400 Bad Request response with message "Cannot remove your own admin status"
**And** I remain an admin

**Given** a deactivated user tries to authenticate
**When** they submit valid credentials
**Then** they receive a 401 Unauthorized response with message "Account is deactivated"

**Given** I am NOT an admin
**When** I call `PATCH /api/admin/users/{id}`
**Then** I receive a 403 Forbidden response

---

## Epic 4: Audit Trail & Compliance

Admin can track all administrative actions for accountability and troubleshooting.

### Story 4.1: Audit Log Infrastructure

**As a** system,
**I want** an audit logging service that records admin actions,
**So that** all administrative changes are tracked for compliance and troubleshooting.

**Acceptance Criteria:**

**Given** the migration runs
**When** it completes
**Then** the `admin_audit_log` table is created with:
- `id`: VARCHAR(36), primary key
- `admin_user_id`: VARCHAR(36), NOT NULL (FK to users)
- `action`: VARCHAR(50), NOT NULL
- `entity_type`: VARCHAR(50), NOT NULL
- `entity_id`: VARCHAR(36), nullable
- `details`: JSON, nullable
- `created_at`: TIMESTAMP, NOT NULL

**Given** an AuditService exists
**When** `AuditService.log(action, entity_type, entity_id, details)` is called
**Then** a new audit record is created with the current admin user from context

**Given** the AuditService.log() method fails (database error, etc.)
**When** the error occurs
**Then** the error is logged to application logs
**And** the calling admin operation is NOT blocked
**And** the admin operation completes successfully (fire-and-forget)

**Given** I am authenticated as an admin
**When** I call `GET /api/admin/audit-log`
**Then** I receive a paginated list of audit entries
**And** most recent entries appear first (ordered by `created_at` DESC)

**Given** I call `GET /api/admin/audit-log?action=category_create`
**When** the response is returned
**Then** results are filtered to only that action type

**Given** I call `GET /api/admin/audit-log?entity_type=recipe`
**When** the response is returned
**Then** results are filtered to only that entity type

**Given** I call `GET /api/admin/audit-log?from=2026-01-01&to=2026-01-31`
**When** the response is returned
**Then** results are filtered to that date range

---

### Story 4.2: Audit Log Integration

**As an** admin,
**I want** all my administrative actions automatically logged,
**So that** I can review what changes were made and by whom.

**Acceptance Criteria:**

**Given** an admin performs a category action
**When** the action completes
**Then** an audit entry is created with:

| Action | entity_type | details |
| --- | --- | --- |
| `category_create` | category | {type, value, label} |
| `category_update` | category | {type, changes: {field: [old, new]}} |
| `category_delete` | category | {type, value} |

**Given** an admin performs an ingredient action
**When** the action completes
**Then** an audit entry is created with:

| Action | entity_type | details |
| --- | --- | --- |
| `ingredient_create` | ingredient | {name, type} |
| `ingredient_update` | ingredient | {changes: {field: [old, new]}} |
| `ingredient_delete` | ingredient | {name, type} |
| `ingredient_merge` | ingredient | {source_ids, source_names, target_id, target_name, recipes_updated} |

**Given** an admin performs a recipe action (on another user's recipe)
**When** the action completes
**Then** an audit entry is created with:

| Action | entity_type | details |
| --- | --- | --- |
| `recipe_admin_update` | recipe | {recipe_name, owner_id, changes: {field: [old, new]}} |
| `recipe_admin_delete` | recipe | {recipe_name, owner_id} |

**Given** an admin performs a user action
**When** the action completes
**Then** an audit entry is created with:

| Action | entity_type | details |
| --- | --- | --- |
| `user_activate` | user | {email} |
| `user_deactivate` | user | {email} |
| `user_grant_admin` | user | {email} |
| `user_revoke_admin` | user | {email} |

**Given** an audit entry is created
**When** I view it in the audit log
**Then** I can see which admin performed the action
**And** I can see the timestamp
**And** I can see what changed (old vs new values where applicable)

---

## Epic 5: Admin User Interface

Admin can access and use all administrative features through an intuitive inline interface.

### Story 5.1: Admin State & Indicator

**As an** admin user,
**I want** to see a visual indicator that I have admin privileges,
**So that** I know admin features are available to me.

**Acceptance Criteria:**

**Given** the `/api/auth/me` endpoint returns user data
**When** the response includes `is_admin: true`
**Then** the AuthContext exposes `isAdmin` boolean to all components

**Given** I am logged in as an admin
**When** I view any page
**Then** an admin badge/indicator appears in the header navigation
**And** the indicator is visually distinct but not obtrusive

**Given** I am logged in as a regular user (not admin)
**When** I view any page
**Then** no admin indicator is shown
**And** admin-only UI elements are not rendered

**Given** the admin state
**When** used in components
**Then** it can be accessed via `const { user } = useAuth(); user?.is_admin`

---

### Story 5.2: Recipe Admin Controls

**As an** admin,
**I want** to see edit and delete controls on any recipe,
**So that** I can quickly fix incorrect data without navigating to separate admin pages.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I view the recipe list/grid
**Then** each recipe card shows edit (pencil) and delete (trash) icons
**And** these icons are only visible to admins

**Given** I am logged in as an admin
**When** I click the edit icon on any recipe card
**Then** I am taken to the recipe edit page for that recipe
**And** I can edit even if I don't own the recipe

**Given** I am logged in as an admin
**When** I click the delete icon on any recipe card
**Then** a confirmation modal appears asking "Delete this recipe?"
**And** the modal shows the recipe name
**And** I must confirm before deletion proceeds

**Given** I confirm the delete action
**When** the deletion completes
**Then** the recipe is removed from the list
**And** a success toast notification appears

**Given** I am on the recipe detail page as an admin
**When** I view a recipe I don't own
**Then** an "Edit" button is visible
**And** clicking it enables inline editing of all fields

---

### Story 5.3: Category Management Modal

**As an** admin,
**I want** to manage categories directly from filter dropdowns,
**So that** I can add or modify options without leaving the current page.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I view any filter dropdown (template, glassware, method, etc.)
**Then** a "Manage" link appears at the bottom of the dropdown

**Given** I click the "Manage" link
**When** the modal opens
**Then** I see a list of ALL category values (including inactive, grayed out)
**And** the list is ordered by `sort_order`

**Given** I am in the category management modal
**When** I click "Add New"
**Then** an inline form appears for entering new category (value, label, description)
**And** the value field auto-generates snake_case from label input

**Given** I am in the category management modal
**When** I click on a category's label
**Then** I can edit the display name inline
**And** changes save on blur or Enter key

**Given** I am in the category management modal
**When** I drag a category row
**Then** I can reorder categories via drag-and-drop
**And** the new order persists when I close the modal

**Given** I click the delete button on a category
**When** the category is used by existing recipes
**Then** a warning shows the count of recipes using it
**And** I must confirm the soft-delete

**Given** I close the category management modal
**When** I return to the filter dropdown
**Then** the dropdown reflects any changes immediately (React Query invalidation)

---

### Story 5.4: Ingredient Admin Page

**As an** admin,
**I want** a dedicated page to manage ingredients with duplicate detection,
**So that** I can clean up the ingredient database efficiently.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to `/admin/ingredients`
**Then** I see a paginated table of all ingredients
**And** columns include: Name, Type, Spirit Category, Usage Count, Actions

**Given** I am on the ingredients admin page
**When** I type in the search box
**Then** the table filters by ingredient name or type
**And** filtering is debounced (300ms delay)

**Given** I click "Add Ingredient"
**When** the form modal opens
**Then** I can enter name, type (dropdown), spirit_category (conditional), description, common_brands
**And** submitting creates the ingredient and refreshes the list

**Given** I click the edit icon on an ingredient row
**When** the form modal opens
**Then** it's pre-populated with the ingredient's current values
**And** I can update and save

**Given** I click "Show Duplicates"
**When** duplicate detection completes
**Then** I see grouped lists of potential duplicates
**And** each group shows: suggested target, duplicates with similarity scores, detection reason

**Given** I select ingredients to merge and click "Merge"
**When** the merge preview modal opens
**Then** I see the target ingredient and sources to be merged
**And** I see the count of recipes that will be affected
**And** I must confirm before merge executes

**Given** the merge completes
**When** the modal closes
**Then** the ingredient list refreshes
**And** a success message shows recipes updated count

---

### Story 5.5: User Management Page

**As an** admin,
**I want** a page to view and manage all users,
**So that** I can control access and grant admin privileges.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to `/admin/users`
**Then** I see a paginated table of all users
**And** columns include: Email, Display Name, Status, Admin, Recipe Count, Created, Last Login

**Given** I am on the user management page
**When** I type in the search box
**Then** the table filters by email or display name

**Given** I am on the user management page
**When** I select a status filter (All/Active/Inactive)
**Then** the table shows only users matching that status

**Given** I click the status toggle for a user
**When** I toggle from Active to Inactive
**Then** a confirmation modal asks "Deactivate this user?"
**And** confirming deactivates the user and updates the UI

**Given** I try to deactivate my own account
**When** I click the toggle
**Then** I see an error message "Cannot deactivate your own account"
**And** my status remains unchanged

**Given** I click the admin toggle for a user
**When** I grant admin status
**Then** a confirmation modal asks "Grant admin privileges to [email]?"
**And** confirming grants admin and updates the UI

**Given** I try to remove my own admin status
**When** I click the toggle
**Then** I see an error message "Cannot remove your own admin status"
**And** my admin status remains unchanged

---

### Story 5.6: Audit Log Viewer

**As an** admin,
**I want** to view a log of all administrative actions,
**So that** I can track changes and troubleshoot issues.

**Acceptance Criteria:**

**Given** I am logged in as an admin
**When** I navigate to `/admin/audit-log`
**Then** I see a paginated table of audit entries
**And** columns include: Timestamp, Admin, Action, Entity Type, Entity ID, Details

**Given** I am on the audit log page
**When** I select an action type filter
**Then** the table shows only entries for that action type

**Given** I am on the audit log page
**When** I select an entity type filter
**Then** the table shows only entries for that entity type

**Given** I am on the audit log page
**When** I select a date range
**Then** the table shows only entries within that range

**Given** I click on an audit entry row
**When** the details panel expands
**Then** I see the full JSON details including old/new values for changes

**Given** the audit log table
**When** rendered
**Then** entries are ordered by timestamp descending (newest first)
**And** pagination allows navigating through historical entries
