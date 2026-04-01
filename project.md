# Build a Terminal Task & Notes Tracker TUI

Build a Python TUI for personal productivity — task tracking, delegation tracking, open points, and running notes — all organized by **subject**. Use **Textual** for the UI and **SQLite** (via Python's built-in `sqlite3`) for storage.

## Core Mental Model

**Subjects are the primary organizing unit.** A subject is anything you're tracking: a project, a client, a person, a workstream, an initiative. Every task, note, open point, and waiting-on item belongs to a subject.

Cross-cutting views (Today, This Week) aggregate items from across all subjects so you can plan your day and week without context-switching.

## Views

### 1. Subjects (home view)
A list of all subjects. This is where you land on launch. Shows each subject with a quick summary: count of open tasks, open points, pending waiting-on items, and latest note date. Pinned subjects float to top.

### 2. Subject Detail
When you select a subject, you see everything related to it in a single scrollable view, split into four collapsible sections:
- **Tasks** — open tasks for this subject (with priority and status)
- **Open Points** — unresolved questions, decisions, discussion topics — things that need to be talked through or figured out, not just executed
- **Waiting On** — things you're waiting on from others, scoped to this subject
- **Notes** — chronological running notes (newest first), like a log

### 3. Today (cross-cutting)
Pulls tasks flagged for today from ALL subjects. Max 5. Each row shows the task + which subject it belongs to. This is your "what am I actually doing right now" view.

### 4. This Week (cross-cutting)
All tasks tagged for the current week across all subjects, grouped or labeled by subject. Helps you plan at the weekly level.

## Tech Stack

- **Python 3.10+**
- **Textual** (`pip install textual`) — the TUI framework. Use its built-in widgets: `ListView`, `DataTable`, `Input`, `TextArea`, `TabbedContent`, `Header`, `Footer`, `Static`, `Label`, `Collapsible`, `OptionList`, and modal `Screen`s
- **Python's built-in `sqlite3`** — no external DB dependency needed
- **`uuid`** from stdlib for ID generation (or `nanoid` via pip if preferred)
- Database file at `~/.tracker/tracker.db` — auto-created on first run
- CSS theming via Textual's `.tcss` files
- No server, no external API, no extra dependencies beyond Textual

## Data Model (SQLite Schema)

The database is initialized on first run with `sqlite3.connect()`. Enable WAL mode and foreign keys on every connection.

```sql
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS subjects (
  id            TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  pinned        INTEGER NOT NULL DEFAULT 0,
  archived      INTEGER NOT NULL DEFAULT 0,
  color         TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
  id            TEXT PRIMARY KEY,
  subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  text          TEXT NOT NULL,
  priority      TEXT NOT NULL DEFAULT 'should'  CHECK (priority IN ('must', 'should', 'if-time')),
  status        TEXT NOT NULL DEFAULT 'todo'    CHECK (status IN ('todo', 'in-progress', 'done', 'blocked')),
  category      TEXT CHECK (category IN ('delivery', 'admin', 'people', 'strategy', 'meeting', 'other')),
  day           TEXT CHECK (day IN ('mon', 'tue', 'wed', 'thu', 'fri', 'anytime')),
  today         INTEGER NOT NULL DEFAULT 0,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at  TEXT
);

CREATE TABLE IF NOT EXISTS open_points (
  id            TEXT PRIMARY KEY,
  subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  text          TEXT NOT NULL,
  context       TEXT,
  status        TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'parked')),
  resolved_note TEXT,
  raised_at     TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at   TEXT
);

CREATE TABLE IF NOT EXISTS waiting (
  id            TEXT PRIMARY KEY,
  subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  text          TEXT NOT NULL,
  owner         TEXT NOT NULL,
  asked_on      TEXT NOT NULL DEFAULT (date('now')),
  due_by        TEXT,
  status        TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'received', 'overdue', 'cancelled')),
  notes         TEXT
);

CREATE TABLE IF NOT EXISTS notes (
  id            TEXT PRIMARY KEY,
  subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  content       TEXT NOT NULL,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS meta (
  key           TEXT PRIMARY KEY,
  value         TEXT NOT NULL
);
```

### Useful Queries

```sql
-- Subjects list with counts (home view)
SELECT s.*,
  (SELECT COUNT(*) FROM tasks t WHERE t.subject_id = s.id AND t.status != 'done') AS open_tasks,
  (SELECT COUNT(*) FROM open_points op WHERE op.subject_id = s.id AND op.status = 'open') AS open_points_count,
  (SELECT COUNT(*) FROM waiting w WHERE w.subject_id = s.id AND w.status = 'waiting') AS waiting_count,
  (SELECT MAX(n.created_at) FROM notes n WHERE n.subject_id = s.id) AS latest_note
FROM subjects s
WHERE s.archived = 0
ORDER BY s.pinned DESC, latest_note DESC NULLS LAST;

-- Today view (cross-cutting, max 5)
SELECT t.*, s.name AS subject_name
FROM tasks t JOIN subjects s ON t.subject_id = s.id
WHERE t.today = 1 AND t.status != 'done'
ORDER BY
  CASE t.priority WHEN 'must' THEN 1 WHEN 'should' THEN 2 ELSE 3 END;

-- This week view
SELECT t.*, s.name AS subject_name
FROM tasks t JOIN subjects s ON t.subject_id = s.id
WHERE t.day IS NOT NULL AND t.status != 'done'
ORDER BY
  CASE t.day WHEN 'mon' THEN 1 WHEN 'tue' THEN 2 WHEN 'wed' THEN 3
             WHEN 'thu' THEN 4 WHEN 'fri' THEN 5 ELSE 6 END,
  CASE t.priority WHEN 'must' THEN 1 WHEN 'should' THEN 2 ELSE 3 END;

-- Full-text search across everything
SELECT 'subject' AS type, id, name AS match_text, NULL AS subject_id FROM subjects WHERE name LIKE ?
UNION ALL
SELECT 'task', id, text, subject_id FROM tasks WHERE text LIKE ?
UNION ALL
SELECT 'note', id, content, subject_id FROM notes WHERE content LIKE ?
UNION ALL
SELECT 'open_point', id, text, subject_id FROM open_points WHERE text LIKE ?
UNION ALL
SELECT 'waiting', id, text, subject_id FROM waiting WHERE text LIKE ? OR owner LIKE ?;
```

## UI Layout

### Subjects List (home)
```
┌──────────────────────────────────────────────────────────┐
│  TRACKER                               Wed, Apr 01 2026  │
│  [Subjects]  [Today 3/5]  [This Week]                    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  📌 Project Alpha          4 tasks  2 waiting  Mar 31   │
│  📌 Q2 Planning            2 tasks  0 waiting  Mar 30   │
│     Client: Acme           1 task   1 waiting  Mar 28   │
│     Hiring — Backend       3 tasks  3 waiting  Mar 25   │
│     Infrastructure         0 tasks  0 waiting  Mar 20   │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  a Add  enter Open  p Pin  / Search  q Quit             │
└──────────────────────────────────────────────────────────┘
```

### Subject Detail
```
┌──────────────────────────────────────────────────────────┐
│  ← Project Alpha                                    📌   │
├──────────────────────────────────────────────────────────┤
│  ▼ TASKS (3 open)                                        │
│  1. ○ Review PR for auth service         must   todo     │
│  2. ● Write API integration tests      should   wip      │
│  3. ○ Update project README           if-time   todo     │
│  4. ✓ Set up CI pipeline               must    done      │
│                                                          │
│  ▼ OPEN POINTS (2 open)                                  │
│  1. ? Do we go with REST or GraphQL for v2?       open   │
│  2. ? Who owns the migration plan?                open   │
│  3. ✓ Decided on Postgres over Mongo           resolved  │
│                                                          │
│  ▼ WAITING ON (2 pending)                                │
│  1. Design mockups from Sarah          due Apr 03  ⏳     │
│  2. Budget approval from finance       due Apr 05  ⏳     │
│                                                          │
│  ▼ NOTES (2 entries)                                     │
│  Apr 01 — Kicked off sprint 3, assigned FE to Marcus.    │
│           Need to follow up on API contract by Thu.      │
│  Mar 28 — Stakeholder meeting went well. Green light     │
│           on the new approach. Budget TBD.               │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  a Add task  n Note  o Open point  w Waiting  esc Back   │
└──────────────────────────────────────────────────────────┘
```

### Today View (cross-cutting)
```
┌──────────────────────────────────────────────────────────┐
│  TRACKER                               Wed, Apr 01 2026  │
│  [Subjects]  [Today 3/5]  [This Week]                    │
├──────────────────────────────────────────────────────────┤
│  TODAY'S FOCUS                                           │
│                                                          │
│  1. ○ Review PR for auth service    must   Project Alpha │
│  2. ○ Send Q2 budget draft        should   Q2 Planning  │
│  3. ● Prep for Acme call          should   Client: Acme │
│  4.                                                      │
│  5.                                                      │
│                                                          │
│  Done: 0/3    Blocked: 0                                 │
│                                                          │
├──────────────────────────────────────────────────────────┤
│  d Done  s Status  p Priority  enter Go to subject       │
└──────────────────────────────────────────────────────────┘
```

## Textual Architecture

### App Structure

Use Textual's `App` class as the root. Use `TabbedContent` for the top-level Subjects / Today / This Week navigation. Subject Detail is pushed as a separate `Screen`.

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, TabbedContent, TabPane
from textual.screen import Screen

class TrackerApp(App):
    """Main app with tabbed navigation."""

    CSS_PATH = "tracker.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("slash", "search", "Search"),
        ("question_mark", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Subjects", id="subjects-tab"):
                yield SubjectsList()
            with TabPane("Today (0/5)", id="today-tab"):
                yield TodayView()
            with TabPane("This Week", id="week-tab"):
                yield WeekView()
        yield Footer()

class SubjectDetailScreen(Screen):
    """Pushed when user selects a subject."""
    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
        ("a", "add_task", "Add task"),
        ("n", "add_note", "New note"),
        ("o", "add_open_point", "Open point"),
        ("w", "add_waiting", "Waiting on"),
    ]
```

### Key Textual Concepts to Use

- **`TabbedContent`** — for Subjects / Today / This Week top-level tabs
- **`Screen`** — SubjectDetailScreen is pushed/popped, not a tab. Use `self.app.push_screen(SubjectDetailScreen(subject_id))` on Enter
- **`ListView` / `ListItem`** — for subjects list, task lists, open points list, waiting list
- **`Collapsible`** — for the four sections within Subject Detail (Tasks, Open Points, Waiting On, Notes), each collapsible with counts in the title
- **`DataTable`** — alternative to ListView if columnar layout is preferred for tasks
- **`Input`** — single-line text input for adding tasks, subjects, search
- **`TextArea`** — full multiline editor for notes (Textual's built-in widget with scroll support)
- **`ModalScreen`** — for search overlay, confirmation dialogs, resolve-open-point dialog
- **`Footer`** — automatically shows current BINDINGS as key hints
- **`Header`** — shows app title and clock
- **`ScrollableContainer`** — wraps the Subject Detail content so all four sections scroll together
- **CSS theming** — all colors, spacing, and layout via `.tcss` files

### Modal Screens for Input

When the user presses `a` (add task), `n` (add note), `o` (add open point), or `w` (add waiting), push a modal `Screen` with the appropriate input fields:

```python
class AddTaskScreen(ModalScreen):
    """Modal for adding a new task."""

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("New Task"),
            Input(placeholder="What needs to be done?", id="task-text"),
            Select(options=[("must", "must"), ("should", "should"), ("if-time", "if-time")], id="priority"),
            Button("Add", variant="primary", id="submit"),
            Button("Cancel", variant="default", id="cancel"),
            id="add-task-dialog",
        )
```

### Reactive Data Flow

1. All data lives in SQLite
2. A `Database` class wraps `sqlite3` with methods for each operation (CRUD for each entity)
3. Widgets call `Database` methods and then refresh themselves via `self.refresh()` or Textual's message system
4. Use Textual's `work` decorator for any DB operations that should be async (though `sqlite3` stdlib is synchronous, which is fine — just avoid blocking the UI on large reads)
5. Use Textual's `on_mount` to load initial data
6. After mutations, post a custom `DataChanged` message so sibling widgets can refresh

## Keyboard Controls

### Global (defined in App.BINDINGS)
- `Tab` / `Shift+Tab` — handled by TabbedContent automatically
- `/` — push SearchScreen (modal)
- `q` — quit
- `?` — push HelpScreen (modal)

### Subjects List
- `a` — push AddSubjectScreen
- `Enter` — push SubjectDetailScreen for selected subject
- `p` — toggle pin on selected subject
- `shift+a` — toggle show/hide archived subjects
- `x` — archive subject (with confirmation via ModalScreen)

### Subject Detail Screen
- `Escape` — pop screen, back to subjects
- `1` / `2` / `3` / `4` — focus sections: tasks / open points / waiting / notes

#### Tasks section:
- `a` — push AddTaskScreen
- `e` — push EditTaskScreen for selected task
- `d` — toggle done
- `b` — toggle blocked
- `s` — cycle status: todo → in-progress → done → blocked
- `p` — cycle priority: must → should → if-time
- `t` — toggle "today" flag (adds/removes from Today view)
- `w` — cycle target day: mon → tue → wed → thu → fri → anytime
- `x` — delete task (confirm)

#### Open Points section:
- `a` or `o` — push AddOpenPointScreen
- `e` — edit text
- `c` — add/edit context
- `r` — push ResolveScreen (prompts for resolution note)
- `s` — cycle status: open → parked → resolved
- `x` — delete

#### Waiting On section:
- `a` — push AddWaitingScreen (fields: what, who, due date)
- `e` — edit
- `s` — cycle status: waiting → received → overdue → cancelled
- `n` — edit follow-up notes
- `x` — delete

#### Notes section:
- `a` or `n` — push AddNoteScreen (with TextArea for multiline input)
- `e` — push EditNoteScreen (TextArea pre-filled)
- `x` — delete note

### Today View
- `d` — toggle done
- `s` — cycle status
- `p` — cycle priority
- `Enter` — push SubjectDetailScreen for that task's subject
- Tasks cannot be added here — go to a subject and flag with `t`

### This Week View
- Same controls as Today
- `w` — change target day
- `Enter` — push SubjectDetailScreen

## Behavior Details

### Week Rollover
On startup, read `week_of` from the `meta` table and compare to current Monday (use `datetime.date.today()` and `isocalendar()`):
- `UPDATE tasks SET today = 0` — clear all today flags
- `UPDATE tasks SET day = NULL WHERE status != 'done'` — reset day assignments
- `DELETE FROM tasks WHERE status = 'done' AND completed_at < date('now', '-14 days')` — prune old done tasks
- `INSERT OR REPLACE INTO meta VALUES ('week_of', ?)` — update to current Monday

### Search (`/`)
Push a `SearchScreen` (modal) with an `Input` at the top. As the user types, query the UNION ALL search query and display results in a `ListView` below. Enter on a result dismisses the modal and navigates to the item (pushes SubjectDetailScreen if needed).

### Persistence
Python's `sqlite3` is synchronous and built-in — no pip install needed for the DB layer. Wrap it in a `Database` class. Every mutation immediately writes to disk. Enable WAL mode and foreign keys on connect:

```python
import sqlite3
from pathlib import Path

class Database:
    def __init__(self, path: Path = Path.home() / ".tracker" / "tracker.db"):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()
```

### Color Scheme (via tracker.tcss)

Use Textual's CSS system. Define color variables and classes:

```css
/* tracker.tcss */

Screen {
    background: $surface;
}

.priority-must {
    color: red;
}

.priority-should {
    color: yellow;
}

.priority-if-time {
    color: $text-muted;
}

.status-done {
    color: green;
    text-style: strike;
}

.status-blocked {
    color: red;
    text-style: bold;
}

.status-in-progress {
    color: cyan;
}

.status-open {
    color: magenta;
}

.status-parked {
    color: $text-muted;
    text-style: italic;
}

.status-resolved {
    color: green;
    text-style: strike;
}

.status-overdue {
    color: red;
    text-style: bold;
}

.subject-pinned {
    color: $accent;
    text-style: bold;
}
```

### Empty States
- Subjects list: "No subjects yet. Press `a` to create your first one — a project, client, or anything you're tracking."
- Subject with no tasks: "No tasks. Press `a` to add one."
- Subject with no open points: "No open questions. Press `o` to add something that needs discussing or deciding."
- Subject with no notes: "No notes yet. Press `n` to start a log."
- Today empty: "Nothing planned for today. Go to a subject and press `t` to pull tasks in."
- Waiting On empty: "Nothing pending from anyone. Either you're self-sufficient or you're forgetting to track delegations."

## File Structure

```
tracker/
├── pyproject.toml              # Project config, dependencies: textual
├── tracker/
│   ├── __init__.py
│   ├── app.py                  # TrackerApp class, top-level TabbedContent
│   ├── db.py                   # Database class — SQLite connection, schema, all queries
│   ├── models.py               # Dataclasses for Subject, Task, OpenPoint, WaitingItem, Note
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── subject_detail.py   # SubjectDetailScreen — full subject dashboard
│   │   ├── add_task.py         # AddTaskScreen (ModalScreen)
│   │   ├── add_note.py         # AddNoteScreen (ModalScreen with TextArea)
│   │   ├── add_open_point.py   # AddOpenPointScreen (ModalScreen)
│   │   ├── add_waiting.py      # AddWaitingScreen (ModalScreen)
│   │   ├── resolve_point.py    # ResolveScreen (ModalScreen — resolution note)
│   │   ├── search.py           # SearchScreen (ModalScreen with live results)
│   │   ├── confirm.py          # Generic confirmation ModalScreen
│   │   └── help.py             # HelpScreen (ModalScreen)
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── subjects_list.py    # SubjectsList widget (ListView of subjects)
│   │   ├── today_view.py       # TodayView widget
│   │   ├── week_view.py        # WeekView widget
│   │   ├── task_list.py        # TaskList widget (used in Subject Detail)
│   │   ├── open_points_list.py # OpenPointsList widget
│   │   ├── waiting_list.py     # WaitingList widget
│   │   └── notes_list.py       # NotesList widget
│   └── tracker.tcss            # All Textual CSS styles
└── README.md
```

## Entry Point

```bash
python -m tracker
```

Add a `__main__.py`:
```python
# tracker/__main__.py
from tracker.app import TrackerApp

app = TrackerApp()
app.run()
```

Also add a console script in `pyproject.toml` so it can be installed as a command:
```toml
[project.scripts]
tt = "tracker.app:main"
```

With a `main()` function in `app.py`:
```python
def main():
    app = TrackerApp()
    app.run()
```

## Implementation Notes

- Use Textual's `BINDINGS` class variable for all key bindings — the `Footer` widget auto-renders them
- Use `@on(ListView.Selected)` and `@on(Button.Pressed)` decorators for event handling
- Use Textual's `ScrollableContainer` to wrap Subject Detail content
- Use `Collapsible` widgets for each section in Subject Detail with counts in titles: "Tasks (3 open)", "Open Points (2 open)", etc.
- For notes: use Textual's `TextArea` widget which natively supports multiline editing with scrolling
- Use `ModalScreen` for all input dialogs — keeps the underlying screen visible but dimmed
- Use Python dataclasses in `models.py` to map SQLite rows to typed objects
- Use `sqlite3.Row` as the row factory so query results can be accessed by column name
- `Textual` handles terminal resize automatically
- Textual's built-in command palette (`ctrl+p`) is available for free — consider registering custom commands
- Use `self.notify()` for toast-style feedback after mutations ("Task added", "Note saved", etc.)
- Use Textual's dark/light theme toggle (built-in with `ctrl+d`) for free
