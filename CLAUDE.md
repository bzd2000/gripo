# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Terminal-based personal productivity TUI called "Tracker" — task tracking, delegation tracking, open points, and running notes organized by **subjects**. Built with Python + Textual + SQLite.

## Commands

```bash
# Install dependencies
pip install -e .

# Run the app
python -m tracker
# or after install:
tt

# Run with Textual dev console (for debugging CSS/events)
textual run --dev tracker.app:TrackerApp

# Run tests
pytest

# Run a single test
pytest tests/test_db_tasks.py::test_add_task -v
```

## Architecture

### Layout
Horizontal split: `NavTree` (left, ~25%) + `ContentArea` (right, ~75%). The tree drives navigation at 3 levels: top-level views (Today, This Week) → subject sections (Tasks, Open Points, etc.) → individual items. The right pane swaps content based on tree selection. Inline forms replace modal screens for all input (except delete confirmations, search, and help which remain as modals).

### Data flow
All state lives in SQLite (`~/.tracker/tracker.db`). The `Database` class (`tracker/db.py`) wraps `sqlite3` with CRUD methods for each entity. Widgets call `Database` methods directly, then refresh via Textual's message system. After mutations, a custom `DataChanged` message notifies the tree and content area to refresh.

### Message flow
- `ShowContent(content_type, data)` — posted by NavTree or list widgets to request content pane change. Bubbles up to TrackerApp which forwards to ContentArea.
- `ContentSaved(content_type, data)` — posted by forms after save. ContentArea navigates back to parent list.
- `ContentCancelled()` — posted by forms on Escape. Same navigation.
- `DataChanged()` — posted after any DB mutation. Tree refreshes, content refreshes.

**Important**: Textual messages bubble UP (child → parent). NavTree and ContentArea are siblings inside a Horizontal container, so ShowContent from NavTree never reaches ContentArea directly. TrackerApp catches it and forwards.

### Key modules
- `tracker/app.py` — `TrackerApp` root with NavTree + ContentArea split
- `tracker/db.py` — `Database` class, schema init, all SQL queries
- `tracker/models.py` — dataclasses mapping SQLite rows (Subject, Task, OpenPoint, FollowUp, Note)
- `tracker/messages.py` — DataChanged, ShowContent, ContentSaved, ContentCancelled
- `tracker/widgets/nav_tree.py` — 3-level navigation tree
- `tracker/widgets/content_area.py` — right pane container, widget factory
- `tracker/widgets/*_form.py` — inline forms (task, open point, follow-up, subject)
- `tracker/widgets/note_editor.py` — markdown note editor
- `tracker/widgets/subject_overview.py` — subject dashboard
- `tracker/widgets/*_list.py` — list widgets for each entity type
- `tracker/widgets/date_input.py` — reusable date input with arrow key navigation
- `tracker/screens/` — confirm, search, help (kept as modals)
- `tracker/tracker.tcss` — all Textual CSS styling

### Data model
Six main tables: `subjects`, `tasks`, `open_points`, `follow_ups`, `notes`, plus a `meta` table for app state. Subjects are the primary organizing unit — all other entities reference a subject via foreign key. All deletes are soft deletes (`deleted_at` column, never use SQL DELETE). Tasks, open points, and follow-ups have a `comment` TEXT field (markdown).

## Textual Layout Reference

Reference: https://textual.textualize.io/guide/layout/

### Core rules

1. **Three layout modes**: `vertical` (default for Screen, stacks top-to-bottom), `horizontal` (left-to-right), `grid` (cell-based)
2. **Width default**: widgets expand to fill parent width automatically
3. **Height default**: widgets do NOT auto-fill parent height. You must explicitly set `height: 100%` or `height: 1fr`
4. **Fractional units (`fr`)**: distribute remaining space proportionally. `1fr` = equal share of leftover space after fixed-size siblings are laid out

### Height chain rule

For a widget deep in the tree to use `height: 1fr`, **every ancestor must also have an explicit height**. If any parent has `height: auto`, the `1fr` child collapses to zero.

```
Screen (height: 100% by default) ✓
  → Horizontal (needs height: 1fr or 100%) ✓
    → Container (needs height: 1fr or 100%) ✓
      → Widget (needs height: 1fr) ✓
        → Vertical (needs height: 1fr or 100%) ✓
          → TextArea (height: 1fr works!) ✓
```

Break any link in this chain and `1fr` stops working.

### Sizing units
- `42` — fixed cells (columns for width, rows for height)
- `50%` — percentage of parent
- `1fr` — fractional share of remaining space
- `auto` — fit content (height only, collapses 1fr children)
- `100vw` / `100vh` — viewport percentage

### Common patterns

**Fill remaining space** (e.g., TextArea at bottom of form):
```css
.form-container {
    height: 1fr;  /* Must fill parent */
}
.fill-remaining {
    height: 1fr;  /* Gets all remaining space */
}
```

**Side-by-side fields**:
```css
.field-row {
    layout: horizontal;
    height: auto;  /* Fit tallest child */
}
.field-row > * {
    width: 1fr;  /* Equal width */
}
```

**Scroll when content overflows**:
- Vertical scroll: automatic in vertical layout
- Horizontal scroll: requires explicit `overflow-x: auto`

### CSS specificity (3-tier)
1. ID selectors (highest): `#my-widget`
2. Class selectors (middle): `.my-class`, `:hover` counts as a class
3. Type selectors (lowest): `Input`, `TextArea`

`DEFAULT_CSS` in widget classes has automatically lower specificity than app CSS. Later rules of equal specificity win (cascade).

### Gotchas
- `height: auto` on a container means `1fr` children inside it get zero space
- Textual Input/Select default to single-line height. No need to set `height: 1` explicitly.
- `box-sizing: border-box` is default — padding/borders subtract from declared dimensions
- Docked widgets (`dock: top/left/etc`) are removed from normal flow
- Use `Vertical`, `Horizontal`, `Grid` container classes — they come pre-configured with the right layout mode

## Tech Constraints

- Python 3.10+ required
- Only external dependency is `textual` — SQLite uses stdlib `sqlite3`
- Enable WAL mode and foreign keys on every DB connection
- Database auto-creates at `~/.tracker/tracker.db` on first run
- Use `uuid` from stdlib for ID generation
- All deletes are soft deletes — no SQL DELETE anywhere
- Entry point: `python -m tracker` via `__main__.py`, or `tt` console script
- Windows compatible: `pathlib.Path` everywhere, no hardcoded separators
