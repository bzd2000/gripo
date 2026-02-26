# Gripo Missing Features — Design

## Goal

Complete the app's CRUD operations, data entry flows, and dashboard so Gripo is usable end-to-end.

## Approach

Bottom-up: fix creation flows first, enrich detail panels, then enhance dashboard.

---

## 1. Quick-Add Bars

Each tab on the subject page gets a quick-add input at the top:

- **Tasks tab**: Text input + Enter. Defaults to priority: medium, no due date.
- **Agenda tab**: Text input + Enter. Creates new agenda point.
- **Minutes tab**: Text input + Enter. Creates minutes with today's date.

Single-line input with placeholder like `+ Add task...`. On Enter, create item, clear input, item appears in list. Command palette creation stays as-is for creating from anywhere.

## 2. Task Detail Panel — Editable Fields

Expand the existing detail panel with:

- **Status selector**: Three pill buttons — todo, in-progress, done. The list checkbox stays as a quick todo/done shortcut.
- **Priority selector**: Three pill buttons — low, medium, high. Color-coded.
- **Due date picker**: `q-input` with `type="date"` and a clear button. Compact.
- **Delete button**: Soft-deletes immediately, shows undo toast for 5 seconds.

Fields go in a compact row between title and description editors. All auto-save with existing 500ms debounce.

## 3. Agenda & Minutes Detail Panels

**Agenda detail**: Add delete button with undo toast. No other changes.

**Minutes detail**: Add date picker to change meeting date. Add delete button with undo toast.

## 4. Inline Subject Editing

On the subject page header:

- **Name**: Click to edit, saves on blur or Enter.
- **Color dot**: Click to open color picker popover with ~8 preset colors.
- **Type**: Click to cycle or dropdown through project/person/team/board/other.
- **Start/End dates**: Two compact date inputs below name. "Set dates" link if none set.
- **Archive button**: Soft-archives with undo toast. Archived subjects leave sidebar.

All changes auto-save immediately.

## 5. Dashboard Enhancements

Add to existing dashboard:

- **Overdue section**: Tasks past due date, not done. Red-tinted icon. Top of grid.
- **Unresolved Agenda Points**: Cross-subject unresolved agendas via existing `loadAllUnresolved()`.
- **Section order**: Overdue, Today, This Week, Next Week, Unresolved Agendas, Pinned, Ongoing.

## 6. Undo Toast (Reusable)

- Composable `useUndoAction()` wrapping Quasar Notify.
- Dark toast, bottom-center, "Undo" action button.
- 5 second timeout. Undo reverses the action (set deleted/archived back to false).
- Used by all delete and archive operations.
