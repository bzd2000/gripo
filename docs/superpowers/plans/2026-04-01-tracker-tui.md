# Tracker TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a terminal-based personal productivity TUI for task tracking, notes, open points, and follow-ups organized by subjects.

**Architecture:** Textual TUI app with SQLite persistence. `Database` class wraps all SQL. Dataclass models map rows. `TabbedContent` for top-level nav, `Screen`s for detail views, `ModalScreen`s for input dialogs. Soft deletes everywhere (no hard DELETEs).

**Tech Stack:** Python 3.10+, Textual (TUI framework), sqlite3 (stdlib), pytest

**Spec:** `docs/superpowers/specs/2026-04-01-tracker-tui-design.md`
**Original requirements:** `project.md`

---

## File Structure

```
tracker/
├── pyproject.toml
├── tracker/
│   ├── __init__.py
│   ├── __main__.py           # Entry point: python -m tracker
│   ├── app.py                # TrackerApp, top-level TabbedContent, global bindings
│   ├── db.py                 # Database class — SQLite connection, schema, all queries
│   ├── models.py             # Dataclasses: Subject, Task, OpenPoint, FollowUp, Note
│   ├── messages.py           # Custom Textual messages (DataChanged)
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── subject_detail.py # SubjectDetailScreen
│   │   ├── add_subject.py    # AddSubjectScreen (ModalScreen)
│   │   ├── add_task.py       # AddTaskScreen (ModalScreen)
│   │   ├── edit_task.py      # EditTaskScreen (ModalScreen)
│   │   ├── add_note.py       # AddNoteScreen (ModalScreen)
│   │   ├── edit_note.py      # EditNoteScreen (ModalScreen)
│   │   ├── add_open_point.py # AddOpenPointScreen (ModalScreen, also used for edit with pre-fill)
│   │   ├── add_follow_up.py  # AddFollowUpScreen (ModalScreen, also used for edit with pre-fill)
│   │   ├── resolve_point.py  # ResolveScreen (ModalScreen)
│   │   ├── search.py         # SearchScreen (ModalScreen)
│   │   ├── confirm.py        # Generic ConfirmScreen (ModalScreen)
│   │   └── help.py           # HelpScreen (ModalScreen)
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── subjects_list.py  # SubjectsList (ListView)
│   │   ├── today_view.py     # TodayView
│   │   ├── week_view.py      # WeekView
│   │   ├── task_list.py      # TaskList (ListView)
│   │   ├── notes_list.py     # NotesList (ListView)
│   │   ├── open_points_list.py # OpenPointsList (ListView)
│   │   └── follow_ups_list.py  # FollowUpsList (ListView)
│   └── tracker.tcss          # All Textual CSS styles
└── tests/
    ├── __init__.py
    ├── conftest.py            # Shared fixtures (in-memory Database)
    ├── test_db_subjects.py
    ├── test_db_tasks.py
    ├── test_db_notes.py
    ├── test_db_open_points.py
    ├── test_db_follow_ups.py
    ├── test_db_week_rollover.py
    └── test_db_search.py
```

---

## Phase 1: Project Setup, Data Layer & Subjects List

### Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`, `tracker/__init__.py`, `tracker/__main__.py`, `tests/__init__.py`

- [ ] Create `pyproject.toml` with `textual` dependency, `pytest` in dev extras, `tt` console script pointing to `tracker.app:main`
- [ ] Create empty `tracker/__init__.py` and `tests/__init__.py`
- [ ] Create `tracker/__main__.py` that calls `main()` from `tracker.app`
- [ ] Run `pip install -e ".[dev]"` to verify install works
- [ ] `git init` and commit

---

### Task 2: Models

**Files:**
- Create: `tracker/models.py`
- Create: `tests/conftest.py`

- [ ] Create dataclasses for `Subject`, `Task`, `OpenPoint`, `FollowUp`, `Note` — each with a `from_row(row: sqlite3.Row)` classmethod. Fields match the schema in the spec. `Subject` includes optional aggregate fields (`open_tasks`, `open_points_count`, `follow_ups_count`, `latest_note`). `Task` includes optional `subject_name` for cross-cutting queries.
- [ ] Create `tests/conftest.py` with a `db` fixture returning `Database(path=":memory:")`
- [ ] Commit

---

### Task 3: Database — schema and subject CRUD

**Files:**
- Create: `tracker/db.py`
- Create: `tests/test_db_subjects.py`

- [ ] Write tests for: schema creates all 6 tables, `add_subject`, `get_subject`, `list_subjects` (excluding archived, excluding soft-deleted, including archived when requested), `toggle_pin` (and pinned sort first), `archive_subject`, `soft_delete_subject` (cascades to children)
- [ ] Run tests — verify they fail
- [ ] Implement `Database` class: constructor takes `path: Path | str`, creates parent dir if Path, connects with `sqlite3.Row`, runs schema DDL (all 6 tables from spec with `deleted_at` columns). Implement subject CRUD methods. `list_subjects` uses the aggregate query from the spec (counts of open tasks, open points, follow-ups, latest note date). `soft_delete_subject` cascades to all child tables in a single transaction. Include stub `add_task`, `list_tasks`, `add_note`, `list_notes` methods (needed for cascade test).
- [ ] Run tests — verify they pass
- [ ] Commit

---

### Task 4: Custom messages

**Files:**
- Create: `tracker/messages.py`

- [ ] Create `DataChanged(Message)` — a simple custom Textual message with no payload, posted after any DB mutation so widgets can refresh
- [ ] Commit

---

### Task 5: CSS styles

**Files:**
- Create: `tracker/tracker.tcss`

- [ ] Create CSS with styles from the spec: priority classes (must=red, should=yellow, if-time=muted), status classes (done=green+strike, blocked=red+bold, in-progress=cyan, open=magenta, parked=muted+italic, resolved=green+strike, overdue=red+bold), subject-pinned style, modal dialog layout, empty state style, subject header, collapsible margins
- [ ] Commit

---

### Task 6: ConfirmScreen

**Files:**
- Create: `tracker/screens/__init__.py`
- Create: `tracker/screens/confirm.py`

- [ ] Create empty `tracker/screens/__init__.py`
- [ ] Create `ConfirmScreen(ModalScreen[bool])` — takes a message string, shows it with Confirm and Cancel buttons, dismisses with `True`/`False`
- [ ] Commit

---

### Task 7: AddSubjectScreen

**Files:**
- Create: `tracker/screens/add_subject.py`

- [ ] Create `AddSubjectScreen(ModalScreen[str | None])` — `Input` for name, validates non-empty, dismisses with name or None. Support `Enter` to submit from the input.
- [ ] Commit

---

### Task 8: SubjectsList widget

**Files:**
- Create: `tracker/widgets/__init__.py`
- Create: `tracker/widgets/subjects_list.py`

- [ ] Create empty `tracker/widgets/__init__.py`
- [ ] Create `SubjectSelected(Message)` carrying `subject_id`
- [ ] Create `SubjectsList(ListView)` — loads from `db.list_subjects()`, renders each subject with pin indicator, name, counts, latest note date. Shows empty state message when no subjects. Bindings: `a` add, `Enter` posts `SubjectSelected`, `p` toggle pin, `A` toggle archived visibility, `x` archive with confirmation. Posts `DataChanged` after mutations.
- [ ] Commit

---

### Task 9: TrackerApp shell

**Files:**
- Create: `tracker/app.py`

- [ ] Create `TrackerApp(App)` with `CSS_PATH = "tracker.tcss"`, `Header`, `Footer`, `TabbedContent` with three `TabPane`s: Subjects (with `SubjectsList`), Today (placeholder Label), This Week (placeholder Label). Binding: `q` quit. `on_subject_selected` handler shows a notify placeholder for now. `main()` function at module level.
- [ ] Run `python -m tracker` to verify it starts
- [ ] Commit

---

## Phase 2: Subject Detail Screen & Tasks

### Task 10: Task CRUD in Database

**Files:**
- Modify: `tracker/db.py`
- Create: `tests/test_db_tasks.py`

- [ ] Write tests for: `add_task` (with priority, category), `list_tasks` (excludes soft-deleted, ordered by status then priority), `update_task_status` (sets `completed_at` when done, clears when un-done), `update_task_priority`, `toggle_today`, `update_task_day` (including setting to None), `update_task` (text, priority, category), `soft_delete_task`
- [ ] Run tests — verify they fail
- [ ] Replace task stubs in `db.py` with full implementations: `add_task`, `get_task`, `list_tasks` (ordered by status priority then priority level), `update_task_status`, `update_task_priority`, `toggle_today`, `update_task_day`, `update_task`, `soft_delete_task`
- [ ] Run tests — verify they pass
- [ ] Commit

---

### Task 11: AddTaskScreen and EditTaskScreen

**Files:**
- Create: `tracker/screens/add_task.py`
- Create: `tracker/screens/edit_task.py`

- [ ] Create `TaskData` dataclass (text, priority, category)
- [ ] Create `AddTaskScreen(ModalScreen[TaskData | None])` — Input for text, Select for priority (default "should"), Select for category (optional, allow blank). Enter submits from text input.
- [ ] Create `EditTaskScreen(ModalScreen[TaskData | None])` — same layout as AddTaskScreen but takes a `Task` in constructor and pre-fills all fields
- [ ] Commit

---

### Task 12: TaskList widget

**Files:**
- Create: `tracker/widgets/task_list.py`

- [ ] Create `TaskList(ListView)` — takes `db` and `subject_id`. Renders tasks with status icons (○ todo, ● in-progress, ✓ done, ✗ blocked), text, priority, status, today flag, day label. Shows empty state. All bindings from spec: `a` add, `e` edit, `d` toggle done, `b` toggle blocked, `s` cycle status, `p` cycle priority, `t` toggle today, `w` cycle day, `x` soft-delete with confirmation. Posts `DataChanged` after each mutation. Uses `self.notify()` for feedback.
- [ ] Commit

---

### Task 13: SubjectDetailScreen

**Files:**
- Create: `tracker/screens/subject_detail.py`
- Modify: `tracker/app.py`

- [ ] Create `SubjectDetailScreen(Screen)` — takes `db` and `subject_id`. Shows subject name with pin indicator. `ScrollableContainer` with four `Collapsible` sections: Tasks (with `TaskList`), Open Points (placeholder), Follow-Ups (placeholder), Notes (placeholder). Collapsible titles show counts (updated via `on_data_changed`). Bindings: `Escape` back, `1`/`2`/`3`/`4` focus sections.
- [ ] Update `TrackerApp.on_subject_selected` to push `SubjectDetailScreen`
- [ ] Run app, verify navigation: add subject → Enter → see detail → Escape → back
- [ ] Commit

---

## Phase 3: Notes Section

### Task 14: Note CRUD in Database

**Files:**
- Modify: `tracker/db.py`
- Create: `tests/test_db_notes.py`

- [ ] Write tests for: `add_note` (markdown content), `list_notes` (newest first, excludes soft-deleted), `get_note`, `update_note` (updates `updated_at`), `soft_delete_note`
- [ ] Run tests — verify they fail
- [ ] Replace note stubs with full implementations
- [ ] Run tests — verify they pass
- [ ] Commit

---

### Task 15: AddNoteScreen and EditNoteScreen

**Files:**
- Create: `tracker/screens/add_note.py`
- Create: `tracker/screens/edit_note.py`

- [ ] Create `AddNoteScreen(ModalScreen[str | None])` — `TextArea` with `language="markdown"` for syntax highlighting. Save and Cancel buttons.
- [ ] Create `EditNoteScreen(ModalScreen[str | None])` — same layout, takes a `Note` and pre-fills the `TextArea`
- [ ] Commit

---

### Task 16: NotesList widget

**Files:**
- Create: `tracker/widgets/notes_list.py`

- [ ] Create `NotesList(ListView)` — takes `db` and `subject_id`. Shows notes newest first, each with date and ~80-char preview (markdown syntax stripped). Empty state message. Bindings: `a`/`n` add, `e` edit, `x` soft-delete with confirmation. Posts `DataChanged`.
- [ ] Commit

---

### Task 17: Wire NotesList into SubjectDetailScreen

**Files:**
- Modify: `tracker/screens/subject_detail.py`

- [ ] Replace Notes placeholder with `NotesList` widget
- [ ] Update `on_data_changed` to refresh notes count in collapsible title
- [ ] Run app, verify notes CRUD in subject detail
- [ ] Commit

---

## Phase 4: Today View

### Task 18: Today query in Database

**Files:**
- Modify: `tracker/db.py`
- Modify: `tests/test_db_tasks.py`

- [ ] Write tests for: `list_today_tasks` (returns today-flagged non-done tasks across all subjects, ordered by priority, includes `subject_name` from join), excludes done tasks, excludes soft-deleted. `today_counts` returns (total, done, blocked) tuple.
- [ ] Run tests — verify they fail
- [ ] Implement `list_today_tasks` (JOIN with subjects for `subject_name`) and `today_counts`
- [ ] Run tests — verify they pass
- [ ] Commit

---

### Task 19: TodayView widget

**Files:**
- Create: `tracker/widgets/today_view.py`
- Modify: `tracker/app.py`

- [ ] Create `TodayView(Vertical)` — header "TODAY'S FOCUS", `ListView` showing up to 5 tasks (sliced at display level), summary line "Done: X/Y | Blocked: Z". Empty state message. Bindings: `d` toggle done, `s` cycle status, `p` cycle priority, `Enter` push `SubjectDetailScreen`. Posts `DataChanged`.
- [ ] Replace Today tab placeholder in `TrackerApp` with `TodayView`
- [ ] Add `on_data_changed` handler to `TrackerApp` that updates tab label "Today (X/Y)" and refreshes `TodayView` and (later) `WeekView`
- [ ] Run app, verify today view works end-to-end
- [ ] Commit

---

## Phase 5: Open Points, Follow-Ups, This Week, Search, Week Rollover

### Task 20: Open Points CRUD in Database

**Files:**
- Modify: `tracker/db.py`
- Create: `tests/test_db_open_points.py`

- [ ] Write tests for: `add_open_point` (with optional context), `list_open_points` (excludes soft-deleted, ordered by status then raised_at), `get_open_point`, `update_open_point_status`, `resolve_open_point` (sets resolved_note and resolved_at), `update_open_point_text`, `update_open_point_context`, `soft_delete_open_point`
- [ ] Run tests — verify they fail
- [ ] Implement all open point methods
- [ ] Run tests — verify they pass
- [ ] Commit

---

### Task 21: Follow-Up CRUD in Database

**Files:**
- Modify: `tracker/db.py`
- Create: `tests/test_db_follow_ups.py`

- [ ] Write tests for: `add_follow_up` (with optional due_by), `list_follow_ups` (excludes soft-deleted, ordered by status then due_by), `get_follow_up`, `update_follow_up_status`, `update_follow_up_notes`, `update_follow_up` (text, owner, due_by), `soft_delete_follow_up`
- [ ] Run tests — verify they fail
- [ ] Implement all follow-up methods
- [ ] Run tests — verify they pass
- [ ] Commit

---

### Task 22: OpenPointsList widget and screens

**Files:**
- Create: `tracker/screens/add_open_point.py`
- Create: `tracker/screens/resolve_point.py`
- Create: `tracker/widgets/open_points_list.py`

- [ ] Create `OpenPointData` dataclass (text, context)
- [ ] Create `AddOpenPointScreen(ModalScreen[OpenPointData | None])` — accepts optional `text` and `context` params for pre-filling when used for editing. Input for text, Input for context (optional).
- [ ] Create `ResolveScreen(ModalScreen[str | None])` — `TextArea` for resolution note
- [ ] Create `OpenPointsList(ListView)` — status icons (? open, ✓ resolved, — parked), text, context, status. Bindings: `a`/`o` add, `e` edit (pre-fills `AddOpenPointScreen` with current values), `c` edit context (pre-fills), `r` resolve, `s` cycle status, `x` soft-delete. Posts `DataChanged`.
- [ ] Commit

---

### Task 23: FollowUpsList widget and screen

**Files:**
- Create: `tracker/screens/add_follow_up.py`
- Create: `tracker/widgets/follow_ups_list.py`

- [ ] Create `FollowUpData` dataclass (text, owner, due_by)
- [ ] Create `AddFollowUpScreen(ModalScreen[FollowUpData | None])` — accepts optional `text`, `owner`, `due_by` params for pre-filling when editing. Inputs for text, owner, due date.
- [ ] Create `FollowUpsList(ListView)` — shows text, owner, due date, status icon (⏳ waiting, ✓ received, ‼ overdue, ✗ cancelled). Bindings: `a` add, `e` edit (pre-fills), `s` cycle status, `n` edit follow-up notes (use `AddNoteScreen` pre-filled with existing notes), `x` soft-delete. Posts `DataChanged`.
- [ ] Commit

---

### Task 24: Wire OpenPointsList and FollowUpsList into SubjectDetailScreen

**Files:**
- Modify: `tracker/screens/subject_detail.py`

- [ ] Replace Open Points and Follow-Ups placeholders with `OpenPointsList` and `FollowUpsList`
- [ ] Update `on_data_changed` to refresh counts for all four collapsible sections
- [ ] Run app, verify all four sections work
- [ ] Commit

---

### Task 25: WeekView widget

**Files:**
- Modify: `tracker/db.py`
- Create: `tracker/widgets/week_view.py`
- Modify: `tracker/app.py`

- [ ] Add `list_week_tasks` to Database — tasks with `day IS NOT NULL` and `status != 'done'`, joined with subjects for `subject_name`, ordered by day then priority
- [ ] Create `WeekView(Vertical)` — header "THIS WEEK", `ListView` with tasks grouped by day (Mon–Fri, Anytime). Day headers as non-selectable items. Bindings: `d` toggle done, `s` cycle status, `p` cycle priority, `w` cycle day, `Enter` push `SubjectDetailScreen`. Posts `DataChanged`.
- [ ] Replace This Week tab placeholder in `TrackerApp` with `WeekView`
- [ ] Update `on_data_changed` in `TrackerApp` to also refresh `WeekView`
- [ ] Commit

---

### Task 26: SearchScreen

**Files:**
- Modify: `tracker/db.py`
- Create: `tracker/screens/search.py`
- Create: `tests/test_db_search.py`
- Modify: `tracker/app.py`

- [ ] Write tests for: `search` finds subjects by name, tasks by text, notes by content, open points by text, follow-ups by text or owner. Excludes soft-deleted. Case-insensitive.
- [ ] Run tests — verify they fail
- [ ] Implement `search(query: str) -> list[dict]` using the UNION ALL query from the spec (with `LIKE %query%` and `deleted_at IS NULL` on every branch)
- [ ] Run tests — verify they pass
- [ ] Create `SearchScreen(ModalScreen[dict | None])` — `Input` at top, live results in `ListView` as user types (min 2 chars). Results show type icon, type label, preview text. `Enter` on result dismisses with result dict. `Escape` cancels.
- [ ] Wire into `TrackerApp`: add `slash` binding, `action_search` pushes `SearchScreen`, on result navigates to subject
- [ ] Commit

---

### Task 27: Week rollover

**Files:**
- Modify: `tracker/db.py`
- Create: `tests/test_db_week_rollover.py`
- Modify: `tracker/app.py`

- [ ] Write tests for: rollover clears today flags, clears day assignments on non-done tasks, preserves done task day assignments, soft-deletes done tasks older than 14 days, keeps recent done tasks, updates `meta.week_of`, skips if same week (no force)
- [ ] Run tests — verify they fail
- [ ] Implement `perform_week_rollover(force: bool = False) -> bool` — reads `week_of` from meta, compares to current Monday, if new week: clear today flags, reset days on non-done, soft-delete old done tasks, update meta. All in one transaction.
- [ ] Run tests — verify they pass
- [ ] Wire into `TrackerApp.on_mount` — call `perform_week_rollover()`, notify user if rollover happened
- [ ] Commit

---

### Task 28: HelpScreen

**Files:**
- Create: `tracker/screens/help.py`
- Modify: `tracker/app.py`

- [ ] Create `HelpScreen(ModalScreen[None])` — `ScrollableContainer` with a `Static` showing all keyboard shortcuts organized by context (Global, Subjects List, Subject Detail > Tasks/Open Points/Follow-Ups/Notes, Today, This Week). `Escape` or `?` to close.
- [ ] Wire into `TrackerApp`: add `question_mark` binding, `action_help` pushes `HelpScreen`
- [ ] Commit

---

### Task 29: Final integration test

- [ ] Run `pytest -v` — all tests pass
- [ ] Run `python -m tracker` — verify end-to-end: subjects CRUD, task CRUD, notes with markdown, today view, week view, open points, follow-ups, search, help, week rollover, all soft deletes
- [ ] Commit any remaining changes
