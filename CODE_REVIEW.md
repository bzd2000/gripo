# Code Review — Tracker TUI

Reviewed: 2026-04-13

## Must Fix

### 1. `update_task` cannot clear category to None
**File**: `tracker/db.py` (`update_task` method)

Uses `if category is not None` instead of the `_SENTINEL` pattern. Once a task has a category, it can never be cleared back to blank through the form.

**Fix**: Use `_SENTINEL` for `category` like `due_date` and `comment`.

### 2. `DateInput` defaults empty string to today
**File**: `tracker/widgets/date_input.py`

```python
initial = value if value else date.today().isoformat()
```

Passing `value=""` (which happens for records without a due date) pre-fills today's date instead of leaving the field blank.

**Fix**: `initial = value if value is not None else date.today().isoformat()`

### 3. `ContentArea.show()` shadows Textual's `Widget.show()`
**File**: `tracker/widgets/content_area.py`

Textual's `Widget` has a built-in `show()` method (counterpart to `hide()`). Our method replaces content instead. If any code ever calls `content_area.show()` expecting Textual behavior, it will break.

**Fix**: Rename to `set_content()` or `display_widget()`.

## Should Fix

### 4. Open point / follow-up save uses multiple commits
**Files**: `tracker/widgets/open_point_form.py`, `tracker/widgets/follow_up_form.py`

Each field update is a separate `conn.commit()`. If the app crashes mid-save, data is partially written. Contrast with `soft_delete_subject` which correctly uses a transaction.

**Fix**: Add `update_open_point()` and update `update_follow_up()` methods that save all fields in a single transaction.

### 5. `DateInput._on_key` uses private Textual API
**File**: `tracker/widgets/date_input.py`

The `_on_key` method (underscore prefix) is Textual's internal handler. This is fragile across Textual versions.

**Fix**: Use `on_key` instead and call `super().on_key(event)` for defaults.

### 6. `ON DELETE CASCADE` contradicts soft-delete design
**File**: `tracker/db.py` (schema)

All child tables use `REFERENCES subjects(id) ON DELETE CASCADE`. Since the project never hard-deletes, this is dormant but creates a trap: anyone hard-deleting a subject row via SQL would cascade-delete all children.

**Fix**: Change to `ON DELETE RESTRICT`.

### 7. SearchScreen / HelpScreen lack modal-dialog CSS
**Files**: `tracker/screens/search.py`, `tracker/screens/help.py`

These modals render full-screen without borders or padding. `ConfirmScreen` correctly uses `.modal-dialog`.

**Fix**: Wrap content in `Vertical(classes="modal-dialog")`.

## Nice to Have

### 8. Duplicated code across files
- `_ItemList` class defined in `overview_view.py`, `milestone_view.py` (was also in deleted `subject_overview.py`)
- Status/priority icon dicts (`_TASK_STATUS_ICON`, `_FU_STATUS_ICON`, `_STATUS_CYCLE`, `_PRIORITY_CYCLE`) repeated in 4+ files

**Fix**: Extract to `tracker/widgets/shared.py` or `tracker/constants.py`.

### 9. Bare `except Exception: pass` throughout
**Files**: `app.py`, `content_area.py`, `task_form.py`, `milestone_view.py`

Silently swallows all errors including data loss. Should catch specific `NoMatches` from Textual for widget queries.

### 10. Type hints use `Optional[str]` instead of `str | None`
**Files**: `models.py`, `db.py`

Project targets Python 3.10+ and already imports `from __future__ import annotations`. Can use modern `str | None` syntax.

---

## Deep Review (2026-04-13)

### Critical

### 11. FollowUpForm `asked_on` is editable but never saved
**File**: `tracker/widgets/follow_up_form.py`

The form renders an editable `DateInput` for `asked_on`, but `action_save` never reads it. On create, the DB default `date('now')` is used regardless. On edit, `update_follow_up` only updates `text`, `owner`, and `due_by`. User changes to `asked_on` are silently discarded.

**Fix**: Read the `asked_on` value in `action_save` and pass it to the DB methods, or make the field read-only when editing.

### 12. Tree expansion preservation is broken
**File**: `tracker/widgets/nav_tree.py` (`_collect_expanded_paths` / `_restore_expanded_paths`)

Path matching uses display labels that include dynamic counts, e.g., `/Overview (1 today, 5 week)/People/Alice/Tasks (3)`. After any mutation, counts change, paths don't match, and all expanded sections collapse. The expansion preservation code is effectively a no-op.

**Fix**: Use stable identifiers for path matching (e.g., `data["id"]` values) instead of display labels.

### 13. `get_task` and `get_subject` return soft-deleted records
**File**: `tracker/db.py` (`get_task`, `get_subject`)

Missing `AND deleted_at IS NULL` filter, unlike `get_open_point`, `get_follow_up`, and `get_milestone` which all filter soft-deleted records. A stale tree node referencing a deleted task will load it for editing, creating ghost records that are modified but never visible in any list.

**Fix**: Add `AND deleted_at IS NULL` to both queries.

### Important

### 14. Archived subjects leak into Today / Week / Gantt views
**File**: `tracker/db.py` (cross-subject queries)

`list_today_tasks`, `list_week_tasks`, `list_today_follow_ups`, `list_week_follow_ups`, and `list_all_active_milestones` check `s.deleted_at IS NULL` but never check `s.archived = 0`. After archiving a subject, its items continue appearing in the overview dashboard. Also, `today_counts()` doesn't join `subjects` at all.

**Fix**: Add `AND s.archived = 0` to all cross-subject queries. Add a subject join to `today_counts()`.

### 15. UTC vs local time mismatch
**Files**: `tracker/db.py` (SQL uses `date('now')` = UTC), `tracker/widgets/overview_view.py` (Python uses `date.today()` = local time)

The global overview uses SQL with `date('now')` (UTC). The subject-filtered overview uses Python `date.today()` (local). Around midnight, these can disagree on what "today" and "this week" mean, causing items to appear in one view but not the other.

**Fix**: Pass `date.today()` as a parameter to DB queries instead of using `date('now')`, or use UTC consistently everywhere.

### 16. CSS ID mismatch for gantt widgets
**File**: `tracker/tracker.tcss`

CSS targets `#gantt-header` and `#gantt-list` but actual widget IDs are `#ov-gantt-header` and `#ov-gantt-list`. Gantt header padding never applies.

**Fix**: Change CSS selectors to `#ov-gantt-header` and `#ov-gantt-list`.

### 17. Search LIKE wildcards not escaped
**File**: `tracker/db.py` (`search` method)

`like = f"%{query}%"` doesn't escape `%` and `_`. Searching for `%` returns all records. Searching for `_` matches any single character.

**Fix**: Escape wildcards before wrapping:
```python
escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
like = f"%{escaped}%"
```
Add `ESCAPE '\\'` to each LIKE clause.

### 18. No way to unarchive a subject
**Files**: `tracker/db.py`, `tracker/widgets/nav_tree.py`

`archive_subject` sets `archived=1` but there is no unarchive method. Even with archived subjects visible (toggle `A`), there is no UI action to unarchive. Subjects can only be recovered by direct SQL.

**Fix**: Change `archive_subject` to `toggle_archive` (like `toggle_pin`), or add a separate unarchive action.

### Minor

### 19. N+1 query pattern in tree rebuild
**File**: `tracker/widgets/nav_tree.py` (`_add_subject_children`)

Each `rebuild` executes 5 global queries plus 5 queries per subject (tasks, open points, follow-ups, milestones, notes). With 20 subjects = 105 queries per rebuild. Fires on every `DataChanged` message.

### 20. `soft_delete_milestone` lacks explicit transaction wrapper
**File**: `tracker/db.py`

Performs 3 statements (delete milestone, unlink tasks, unlink follow-ups) with `conn.commit()` but without `with self.conn:` like `soft_delete_subject` does.

### 21. OpenPointForm cannot clear a resolved_note once set
**File**: `tracker/widgets/open_point_form.py`

The save logic only calls `resolve_open_point` if the resolved note is non-empty. Clearing the field leaves the old value in the database.

### 22. NoteEditor TextArea uses `height: 100%` instead of `1fr`
**File**: `tracker/tracker.tcss`

`NoteEditor TextArea { height: 100% }` — since NoteEditor also contains a Label, total content exceeds 100%. Should use `height: 1fr` to fill remaining space after the Label.

### 23. Week rollover fires on first app launch
**File**: `tracker/db.py` (`perform_week_rollover`)

On first launch, no `week_of` entry exists in `meta`, so rollover always executes, clearing all `today` flags and `day` assignments. If someone imports data and launches the app mid-week, all assignments are wiped.

**Fix**: On first launch, set `week_of` without performing rollover operations.

### 24. `lead_weeks` input silently drops non-numeric values
**File**: `tracker/widgets/milestone_form.py`

`int(lead_weeks_str) if lead_weeks_str.isdigit() else None` — typing "five" or "2.5" gets no feedback that the input was ignored.

### 25. Database connection never explicitly closed
**File**: `tracker/db.py`

No `close()` method. Connection closed only by GC. With WAL mode, this can leave `.db-wal` and `.db-shm` files on disk after exit.

**Fix**: Add `close()` method and call from `TrackerApp.on_unmount`.

---

## Positive Observations

- Message flow architecture is correct (ShowContent bubbles to app, forwarded to ContentArea)
- Tree expansion state preservation during refresh is solid UX
- CSS height chain properly maintained throughout layout hierarchy
- Gantt chart is a creative use of Rich markup within Textual Static widgets
- `_SENTINEL` pattern in `update_task` / `update_milestone` correctly distinguishes "not provided" from "set to None"
- DB mutations consistently post `DataChanged()` to trigger tree refresh
- `DateInput` with arrow-key date navigation is a thoughtful widget
- Consistent soft-delete pattern across all entities
