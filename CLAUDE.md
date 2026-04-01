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
pytest tests/test_db.py::test_add_task -v
```

## Architecture

### Data flow
All state lives in SQLite (`~/.tracker/tracker.db`). The `Database` class (`tracker/db.py`) wraps `sqlite3` with CRUD methods for each entity. Widgets call `Database` methods directly, then refresh via Textual's message system. After mutations, a custom `DataChanged` message notifies sibling widgets to refresh.

### Navigation model
- **Top-level**: `TabbedContent` with three tabs — Subjects (home), Today, This Week
- **Subject Detail**: pushed as a separate `Screen` (not a tab) via `push_screen()`
- **All input dialogs**: `ModalScreen` subclasses (add task, add note, search, confirm, etc.)

### Key modules
- `tracker/app.py` — `TrackerApp` root, top-level tabs and global bindings
- `tracker/db.py` — `Database` class, schema init, all SQL queries
- `tracker/models.py` — dataclasses mapping SQLite rows (Subject, Task, OpenPoint, WaitingItem, Note)
- `tracker/screens/` — `SubjectDetailScreen` + modal screens for input/search/confirm
- `tracker/widgets/` — `SubjectsList`, `TodayView`, `WeekView`, section list widgets
- `tracker/tracker.tcss` — all Textual CSS styling

### Data model
Five main tables: `subjects`, `tasks`, `open_points`, `waiting`, `notes`, plus a `meta` table for app state (e.g., `week_of` for week rollover logic). Subjects are the primary organizing unit — all other entities reference a subject via foreign key with CASCADE delete.

### Week rollover
On startup, compare `meta.week_of` to current Monday. If different: clear today flags, reset day assignments on non-done tasks, prune done tasks older than 14 days.

## Tech Constraints

- Python 3.10+ required
- Only external dependency is `textual` — SQLite uses stdlib `sqlite3`
- Enable WAL mode and foreign keys on every DB connection
- Database auto-creates at `~/.tracker/tracker.db` on first run
- Use `uuid` from stdlib for ID generation
- Entry point: `python -m tracker` via `__main__.py`, or `tt` console script
