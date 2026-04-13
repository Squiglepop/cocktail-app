---
title: Admin Panel User Manual
description: Complete guide to all administrative features in Cocktail Shots
author: Paige (Technical Writer Agent)
date: 2026-04-10
---

# Admin Panel User Manual

This manual covers every administrative feature in Cocktail Shots. You will learn how to identify your admin status, manage recipes, categories, ingredients, users, and review the audit trail.

---

## Table of Contents

1. [Admin Indicator](#1-admin-indicator)
2. [Recipe Admin Controls](#2-recipe-admin-controls)
3. [Category Management](#3-category-management)
4. [Ingredient Management](#4-ingredient-management)
5. [User Management](#5-user-management)
6. [Audit Log Viewer](#6-audit-log-viewer)
7. [Security and Access Control](#7-security-and-access-control)
8. [Quick Reference](#8-quick-reference)

---

## 1. Admin Indicator

### How You Know You Are an Admin

When you log in with an admin account, a small **amber "Admin" badge** appears in the header navigation, next to your display name. This badge is visible on every page throughout the application.

- The badge uses amber/gold tones (`bg-amber-100 text-amber-800`) to be visually distinct without being obtrusive.
- Screen readers announce it as "Administrator account" via the `aria-label` attribute.
- Regular users see no badge and no admin-specific controls anywhere in the UI.

### How Admin Status Is Assigned

The first user to register on a new Cocktail Shots installation automatically becomes the admin. After that, only existing admins can grant admin privileges to other users (see [User Management](#5-user-management)).

### Accessing Admin State in Code

Admin status flows through the `AuthContext`. Any component can check it:

```typescript
const { user } = useAuth();
if (user?.is_admin) {
  // Render admin controls
}
```

---

## 2. Recipe Admin Controls

Admins can edit and delete **any** recipe in the system, regardless of who owns it. These controls appear inline alongside the regular UI, keeping everything seamless.

### Recipe Card Controls

When you browse the recipe grid as an admin:

- **Edit icon** (pencil) and **Delete icon** (trash) appear at the **bottom-right of each recipe card's image area**.
- On desktop, these icons reveal on hover. On mobile, they are always visible.
- Clicking the pencil navigates to `/recipes/{id}/edit`.
- Clicking the trash opens a confirmation modal (see below).

Regular users see no edit or delete icons on cards.

### Recipe Detail Page

When viewing a recipe detail page as an admin:

- The **Edit**, **Add Images**, and **Delete** buttons appear in the action bar, even for recipes you do not own.
- These are the same buttons an owner sees. Admin access simply broadens the permission check.

### Recipe Edit Page

Navigating to `/recipes/{id}/edit` as an admin grants full edit access to any recipe:

- All text fields: name, description, instructions, notes, garnish
- All category assignments: template, glassware, method, serving style, main spirit
- Ingredients: add, remove, or modify
- No "Access Denied" page appears for non-owned recipes

The backend already handles the admin ownership bypass, so saves work identically to owner edits.

### Delete Confirmation Modal

All recipe deletions (by owners and admins alike) go through a **confirmation modal** instead of the browser's native `confirm()` dialog:

- **Title:** "Delete this recipe?"
- **Body:** "Are you sure you want to delete **{recipe name}**? This cannot be undone."
- **Warning icon:** Red `AlertTriangle` icon
- **Buttons:** Cancel (gray) and Delete (red)
- While deleting, the button shows "Deleting..." with a spinner and is disabled
- The Cancel button remains clickable during deletion so you can bail out of hanging requests
- On success, the recipe disappears from the grid automatically (no separate toast or notification)

### What Happens on Delete

- The recipe is **hard deleted** from the database, including associated images
- Recipe ingredients are cascaded (deleted along with the recipe)
- The deletion is recorded in the [Audit Log](#6-audit-log-viewer)

---

## 3. Category Management

Categories are the filter options that organize recipes: **Templates** (Sour, Old Fashioned, Martini, etc.), **Main Spirit** (Gin, Vodka, Rum, etc.), **Glassware**, **Serving Style**, and **Method**. Admins can add, rename, reorder, and deactivate these values.

### Accessing Category Management

1. Go to any page that shows the recipe filter sidebar (the main recipe list page).
2. Below each category dropdown, you will see a small amber **"Manage"** link with a gear icon.
3. Click "Manage" to open the Category Management Modal for that category type.

Regular users do not see the "Manage" links.

Both the desktop sidebar and the mobile tile layout include these links.

### The Category Management Modal

The modal displays a full list of all category values for the selected type, ordered by sort position.

**Header:** "Manage {Category Type}" with an X close button.

**Category list:** Each row shows:

| Element | Description |
|---------|-------------|
| Label | The display name (clickable for inline editing) |
| Value | Snake_case internal identifier (shown in small gray text) |
| Category | Glassware only: stemmed, short, tall, or specialty |
| Up/Down arrows | Reorder buttons (ChevronUp / ChevronDown icons) |
| Pencil icon | Appears on hover, triggers inline label editing |
| Trash icon | Appears on hover, soft-deletes the category |

**Inactive items** appear grayed out with strikethrough text. The trash icon is hidden on already-inactive items.

**Footer:** A "Done" button closes the modal.

### Adding a New Category

1. Click the **"Add New"** button at the top of the category list.
2. An inline form appears with:
   - **Label** text input (required) -- the user-facing display name
   - **Value preview** (read-only) -- auto-generated snake_case from the label, e.g., "Dark Rum" becomes `dark_rum`
   - **Description** text input (optional)
   - **Category dropdown** (glassware type only) -- stemmed, short, tall, or specialty
3. Click **Save** to create, or **Cancel** to discard.

**Validation rules:**

- The generated value must start with a letter and match the pattern `^[a-z][a-z0-9_]*$`
- If the label produces an empty or invalid value (e.g., all digits), the Save button is disabled and an inline error appears: "Label must contain at least one letter"
- If the value already exists, the API returns a 409 error and you see: "Category value already exists"

On success, the new category appears at the end of the list.

### Editing a Category Label

1. Click on any category's label text.
2. The text converts to an input field.
3. Edit the label and press **Enter** or click away (blur) to save.
4. Press **Escape** to cancel and revert to the original.

Only the display label is editable. The internal `value` is immutable after creation.

### Reordering Categories

- Click the **up arrow** to move a category higher in the list.
- Click the **down arrow** to move it lower.
- The first item's up arrow is disabled. The last item's down arrow is disabled.
- Buttons are disabled during the reorder API call to prevent double-clicks.
- The new order is saved immediately via the reorder endpoint.

### Deactivating (Soft-Deleting) a Category

1. Click the **trash icon** on any active category row.
2. The category is immediately soft-deleted (no confirmation modal -- this is reversible).
3. An inline message appears: **"{value} deactivated. {N} recipes affected."**
4. The item stays in the list but appears grayed out.

Deactivated categories no longer appear in public filter dropdowns but remain visible in the admin modal.

### Filter Dropdown Refresh

When you close the Category Management Modal, the public category data is automatically refreshed. Filter dropdowns reflect your changes immediately.

---

## 4. Ingredient Management

The ingredient admin page provides full CRUD for the ingredient master list, plus duplicate detection and merge capabilities.

### Accessing the Ingredients Page

Navigate to **`/admin/ingredients`** directly. You must be logged in as an admin; otherwise, you are redirected to the home page.

### Page Layout

The page title is **"Ingredient Management"** with an **"Add Ingredient"** button (amber, with a `+` icon) at the top-right.

Below the title:

- **Search box** -- filters by ingredient name with a 300ms debounce
- **Type dropdown** -- filters by ingredient type (spirit, liqueur, syrup, juice, etc.)

### Ingredient Table

| Column | Description |
|--------|-------------|
| Name | Ingredient name (e.g., "Raspberry Liqueur") |
| Type | Category type (spirit, liqueur, syrup, mixer, etc.) |
| Spirit Category | Shown only for spirit-type ingredients (gin, vodka, rum, etc.) |
| Actions | Edit (pencil) and Delete (trash) icons, visible on row hover |

The table is paginated with Previous/Next buttons (chevron icons) and a page indicator.

### Adding an Ingredient

1. Click **"Add Ingredient"** to open the form modal.
2. Fill in the fields:
   - **Name** (required) -- the ingredient name
   - **Type** (required) -- dropdown selection
   - **Spirit Category** -- appears only when Type is "spirit"
   - **Description** (optional)
   - **Common Brands** (optional)
3. Click **Save** to create.

If the name already exists (case-insensitive), you see: **"Ingredient name already exists"** (409 error).

### Editing an Ingredient

1. Click the **pencil icon** on any ingredient row.
2. The form modal opens pre-populated with the ingredient's current values.
3. Edit any field and click **Save**.

### Deleting an Ingredient

1. Click the **trash icon** on an ingredient row.
2. **If the ingredient is not used in any recipe:** A confirmation modal appears. Confirm to permanently delete it.
3. **If the ingredient is in use:** The delete is blocked with the message: **"Cannot delete: used in {N} recipes"** shown as a red dismissible banner.

### Duplicate Detection

Below the ingredient table, a **Duplicate Detection Panel** helps you find and merge duplicate ingredients.

1. Click **"Show Duplicates"** to run detection.
2. Results appear as grouped lists of potential duplicates. Each group shows:
   - **Suggested target** -- the ingredient with the highest usage count (recommended merge destination)
   - **Potential duplicates** -- each with a similarity score and detection reason:
     - `exact_match_case_insensitive` -- same name, different case (e.g., "Lime Juice" vs "lime juice")
     - `fuzzy_match` -- similar names with >80% similarity (Levenshtein distance)
     - `variation_pattern` -- common variations (e.g., "Fresh Lime" vs "Lime")

### Merging Ingredients

1. In a duplicate group, click **"Merge"**.
2. A **merge preview modal** opens showing:
   - The **target ingredient** (merge destination)
   - The **source ingredients** that will be absorbed
   - The **count of recipes** that will be updated
3. Confirm to execute the merge.
4. On success:
   - All recipe references are updated from source ingredients to the target
   - Source ingredients are permanently deleted
   - A success message shows the count of recipes updated
   - The ingredient list refreshes automatically

---

## 5. User Management

The user management page gives you a complete view of all registered users with controls to activate, deactivate, and grant or revoke admin privileges.

### Accessing the Users Page

Navigate to **`/admin/users`** directly. Non-admins are redirected to the home page.

### Page Layout

The page shows:

- **Search box** -- filters by email or display name with a 300ms debounce
- **Status filter tabs** -- three options: All, Active, Inactive
- **User table** (see below)
- **Pagination** -- Previous/Next buttons with a page indicator and total count

### User Table

| Column | Description |
|--------|-------------|
| Email | Primary user identifier |
| Display Name | User's display name, or "---" if not set |
| Status | Clickable toggle badge: green "Active" (with UserCheck icon) or red "Inactive" (with UserX icon) |
| Admin | Clickable toggle badge: purple "Admin" (with Shield icon) or gray "User" (with ShieldOff icon) |
| Recipes | Count of recipes owned by this user |
| Created | Account creation date |
| Last Login | Last login timestamp, or "Never" if the user has never logged in |

### Toggling User Status (Active / Inactive)

1. Click the status badge on any user row.
2. A **confirmation modal** appears:
   - **Deactivating:** Title "Deactivate this user?", red styling (danger variant)
   - **Activating:** Title "Activate this user?", default styling
3. Confirm to apply the change. The table updates immediately.

**When a user is deactivated:**

- They can no longer log in
- All their existing refresh tokens are revoked (handled server-side)
- Their recipes remain in the system

### Toggling Admin Status

1. Click the admin badge on any user row.
2. A **confirmation modal** appears:
   - **Granting:** Title "Grant admin privileges to {email}?", amber styling (warning variant)
   - **Revoking:** Title "Revoke admin privileges from {email}?", amber styling (warning variant)
3. Confirm to apply the change.

### Self-Protection Rules

You cannot modify your own account through this interface:

- **Attempting to deactivate yourself** shows: "Cannot deactivate your own account"
- **Attempting to remove your own admin status** shows: "Cannot remove your own admin status"

These checks are enforced both client-side (immediate feedback) and server-side (400 error as safety net).

### Accessibility

- Toggle controls use `role="switch"` with `aria-checked` and descriptive `aria-label` values
- Status badges use `role="status"` for screen reader announcements
- Error messages are wrapped in `aria-live="polite"` regions

---

## 6. Audit Log Viewer

The audit log provides a complete, chronological record of every administrative action taken in the system. It is read-only.

### Accessing the Audit Log

Navigate to **`/admin/audit-log`** directly. Non-admins are redirected to the home page.

### Page Layout

The page title is **"Audit Log"** with a filter bar and paginated table.

### Filters

| Filter | Type | Description |
|--------|------|-------------|
| Action | Dropdown | Filter by specific action type (see table below) |
| Entity Type | Dropdown | Filter by entity: category, ingredient, recipe, or user |
| From | Date input | Start date for the range (inclusive) |
| To | Date input | End date for the range (inclusive) |
| Clear Filters | Button | Resets all filters and returns to page 1 |

Changing any filter automatically resets the page to 1.

### Audit Log Table

| Column | Description |
|--------|-------------|
| Timestamp | Date and time of the action (formatted as locale date+time) |
| Admin | Email of the admin who performed the action (falls back to user ID if email is unavailable) |
| Action | Human-readable action name (e.g., "Category Create") |
| Entity Type | Human-readable entity type (e.g., "Ingredient") |
| Entity ID | UUID of the affected entity (truncated with "..." for long IDs), or "---" if null |
| Details | Expand/collapse chevron (triangular arrow) |

Entries are ordered **newest first** (descending timestamp).

### Expandable Details

Click any row (or the chevron icon) to expand it. The expanded section shows the full JSON details of the action, formatted with indentation:

```json
{
  "type": "templates",
  "value": "tiki",
  "label": "Tiki"
}
```

Click the row again to collapse the details. Rows with `null` details show no expanded content.

### All Tracked Actions

| Action | Entity Type | Details Captured |
|--------|-------------|-----------------|
| `category_create` | category | type, value, label |
| `category_update` | category | type, field changes (old/new values) |
| `category_delete` | category | type, value |
| `ingredient_create` | ingredient | name, type |
| `ingredient_update` | ingredient | field changes (old/new values) |
| `ingredient_delete` | ingredient | name, type |
| `ingredient_merge` | ingredient | source IDs, source names, target ID, target name, recipes updated |
| `recipe_admin_update` | recipe | recipe name, owner ID, field changes |
| `recipe_admin_delete` | recipe | recipe name, owner ID |
| `user_activate` | user | email |
| `user_deactivate` | user | email |
| `user_grant_admin` | user | email |
| `user_revoke_admin` | user | email |

### Pagination

The audit log displays **20 entries per page**. Navigate using Previous/Next buttons with a "Page X of Y" indicator.

---

## 7. Security and Access Control

### Route Protection

All admin pages under `/admin/*` are protected by a shared layout component:

- While authentication is loading, a spinner is displayed
- If the user is not logged in or not an admin, they are immediately redirected to `/`
- The page content is not rendered until admin status is confirmed

### Backend Authorization

Every admin API endpoint is protected by the `require_admin` dependency:

- Non-authenticated requests receive a **401** response
- Authenticated non-admin users receive a **403** response with "Admin access required"

### Rate Limiting

Admin endpoints are rate-limited to prevent abuse:

- Most admin endpoints: **10 requests per minute**
- Audit log (read-heavy): **30 requests per minute**

### Audit Trail

All administrative actions are automatically logged with:

- The admin who performed the action
- The action type and affected entity
- A JSON snapshot of relevant details (old/new values for updates)
- A timestamp

Audit logging uses a **fire-and-forget pattern**: if logging fails, the admin operation still succeeds. This ensures that audit infrastructure issues never block legitimate admin work.

---

## 8. Quick Reference

### Admin Page URLs

| Page | URL |
|------|-----|
| Ingredient Management | `/admin/ingredients` |
| User Management | `/admin/users` |
| Audit Log | `/admin/audit-log` |
| Category Management | Via "Manage" links on filter dropdowns (modal, not a page) |

### Keyboard Shortcuts

| Context | Key | Action |
|---------|-----|--------|
| Any modal | `Escape` | Close the modal |
| Inline label edit (categories) | `Enter` | Save the edit |
| Inline label edit (categories) | `Escape` | Cancel the edit |

### Data Caching

Admin views use a **1-minute cache** (stale time) for faster data display with frequent refreshes. Regular user views use a 5-minute cache for stable data. Category management modal invalidates the public category cache on close, so filter dropdowns always reflect the latest changes.

### Common Error Messages

| Message | Meaning |
|---------|---------|
| "Category value already exists" | The snake_case value conflicts with an existing category |
| "Ingredient name already exists" | Duplicate ingredient name (case-insensitive) |
| "Cannot delete: used in {N} recipes" | Ingredient is referenced by recipes and cannot be removed |
| "Cannot deactivate your own account" | Self-protection: you cannot lock yourself out |
| "Cannot remove your own admin status" | Self-protection: you cannot revoke your own admin role |
| "Admin access required" | You are authenticated but not an admin (403) |
