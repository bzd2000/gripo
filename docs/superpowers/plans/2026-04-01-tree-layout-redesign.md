# Tree Layout Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the tabbed + modal architecture with a tree sidebar + content pane layout, add markdown comments to entities, add DateInput widget, render all markdown via Textual's Markdown widget.

**Architecture:** Horizontal split layout with `Tree` widget (left) and `ContentArea` container (right). Tree drives navigation at 3 levels (top-level views → subject sections → individual items). Right pane swaps content based on tree selection. Inline forms replace modal screens. DB layer unchanged.

**Tech Stack:** Python 3.10+, Textual (Tree, Markdown widgets), sqlite3

**Spec:** `docs/superpowers/specs/2026-04-01-tree-layout-redesign.md`

---

## File Structure

```
tracker/
├── tracker/
│   ├── app.py                      # REWRITE — Tree + ContentArea split layout
│   ├── db.py                       # MODIFY — add comment columns, migrations
│   ├── models.py                   # MODIFY — add comment field to Task, OpenPoint, FollowUp
│   ├── messages.py                 # MODIFY — add new messages (ShowContent, EditItem, etc.)
│   ├── tracker.tcss                # MODIFY — tree/pane layout styles
│   ├── screens/
│   │   ├── confirm.py              # KEEP
│   │   ├── search.py               # KEEP
│   │   └── help.py                 # KEEP
│   ├── widgets/
│   │   ├── date_input.py           # NEW — reusable date input with arrow key navigation
│   │   ├── nav_tree.py             # NEW — navigation tree (3 levels)
│   │   ├── content_area.py         # NEW — right pane container that swaps widgets
│   │   ├── subject_overview.py     # NEW — subject dashboard
│   │   ├── subject_form.py         # NEW — add subject inline form
│   │   ├── task_form.py            # NEW — task add/edit inline form
│   │   ├── open_point_form.py      # NEW — open point add/edit inline form
│   │   ├── follow_up_form.py       # NEW — follow-up add/edit inline form
│   │   ├── note_editor.py          # NEW — note add/edit with TextArea
│   │   ├── task_list.py            # MODIFY — remove modal refs, emit messages
│   │   ├── notes_list.py           # MODIFY — render markdown previews, emit messages
│   │   ├── open_points_list.py     # MODIFY — remove modal refs, emit messages
│   │   ├── follow_ups_list.py      # MODIFY — remove modal refs, emit messages
│   │   ├── today_view.py           # MODIFY — adapt for content pane
│   │   └── week_view.py            # MODIFY — adapt for content pane
│   └── screens/ (DELETE these)
│       ├── subject_detail.py       # DELETE
│       ├── add_subject.py          # DELETE
│       ├── add_task.py             # DELETE
│       ├── edit_task.py            # DELETE
│       ├── add_note.py             # DELETE
│       ├── edit_note.py            # DELETE
│       ├── add_open_point.py       # DELETE
│       ├── add_follow_up.py        # DELETE
│       └── resolve_point.py        # DELETE
├── tests/
│   ├── test_date_input.py          # NEW — DateInput widget tests
│   └── (existing DB tests unchanged)
```

---

## Phase 1: Foundation (DB changes, DateInput, messages)

### Task 1: Add comment columns to DB + models

**Files:**
- Modify: `tracker/db.py`
- Modify: `tracker/models.py`
- Modify: `tests/test_db_tasks.py` (add comment tests)

- [ ] Write tests: `add_task` with comment, `update_task` with comment, verify comment round-trips. Same for open_points and follow_ups.
- [ ] Run tests — verify fail
- [ ] Add `comment TEXT` column to tasks, open_points, follow_ups table DDL in `_SCHEMA`
- [ ] Add migration in `_migrate()` for each table: `ALTER TABLE x ADD COLUMN comment TEXT` if missing
- [ ] Add `comment: Optional[str]` field to `Task`, `OpenPoint`, `FollowUp` dataclasses, update `from_row`
- [ ] Update `add_task` to accept `comment` param, update INSERT
- [ ] Add `update_task_comment(task_id, comment)` method
- [ ] Update `update_task` to support `comment` field
- [ ] Add `add_open_point` comment param, `update_open_point_comment(point_id, comment)`
- [ ] Add `add_follow_up` comment param, `update_follow_up_comment(follow_up_id, comment)`
- [ ] Run tests — verify pass
- [ ] Commit

---

### Task 2: DateInput widget

**Files:**
- Create: `tracker/widgets/date_input.py`
- Create: `tests/test_date_input.py`

- [ ] Write tests: default value is today, left arrow decreases by 1 day, right arrow increases by 1 day, up arrow increases by 1 month, down arrow decreases by 1 month, delete clears to empty, text input accepted, empty string returns None from `.value` property
- [ ] Run tests — verify fail
- [ ] Implement `DateInput(Input)` subclass:
  - Constructor: `def __init__(self, value: str = "", placeholder: str = "YYYY-MM-DD")`. If value is empty, pre-fill with `date.today().isoformat()`
  - Override `on_key` to intercept Left/Right (±1 day), Up/Down (±1 month) when input has a valid date. Use `datetime.date.fromisoformat()` + `timedelta` for days, manual month arithmetic for months
  - Property `date_value -> Optional[str]`: returns the current text if valid ISO date, None if empty
  - Let Backspace/Delete work normally on text; when fully empty, value is None
- [ ] Run tests — verify pass
- [ ] Commit

---

### Task 3: New messages

**Files:**
- Modify: `tracker/messages.py`

- [ ] Add messages that content pane widgets will post to communicate with the app:
  - `ShowContent(Message)` — carries `content_type: str` (e.g. "task_list", "task_form", "today") and `data: dict` (e.g. `{"subject_id": "...", "task_id": "..."}`)
  - `ContentSaved(Message)` — posted by forms after successful save, carries `content_type: str` and `data: dict`
  - `ContentCancelled(Message)` — posted by forms on Escape
- [ ] Commit

---

## Phase 2: Navigation Tree

### Task 4: NavTree widget

**Files:**
- Create: `tracker/widgets/nav_tree.py`

- [ ] Create `NavTree(Tree)` that takes `db: Database`:
  - `rebuild()` method: clears tree, adds "Today (N)" and "This Week" as root nodes, then subjects (pinned first, excluding archived by default) as root nodes. Under each subject: "Tasks (N)", "Open Points (N)", "Follow-Ups (N)", "Notes (N)" as children. Under each section: individual items as leaf nodes with status icons and truncated text.
  - Each tree node stores metadata via `node.data`: `{"type": "today"|"week"|"subject"|"task_section"|"open_points_section"|"follow_ups_section"|"notes_section"|"task"|"open_point"|"follow_up"|"note", "id": "...", "subject_id": "..."}`
  - Status icons for task leaves: ○ todo, ● in-progress, ✓ done, ✗ blocked
  - Status icons for open point leaves: ? open, ✓ resolved, — parked
  - Status icons for follow-up leaves: ⏳ waiting, ✓ received, ‼ overdue, ✗ cancelled
  - `on_tree_node_selected` posts `ShowContent` with appropriate type and data
  - `refresh_tree()` method: rebuilds while preserving expanded nodes and current selection
  - Toggle archived subjects with `shift+a`
  - `add_subject` binding `a` when at root level: posts `ShowContent(content_type="subject_form")`
  - `p` binding: toggle pin when on a subject node
  - `x` binding: archive subject (with ConfirmScreen) when on a subject node
- [ ] Commit

---

## Phase 3: Content Area + Forms

### Task 5: ContentArea container

**Files:**
- Create: `tracker/widgets/content_area.py`

- [ ] Create `ContentArea(Container)` that manages the right pane:
  - `show(widget)` method: removes current child, mounts new widget
  - `on_show_content(message: ShowContent)` handler: creates appropriate widget based on `content_type` and mounts it via `show()`. Maps:
    - `"today"` → `TodayView(db)`
    - `"week"` → `WeekView(db)`
    - `"subject_overview"` → `SubjectOverview(db, subject_id)`
    - `"task_list"` → `TaskList(db, subject_id)`
    - `"task_form"` → `TaskForm(db, subject_id, task_id=None)` (add) or `TaskForm(db, subject_id, task_id)` (edit)
    - `"open_points_list"` → `OpenPointsList(db, subject_id)`
    - `"open_point_form"` → `OpenPointForm(db, subject_id, point_id)`
    - `"follow_ups_list"` → `FollowUpsList(db, subject_id)`
    - `"follow_up_form"` → `FollowUpForm(db, subject_id, follow_up_id)`
    - `"notes_list"` → `NotesList(db, subject_id)`
    - `"note_editor"` → `NoteEditor(db, subject_id, note_id)`
    - `"subject_form"` → `SubjectForm(db)`
  - On `ContentSaved` or `ContentCancelled`: navigate back to the parent list view
- [ ] Commit

---

### Task 6: SubjectForm (inline)

**Files:**
- Create: `tracker/widgets/subject_form.py`

- [ ] Create `SubjectForm(Widget)` — takes `db`:
  - `compose()`: Label "New Subject", Input for name, focused on mount
  - `Enter` on input: validates non-empty, calls `db.add_subject(name)`, posts `ContentSaved` and `DataChanged`
  - `Escape`: posts `ContentCancelled`
- [ ] Commit

---

### Task 7: TaskForm (inline)

**Files:**
- Create: `tracker/widgets/task_form.py`

- [ ] Create `TaskForm(Widget)` — takes `db`, `subject_id`, optional `task_id` (None = add, set = edit):
  - `compose()`: Label "New Task" or "Edit Task", Input for text, Select for priority, Select for category, `DateInput` for due date, Label "Comment", TextArea(language="markdown") for comment. All pre-filled if editing.
  - `Enter` on any Input: saves — calls `db.add_task(...)` or `db.update_task(...)` including comment and due_date. Posts `ContentSaved` and `DataChanged`.
  - `Escape`: posts `ContentCancelled`
  - Bindings: `ctrl+s` also saves
- [ ] Commit

---

### Task 8: OpenPointForm (inline)

**Files:**
- Create: `tracker/widgets/open_point_form.py`

- [ ] Create `OpenPointForm(Widget)` — takes `db`, `subject_id`, optional `point_id`:
  - `compose()`: Input for text, Input for context, Label "Comment", TextArea(language="markdown") for comment. Pre-filled if editing.
  - Save/cancel same pattern as TaskForm
  - If editing and status needs resolving: show resolved_note field when status is "resolved"
- [ ] Commit

---

### Task 9: FollowUpForm (inline)

**Files:**
- Create: `tracker/widgets/follow_up_form.py`

- [ ] Create `FollowUpForm(Widget)` — takes `db`, `subject_id`, optional `follow_up_id`:
  - `compose()`: Input for text, Input for owner, `DateInput` for due_by, `DateInput` for asked_on, Label "Comment", TextArea(language="markdown") for comment. Pre-filled if editing.
  - Save/cancel same pattern
- [ ] Commit

---

### Task 10: NoteEditor (inline)

**Files:**
- Create: `tracker/widgets/note_editor.py`

- [ ] Create `NoteEditor(Widget)` — takes `db`, `subject_id`, optional `note_id`:
  - `compose()`: TextArea(language="markdown") for content, pre-filled if editing
  - `ctrl+s`: saves, posts `ContentSaved` and `DataChanged`
  - `Escape`: posts `ContentCancelled`
- [ ] Commit

---

### Task 11: SubjectOverview widget

**Files:**
- Create: `tracker/widgets/subject_overview.py`

- [ ] Create `SubjectOverview(Widget)` — takes `db`, `subject_id`:
  - `compose()`: ScrollableContainer with sections:
    - Subject name header with pin indicator
    - "Important Tasks" — tasks with priority "must" or due_date within 3 days, rendered as a compact list (max 5)
    - "Open Points" — open points with status "open" (max 5)
    - "Pending Follow-Ups" — follow-ups with status "waiting" or "overdue" (max 5)
    - "Recent Notes" — last 3 notes, each showing date and markdown-rendered preview (using Textual `Markdown` widget)
  - Each section has a heading and shows "None" if empty
- [ ] Commit

---

## Phase 4: Adapt Existing List Widgets

### Task 12: Adapt TaskList

**Files:**
- Modify: `tracker/widgets/task_list.py`

- [ ] Remove all modal screen imports (AddTaskScreen, EditTaskScreen)
- [ ] Change `action_add_task`: instead of pushing modal, post `ShowContent(content_type="task_form", data={"subject_id": self._subject_id})`
- [ ] Change `action_edit_task`: post `ShowContent(content_type="task_form", data={"subject_id": self._subject_id, "task_id": task.id})`
- [ ] Keep all status/priority/today/day cycling actions unchanged (they mutate DB and refresh in-place)
- [ ] Keep delete action (still uses ConfirmScreen modal)
- [ ] After `DataChanged`, also post it upward so the tree refreshes
- [ ] Display task comment as rendered Markdown below the task list for the highlighted item (optional — or just show in form view)
- [ ] Commit

---

### Task 13: Adapt OpenPointsList

**Files:**
- Modify: `tracker/widgets/open_points_list.py`

- [ ] Remove modal imports (AddOpenPointScreen, ResolveScreen)
- [ ] Change add/edit/context actions to post `ShowContent(content_type="open_point_form", ...)`
- [ ] Change resolve action: post `ShowContent` to open form with resolve mode
- [ ] Keep status cycling and delete
- [ ] Commit

---

### Task 14: Adapt FollowUpsList

**Files:**
- Modify: `tracker/widgets/follow_ups_list.py`

- [ ] Remove modal imports (AddFollowUpScreen, AddNoteScreen)
- [ ] Change add/edit actions to post `ShowContent(content_type="follow_up_form", ...)`
- [ ] Change notes action to post `ShowContent` to open form
- [ ] Keep status cycling and delete
- [ ] Commit

---

### Task 15: Adapt NotesList

**Files:**
- Modify: `tracker/widgets/notes_list.py`

- [ ] Remove modal imports (AddNoteScreen, EditNoteScreen)
- [ ] Change add/edit actions to post `ShowContent(content_type="note_editor", ...)`
- [ ] Render note previews using Textual's `Markdown` widget instead of stripped plain text
- [ ] Keep delete action
- [ ] Commit

---

### Task 16: Adapt TodayView and WeekView

**Files:**
- Modify: `tracker/widgets/today_view.py`
- Modify: `tracker/widgets/week_view.py`

- [ ] Remove `SubjectDetailScreen` imports from both
- [ ] Change `Enter` action to post `ShowContent(content_type="subject_overview", data={"subject_id": ...})` instead of pushing SubjectDetailScreen
- [ ] Both should work as standalone widgets mounted in ContentArea (no Screen dependency)
- [ ] Commit

---

## Phase 5: App Rewrite + Cleanup

### Task 17: Rewrite TrackerApp

**Files:**
- Modify: `tracker/app.py`

- [ ] Replace TabbedContent layout with horizontal split:
  - Left: `NavTree(db)` in a container (~25% width)
  - Right: `ContentArea(db)` (~75% width)
- [ ] `on_mount`: call `db.perform_week_rollover()`, build initial tree, show Today view in content area
- [ ] Handle `DataChanged`: call `nav_tree.refresh_tree()`, refresh current content if needed
- [ ] Handle `ShowContent`: forward to content area
- [ ] Handle `ContentSaved` / `ContentCancelled`: navigate content area back to parent list, refresh tree
- [ ] Global bindings: `q` quit, `/` search, `?` help, `ctrl+w` focus tree
- [ ] Remove all old imports (TabbedContent, TabPane, SubjectsList, SubjectDetailScreen, etc.)
- [ ] Commit

---

### Task 18: Update CSS

**Files:**
- Modify: `tracker/tracker.tcss`

- [ ] Add layout styles:
  - `#app-layout` horizontal container, height 100%
  - `#nav-tree` with width 25%, border-right, overflow-y auto
  - `#content-area` with width 75%, padding
  - Form styles: inputs with margin, TextArea height
  - Subject overview section styles
  - Keep all existing priority/status/empty-state classes
- [ ] Commit

---

### Task 19: Delete old files

**Files:**
- Delete: `tracker/screens/subject_detail.py`
- Delete: `tracker/screens/add_subject.py`
- Delete: `tracker/screens/add_task.py`
- Delete: `tracker/screens/edit_task.py`
- Delete: `tracker/screens/add_note.py`
- Delete: `tracker/screens/edit_note.py`
- Delete: `tracker/screens/add_open_point.py`
- Delete: `tracker/screens/add_follow_up.py`
- Delete: `tracker/screens/resolve_point.py`
- Delete: `tracker/widgets/subjects_list.py`

- [ ] Delete all listed files
- [ ] Remove any remaining imports of deleted modules across the codebase
- [ ] Run `pytest tests/ -v` — all existing DB tests should still pass
- [ ] Run `python -m tracker` — verify app launches with tree layout
- [ ] Commit

---

### Task 20: Final integration verification

- [ ] Run `pytest tests/ -v` — all tests pass
- [ ] Run `python -m tracker` — verify:
  - Tree shows Today, This Week, subjects with children
  - Arrow keys navigate tree, Enter expands/selects
  - Selecting subject shows overview dashboard
  - Selecting Tasks section shows task list
  - Selecting a task leaf shows edit form
  - `a` on Tasks section shows add form
  - `Enter` saves, `Escape` cancels forms
  - `ctrl+w` returns focus to tree
  - Status shortcuts work (d, s, p, t, w on tasks)
  - Delete with `x` shows confirm dialog
  - Search `/` and Help `?` modals work
  - DateInput arrows change dates
  - Markdown comments display rendered, edit as raw
  - Pinned subjects sort to top
  - Week rollover on startup
- [ ] Commit any remaining fixes
