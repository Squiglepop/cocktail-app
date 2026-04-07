# UX Spec: Mobile Filter Dropdown Improvements

**Author:** Sally (UX Designer)
**Date:** 2026-01-08
**Status:** Ready for Implementation

---

## Problem Statement

On mobile, the filter dropdown in `FilterSidebar.tsx` (tile variant) has a critical usability issue:

- The dropdown is **288px wide** on a ~375px screen (76% of viewport)
- The **only dismiss mechanism** is tapping outside the dropdown
- This leaves only ~45px margins on each side — nearly impossible to tap accurately
- Users get "trapped" in the filter panel with no clear way to close it and see results

**User impact:** Frustration, accidental taps on recipe cards beneath, poor mobile experience.

---

## Solution Overview

Implement **two complementary UX patterns**:

1. **Backdrop/Scrim** — Semi-transparent overlay behind dropdown that provides a large tap target for dismissal
2. **"Show X Results" Button** — Explicit action button at dropdown bottom that closes and shows filtered count

---

## Design Specifications

### 1. Backdrop Scrim

**Visual:**
```
┌─────────────────────────────────┐
│  [Header]                       │
├─────────────────────────────────┤
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │  ← Dark overlay (bg-black/50)
│ ░░░░░░░░░┌──────────────┐░░░░░░ │     Tapping here closes dropdown
│ ░░░░░░░░░│   Filters    │░░░░░░ │
│ ░░░░░░░░░│   [Fields]   │░░░░░░ │
│ ░░░░░░░░░│              │░░░░░░ │
│ ░░░░░░░░░│ ┌──────────┐ │░░░░░░ │
│ ░░░░░░░░░│ │Show 12   │ │░░░░░░ │
│ ░░░░░░░░░│ │Results   │ │░░░░░░ │
│ ░░░░░░░░░│ └──────────┘ │░░░░░░ │
│ ░░░░░░░░░└──────────────┘░░░░░░ │
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ │
└─────────────────────────────────┘
```

**Implementation:**
- Position: `fixed inset-0`
- Background: `bg-black/50` (50% opacity black)
- Z-index: `z-[55]` (below dropdown at z-[60], above page content)
- Behavior: Clicking scrim calls `setIsExpanded(false)`
- Only render when `isExpanded && variant === 'tile'`

### 2. "Show X Results" Button

**Location:** Bottom of the dropdown content area, inside the dropdown container.

**Button States:**

| Condition | Button Text |
|-----------|-------------|
| Has `resultCount` | `Show {resultCount} Results` |
| `resultCount === 1` | `Show 1 Result` |
| `resultCount === 0` | `No Results` (still closeable) |
| No count provided | `Show Results` |

**Styling:**
- Full width: `w-full`
- Amber theme: `bg-amber-600 hover:bg-amber-700 text-white`
- Rounded: `rounded-lg`
- Padding: `py-2.5 px-4`
- Font: `font-medium text-sm`
- Margin top: `mt-4` to separate from last filter
- Optional: subtle top border or shadow to create visual separation

**Behavior:**
- On click: `setIsExpanded(false)` — closes dropdown

---

## Props Changes

**File:** `frontend/components/recipes/FilterSidebar.tsx`

Add new optional prop:

```typescript
interface FilterSidebarProps {
  filters: { /* existing */ };
  onFilterChange: (filters: FilterSidebarProps['filters']) => void;
  className?: string;
  variant?: 'sidebar' | 'tile';
  disabled?: boolean;
  resultCount?: number;  // NEW: Count of filtered results to display
}
```

**File:** `frontend/app/page.tsx`

Pass the count to the mobile FilterSidebar:

```tsx
<FilterSidebar
  filters={filters}
  onFilterChange={setFilters}
  variant="tile"
  disabled={!isOnline}
  resultCount={recipeCount?.filtered}  // NEW
/>
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/components/recipes/FilterSidebar.tsx` | Add backdrop, add button, accept `resultCount` prop |
| `frontend/app/page.tsx` | Pass `resultCount` prop to mobile FilterSidebar |

---

## Implementation Notes

1. **Backdrop should be a sibling to dropdown**, not a parent — keeps click handling simple
2. **Existing click-outside logic** (lines 31-43) can remain; the backdrop just gives it a bigger target
3. **No changes to desktop sidebar** — only affects `variant="tile"` (mobile)
4. **Filters still apply immediately** — button is purely for closing, not for "applying"

---

## Acceptance Criteria

- [ ] When filter dropdown opens on mobile, a semi-transparent backdrop appears
- [ ] Tapping backdrop closes the dropdown
- [ ] "Show X Results" button appears at bottom of dropdown
- [ ] Button displays correct filtered count when available
- [ ] Button closes dropdown when tapped
- [ ] Desktop sidebar is unaffected
- [ ] No visual regressions on existing filter functionality

---

## Dev Handoff Command

In a fresh session:

```
/bmad:bmm:agents:dev

Implement the UX changes in docs/ux-mobile-filter-improvements.md
```
