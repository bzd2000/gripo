# Tracker TUI — Design Spec

A terminal-based personal productivity TUI for task tracking, delegation tracking, open points, and running notes, organized by subjects. Built with Python + Textual + SQLite.

## Decisions from Brainstorming

- **Usage pattern**: Both quick capture and longer review sessions — needs snappy input flows AND scannable layouts
- **Build strategy**: Vertical slices in 5 phases; each phase ships a working app
- **List widget**: `ListView` with styled `ListItem`s (not `DataTable`) for task lists and all entity lists
- **Testing**: In-memory SQLite (`:memory:`) for tests
- **DB path**: `~/.tracker/tracker.db` (simple, not XDG)
- **Notes format**: Markdown — stored as raw markdown, `TextArea` with markdown syntax highlighting for editing
- **Windows compatible**: Use `pathlib.Path` everywhere, no hardcoded path separators
- **Soft deletes only**: No hard `DELETE` statements anywhere. All entities use a `deleted_at TEXT` column (NULL = active, timestamp = soft-deleted). Queries filter with `WHERE deleted_at IS NULL`. Subjects use their existing `archived` column for archiving, plus `deleted_at` for deletion.

## Phases

### Phase 1: Project Setup, Data Layer & Subjects List
### Phase 2: Subject Detail Screen & Tasks
### Phase 3: Notes Section
### Phase 4: Today View
### Phase 5: Open Points, Follow-Ups, This Week, Search, Week Rollover

---

## Phase 1: Project Setup, Data Layer & Subjects List

### Project Setup

- `pyproject.toml` with `textual` as dependency, `pytest` as dev dependency
- Entry point: `python -m tracker` via `__main__.py`, plus `tt` console script
- File structure follows the spec layout in `project.md`

### Data Entity Model

```
┌─────────────────────────────────────────────────────────┐
│                        subjects                         │
├─────────────────────────────────────────────────────────┤
│ PK  id            TEXT                                  │
│     name          TEXT NOT NULL                         │
│     pinned        INTEGER NOT NULL DEFAULT 0            │
│     archived      INTEGER NOT NULL DEFAULT 0            │
│     color         TEXT                                  │
│     created_at    TEXT NOT NULL DEFAULT datetime('now')  │
│ DEL deleted_at    TEXT                                  │
└──────────┬──────────┬──────────┬──────────┬─────────────┘
           │          │          │          │
     ┌─────┘    ┌─────┘    ┌────┘     ┌────┘
     ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌────────┐ ┌──────────┐
│  tasks   │ │open_point│ │follow_ups │ │  notes   │
│          │ │    s     │ │        │ │          │
├──────────┤ ├──────────┤ ├────────┤ ├──────────┤
│PK id     │ │PK id     │ │PK id   │ │PK id     │
│FK subj_id│ │FK subj_id│ │FK s_id │ │FK subj_id│
│  text    │ │  text    │ │  text  │ │  content │
│  priority│ │  context │ │  owner │ │ (markdown)│
│  status  │ │  status  │ │  due_by│ │ created  │
│  category│ │  resolved│ │  status│ │ updated  │
│  day     │ │  _note   │ │  notes │ │DEL del_at│
│  today   │ │  raised  │ │  asked │ └──────────┘
│  created │ │  resolved│ │DEL d_at│
│  done_at │ │DEL del_at│ └────────┘
│DEL del_at│ └──────────┘
└──────────┘

┌──────────────────────┐
│        meta          │  (standalone, no FK)
├──────────────────────┤
│ PK  key    TEXT      │
│     value  TEXT      │
│ e.g. week_of = date  │
└──────────────────────┘

Legend: PK = Primary Key, FK = Foreign Key (subject_id),
        DEL = Soft delete column (deleted_at TEXT)

Relationships:
  subjects 1──►N tasks        (ON DELETE CASCADE as safety net)
  subjects 1──►N open_points  (ON DELETE CASCADE as safety net)
  subjects 1──►N follow_ups      (ON DELETE CASCADE as safety net)
  subjects 1──►N notes        (ON DELETE CASCADE as safety net)

Constraints:
  tasks.priority:    must | should | if-time
  tasks.status:      todo | in-progress | done | blocked
  tasks.category:    delivery | admin | people | strategy | meeting | other
  tasks.day:         mon | tue | wed | thu | fri | anytime
  open_points.status: open | resolved | parked
  follow_ups.status:    waiting | received | overdue | cancelled
```

### Database (`tracker/db.py`)

A `Database` class:
- Constructor takes optional `path: Path | str` (defaults to `Path.home() / ".tracker" / "tracker.db"`; accepts `":memory:"` for tests)
- Creates parent directory via `path.parent.mkdir(parents=True, exist_ok=True)`
- Connects with `sqlite3.Row` row factory
- Enables WAL mode and foreign keys on every connection
- Runs schema initialization (all six tables from the spec: `subjects`, `tasks`, `open_points`, `follow_ups`, `notes`, `meta`)
- All entity tables (`subjects`, `tasks`, `open_points`, `follow_ups`, `notes`) include a `deleted_at TEXT` column (NULL by default). All queries filter `WHERE deleted_at IS NULL` unless explicitly viewing deleted items.

CRUD methods per entity type, returning dataclass instances. The aggregate subjects query (with open task count, open points count, follow_ups count, latest note date) is a dedicated method used by the home view.

### Models (`tracker/models.py`)

Python dataclasses: `Subject`, `Task`, `OpenPoint`, `FollowUp`, `Note`. Each has a `from_row(row: sqlite3.Row)` classmethod. IDs generated with `uuid.uuid4().hex`.

### App Shell (`tracker/app.py`)

`TrackerApp(App)` with:
- `CSS_PATH = "tracker.tcss"`
- `TabbedContent` with three `TabPane`s: Subjects, Today (placeholder), This Week (placeholder)
- `Header` and `Footer`
- Global bindings: `q` quit, `/` search, `?` help

### SubjectsList (`tracker/widgets/subjects_list.py`)

A `ListView` loaded from the aggregate subjects query. Pinned subjects float to top. Each `ListItem` shows: pin indicator, subject name, open task count, follow_ups count, latest note date. Empty state message when no subjects exist.

Bindings:
- `a` — push `AddSubjectScreen`
- `Enter` — push `SubjectDetailScreen`
- `p` — toggle pin
- `shift+a` — toggle show/hide archived
- `x` — archive with confirmation

### AddSubjectScreen (`tracker/screens/add_subject.py`)

`ModalScreen` with `Input` for name. On submit, inserts into DB, dismisses with result so `SubjectsList` refreshes.

### ConfirmScreen (`tracker/screens/confirm.py`)

Generic reusable `ModalScreen` for confirmation dialogs. Takes a message string and returns True/False.

### Soft Delete Cascade

When a subject is soft-deleted, all its child entities (tasks, open points, follow_ups items, notes) are also soft-deleted in the same DB transaction. The foreign key `ON DELETE CASCADE` in the schema is retained as a safety net but is not relied upon — the `Database` class handles cascading soft deletes explicitly.

### DataChanged Message

A custom Textual message posted after any DB mutation. Widgets listen for this to refresh their data.

### Testing

`pytest` with a fixture providing an in-memory `Database(path=":memory:")`. Tests cover:
- Schema creation
- CRUD for subjects
- Aggregate query (subjects with counts)
- Pin/archive behavior

---

## Phase 2: Subject Detail Screen & Tasks

### SubjectDetailScreen (`tracker/screens/subject_detail.py`)

A `Screen` receiving `subject_id` on construction. Layout:
- Subject name in header with pin indicator
- `ScrollableContainer` wrapping four `Collapsible` sections
- Only Tasks section is functional; Open Points, Follow-Ups, Notes show "(coming soon)" placeholders
- Collapsible titles show counts: "Tasks (3 open)"
- Binding: `Escape` to pop back, `1`/`2`/`3`/`4` to focus sections

### TaskList (`tracker/widgets/task_list.py`)

`ListView` inside the Tasks collapsible. Each `ListItem` displays:
- Status icon: `○` todo, `●` in-progress, `✓` done, `✗` blocked
- Task text
- Priority label
- Status label
- CSS classes applied per priority and status for color styling

Bindings (scoped to TaskList widget):
- `a` — push `AddTaskScreen`
- `e` — push `EditTaskScreen` for selected task
- `d` — toggle done (sets/clears `completed_at`)
- `b` — toggle blocked
- `s` — cycle status: todo → in-progress → done → blocked
- `p` — cycle priority: must → should → if-time
- `t` — toggle today flag
- `w` — cycle day: mon → tue → wed → thu → fri → anytime → none (NULL)
- `x` — soft-delete with confirmation (sets `deleted_at`)

### AddTaskScreen (`tracker/screens/add_task.py`)

`ModalScreen` with:
- `Input` for task text
- `Select` for priority (must / should / if-time), default "should"
- `Select` for category (delivery / admin / people / strategy / meeting / other), optional
- Submit and Cancel buttons

### EditTaskScreen

Same layout as `AddTaskScreen`, pre-filled with current values.

### Toast Notifications

Use `self.notify()` after mutations: "Task added", "Task marked done", etc. Applied to all phases.

### Testing

- CRUD for tasks
- Status cycling logic
- Priority cycling logic
- Today flag toggle
- Day cycling

---

## Phase 3: Notes Section

### NotesList (`tracker/widgets/notes_list.py`)

`ListView` inside the Notes collapsible. Notes displayed newest first. Each `ListItem` shows:
- Date (from `created_at`)
- Truncated preview (~80 chars, markdown syntax stripped for readability)

### AddNoteScreen (`tracker/screens/add_note.py`)

`ModalScreen` with:
- `TextArea` with language set to `"markdown"` for syntax highlighting
- Submit and Cancel buttons
- On submit: inserts with current timestamps for `created_at` and `updated_at`

### EditNoteScreen

Same layout, `TextArea` pre-filled. On save: updates content and `updated_at` timestamp.

### Notes Bindings (scoped to NotesList)

- `a` or `n` — add note
- `e` — edit selected note
- `x` — soft-delete with confirmation (sets `deleted_at`)

### Milestone

End of Phase 3 = first "complete enough to actually use" version. Functional subject-based task + notes tracker.

### Testing

- CRUD for notes
- Markdown content round-trip (store and retrieve)
- Timestamp updates on edit

---

## Phase 4: Today View

### TodayView (`tracker/widgets/today_view.py`)

Replaces placeholder in the Today tab. Queries tasks where `today = 1` and `status != 'done'`, across all subjects, ordered by priority (must → should → if-time).

Layout:
- "TODAY'S FOCUS" header
- `ListView` showing up to 5 tasks
- Each row: task text, priority, status, subject name
- Summary line: "Done: 2/4 | Blocked: 1"

### Tab Label

Dynamic: "Today (3/5)" showing non-done today tasks vs max 5. Updates on `DataChanged` or tab activation.

### Bindings

- `d` — toggle done
- `s` — cycle status
- `p` — cycle priority
- `Enter` — push `SubjectDetailScreen` for that task's subject

No task creation in this view. Tasks are pulled in via `t` from a subject's task list.

### Testing

- Today query returns only flagged, non-done tasks
- Max 5 enforcement at display level (not DB)
- Priority ordering

---

## Phase 5: Open Points, Follow-Ups, This Week, Search, Week Rollover

### OpenPointsList (`tracker/widgets/open_points_list.py`)

`ListView` in Subject Detail. Each row: status icon (`?` open, `✓` resolved, `—` parked), text, status label.

Bindings:
- `a` or `o` — add open point
- `e` — edit text
- `c` — add/edit context
- `r` — push `ResolveScreen` (resolution note)
- `s` — cycle: open → parked → resolved
- `x` — soft-delete with confirmation (sets `deleted_at`)

### ResolveScreen (`tracker/screens/resolve_point.py`)

`ModalScreen` with `TextArea` for resolution note. Sets status to resolved, records `resolved_at`.

### AddOpenPointScreen (`tracker/screens/add_open_point.py`)

`ModalScreen` with `Input` for text and optional `Input` for context.

### FollowUpsList (`tracker/widgets/follow_ups_list.py`)

`ListView` in Subject Detail. Each row: text, owner, due date, status icon.

Bindings:
- `a` — push `AddFollowUpScreen`
- `e` — edit
- `s` — cycle: waiting → received → overdue → cancelled
- `n` — edit follow-up notes
- `x` — soft-delete with confirmation (sets `deleted_at`)

### AddFollowUpScreen (`tracker/screens/add_follow_ups.py`)

`ModalScreen` with fields: text (`Input`), owner (`Input`), due date (`Input`, optional).

### WeekView (`tracker/widgets/week_view.py`)

Tasks with a `day` value across all subjects, grouped by day (Mon–Fri, then Anytime). Ordered by priority within each day.

Bindings: same as Today plus `w` to change target day.

### SearchScreen (`tracker/screens/search.py`)

`ModalScreen` with `Input` at top. Live results via UNION ALL query from spec as user types. Results in `ListView` showing type icon, match text, and subject name. `Enter` dismisses and navigates to the item's subject.

### Week Rollover

On app startup in `TrackerApp.on_mount()`:
1. Read `week_of` from `meta` table
2. Compare to current Monday (`date.today()` + `isocalendar()`)
3. If different week:
   - `UPDATE tasks SET today = 0` — clear today flags
   - `UPDATE tasks SET day = NULL WHERE status != 'done'` — reset day assignments
   - `UPDATE tasks SET deleted_at = datetime('now') WHERE status = 'done' AND completed_at < date('now', '-14 days') AND deleted_at IS NULL` — soft-delete old done tasks
   - `INSERT OR REPLACE INTO meta VALUES ('week_of', ?)` — update to current Monday

### HelpScreen (`tracker/screens/help.py`)

`ModalScreen` showing all keyboard bindings organized by context (Global, Subjects List, Subject Detail > Tasks, etc.).

### Testing

- CRUD for open points, follow_ups items
- Status cycling for each entity type
- Week rollover logic (mock dates)
- Search query returns results across all entity types
- This week query groups by day correctly

---

## Styling (`tracker/tracker.tcss`)

All visual styling via Textual CSS:

- **Priority colors**: red (must), yellow (should), `$text-muted` (if-time)
- **Status colors**: green+strikethrough (done), red+bold (blocked), cyan (in-progress), magenta (open), `$text-muted`+italic (parked), green+strikethrough (resolved), red+bold (overdue)
- **Pinned subjects**: `$accent`, bold
- **Modals**: semi-transparent background overlay, centered dialog
- **Collapsibles**: consistent padding, clear visual separation
- **Empty states**: muted, centered text

Relies on Textual's built-in dark/light toggle (`ctrl+d`) and CSS variables (`$surface`, `$accent`, `$text-muted`) so both modes work automatically. No custom theme system.

---

## Cross-Cutting Concerns

### Windows Compatibility

- `pathlib.Path` for all file paths — no hardcoded separators
- `Path.home()` for home directory resolution
- `sqlite3` and Textual both work on Windows natively

### Error Handling

- DB connection failures: show error in app via `self.notify()` with severity
- Missing DB directory: auto-created by `Path.mkdir(parents=True, exist_ok=True)`
- Invalid data from DB: dataclass construction validates via type hints

### Performance

- SQLite queries are fast enough for personal use volumes
- No async DB wrapper needed — `sqlite3` is synchronous, operations are sub-millisecond for expected data sizes
- ListView renders only visible items (Textual handles virtualization)
