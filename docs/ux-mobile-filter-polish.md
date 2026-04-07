# UX Spec: Mobile Filter Dropdown Polish

**Author:** Sally (UX Designer)
**Date:** 2026-01-08
**Status:** Ready for Implementation

---

## Changes Requested

### 1. Add Reset Filters Button (Mobile)

The mobile filter dropdown needs a visible "Reset Filters" button. Currently there's a "Clear all" in the header that only appears when filters are active, but it's not prominent enough.

**Implementation:**

- Add a "Reset Filters" button in the dropdown footer, above the "Show Results" button
- Style as secondary/outline button to differentiate from primary "Show Results"
- Only show when `hasActiveFilters` is true (no point resetting nothing)
- On click, call the existing `clearFilters()` function

**Suggested layout:**

```
┌──────────────────────────┐
│  Filters     [Clear all] │  ← Keep existing header
│  ────────────────────────│
│  [Filter fields...]      │
│                          │
│  ┌────────────────────┐  │
│  │   Reset Filters    │  │  ← Secondary (outline amber)
│  └────────────────────┘  │
│  ┌────────────────────┐  │
│  │  Show 12 Results   │  │  ← Primary (solid amber)
│  └────────────────────┘  │
└──────────────────────────┘
```

**Styling for Reset button:**

```jsx
className="w-full py-2 px-4 border border-amber-600 text-amber-600 hover:bg-amber-50 font-medium text-sm rounded-lg transition-colors"
```

### 2. Rename "Template / Family" to "Template"

Simple label change in both variants:

- Line ~150 (mobile tile variant): `Template / Family` → `Template`
- Line ~368 (sidebar variant): `Template / Family` → `Template`

### 3. Reposition Dropdown to Top of Page

Currently the dropdown is positioned relative to the filter tile button (`absolute top-full right-0`). This puts it below the button, which can push important filters off-screen on mobile.

**New behavior:**

- Position dropdown at the top of the viewport, just below the header bar
- Use `fixed` positioning with `top` set to clear the header
- Center horizontally or keep right-aligned with padding
- This ensures all filter options are visible without scrolling

**Current (line ~98-99):**

```jsx
<div className="absolute top-full right-0 mt-2 w-72 bg-white rounded-lg shadow-lg border border-gray-200 p-4 space-y-4 z-[60]">
```

**New:**

```jsx
<div className="fixed top-16 left-4 right-4 sm:left-auto sm:right-4 sm:w-72 bg-white rounded-lg shadow-lg border border-gray-200 p-4 space-y-4 z-[60] max-h-[80vh] overflow-y-auto">
```

Notes:
- `top-16` = 64px, adjust if header is different height
- `left-4 right-4` on mobile makes it nearly full-width
- `sm:left-auto sm:right-4 sm:w-72` restores fixed width on larger screens
- `max-h-[80vh] overflow-y-auto` ensures scrolling if content overflows

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/components/recipes/FilterSidebar.tsx` | All 3 changes |

---

## Verification

1. Open app on mobile (or narrow browser window)
2. Tap Filters tile
3. Verify dropdown appears at top of screen, under header
4. Verify "Template" label (not "Template / Family")
5. Apply a filter, verify "Reset Filters" button appears
6. Tap Reset Filters, verify all filters clear
7. Verify "Show Results" still works to close dropdown
8. Test on desktop sidebar - verify "Template" label there too

---

## Dev Handoff

In a fresh session:

```
/bmad:bmm:agents:dev

Implement the UX changes in docs/ux-mobile-filter-polish.md
```
