# Admin Panel Brief

**Author:** Deemo (with Sally, UX Designer)
**Date:** 2026-01-08
**Status:** Ready for Analyst Review

---

## Vision

Add administrative capabilities to the Cocktail Library app, allowing the owner to manage database content and users directly through the existing UI.

---

## Core Requirements

### 1. Category Management

- Add/edit/delete items in: Spirits, Methods, Glassware, Serving Styles, Templates
- Currently these are enums — need to become database-driven
- Changes reflect immediately in filter dropdowns

### 2. Recipe Management

- Edit existing recipes inline (click to edit mode)
- Delete recipes (with confirmation)
- Bulk operations? (optional — delete multiple, export)

### 3. User Management (Basic)

- View list of registered users
- Add new users (invite by email?)
- Delete/deactivate users
- *Not* full role-based permissions — single admin model

---

## UX Approach

**Inline editing** — Admin controls appear contextually on existing pages when logged in as admin, rather than a separate admin portal.

Examples:
- Edit pencil icon on recipe cards/detail pages
- "Manage" link next to filter dropdowns
- User list accessible from profile/settings

---

## Single Admin Model

- One admin account (the owner)
- Simple authentication check, no complex permissions
- Future-proof: could add roles later if needed

---

## Open Questions for Analyst

1. Should categories become fully database-driven, or stay as enums with an "Other" option?
2. What's the migration path for existing enum data?
3. User auth — is there existing auth in the app, or does this need to be built?
4. What audit/logging is needed for admin actions?

---

## Analyst Handoff

```
/bmad:bmm:agents:analyst

Review the admin panel brief in docs/admin-panel-brief.md and help refine requirements
```
