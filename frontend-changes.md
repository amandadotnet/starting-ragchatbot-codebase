# Frontend Changes: Sidebar Toggle Button

## Summary

Added a toggle button that collapses/expands the left sidebar (Courses stats + Suggested Questions), so users can reclaim horizontal space for the chat area. Collapsed state persists across page reloads via `localStorage`.

## Files changed

- `frontend/index.html`
- `frontend/style.css`
- `frontend/script.js`

## Details

### index.html
- Gave `.main-content` and `.sidebar` `id`s (`mainContent`, `sidebar`) so JS can target them.
- Added a `#sidebarToggle` button (chevron-left SVG icon) as a sibling of `.sidebar`, inside `.main-content`, so it stays visible even when the sidebar collapses.
- Bumped cache-busting query params (`style.css?v=10`, `script.js?v=10`).

### style.css
- `.main-content` is now `position: relative` so the toggle button can be absolutely positioned relative to it.
- `.sidebar` gained a transition on `width`, `padding`, and `opacity` for a smooth collapse animation, plus `overflow-x: hidden` to avoid content spilling out mid-transition.
- New `.main-content.sidebar-collapsed .sidebar` rule collapses the sidebar to `width: 0` with no padding/opacity, and disables pointer events.
- New `.sidebar-toggle` styles: a small circular button pinned to the top edge of the sidebar, sitting on the boundary between sidebar and chat. Its icon rotates 180° when collapsed to flip from "collapse" to "expand" affordance.
- Responsive tweaks: toggle button's `left` offset adjusted at the 1024px breakpoint (matches the narrower 280px sidebar), and hidden entirely below 768px, where the sidebar already stacks above the chat instead of sitting beside it.

### script.js
- Cached `mainContent` and `sidebarToggle` DOM references on load.
- Added `initSidebarState()` — reads `sidebarCollapsed` from `localStorage` on page load and applies it.
- Added `toggleSidebar()` — flips the collapsed state on click.
- Added `setSidebarCollapsed(collapsed)` — single source of truth that toggles the `sidebar-collapsed` class on `#mainContent`, updates the button's `aria-expanded` attribute, and persists the choice to `localStorage`.
- Wired `sidebarToggle`'s click event in `setupEventListeners()`.

## Notes

- Accessibility: button has `aria-label="Toggle sidebar"` and `aria-expanded` is kept in sync with state.
- No backend changes were needed for this feature.
