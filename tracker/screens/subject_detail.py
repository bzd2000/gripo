"""SubjectDetailScreen — shows all detail sections for a subject."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Collapsible, Footer, Header, Label
from textual.containers import ScrollableContainer

from tracker.db import Database
from tracker.messages import DataChanged
from tracker.widgets.notes_list import NotesList
from tracker.widgets.task_list import TaskList


class SubjectDetailScreen(Screen):
    """Detail screen for a single subject.

    Shows tasks (functional), and placeholder sections for open points,
    follow-ups, and notes.
    """

    BINDINGS = [
        Binding("escape", "pop_screen", "Back"),
        Binding("1", "focus_section('tasks')", "Tasks"),
        Binding("2", "focus_section('open-points')", "Open Points"),
        Binding("3", "focus_section('follow-ups')", "Follow-Ups"),
        Binding("4", "focus_section('notes')", "Notes"),
    ]

    def __init__(self, db: Database, subject_id: str) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id

    def _task_count(self) -> int:
        return len(self._db.list_tasks(self._subject_id))

    def _subject_label(self) -> str:
        subject = self._db.get_subject(self._subject_id)
        if not subject:
            return "Unknown Subject"
        pin = " 📌" if subject.pinned else ""
        return f"{subject.name}{pin}"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label(self._subject_label(), classes="subject-header")
        with ScrollableContainer():
            with Collapsible(title=self._tasks_title(), id="tasks-collapsible"):
                yield TaskList(self._db, self._subject_id)
            with Collapsible(title="Open Points", id="open-points-collapsible"):
                yield Label("No open points yet.", classes="empty-state")
            with Collapsible(title="Follow-Ups", id="follow-ups-collapsible"):
                yield Label("No follow-ups yet.", classes="empty-state")
            with Collapsible(title=self._notes_title(), id="notes-collapsible"):
                yield NotesList(self._db, self._subject_id)
        yield Footer()

    def _tasks_title(self) -> str:
        count = self._task_count()
        return f"Tasks ({count})"

    def _notes_count(self) -> int:
        return len(self._db.list_notes(self._subject_id))

    def _notes_title(self) -> str:
        count = self._notes_count()
        return f"Notes ({count} entries)"

    def on_data_changed(self, message: DataChanged) -> None:
        """Refresh collapsible titles when data changes."""
        tasks_collapsible = self.query_one("#tasks-collapsible", Collapsible)
        tasks_collapsible.title = self._tasks_title()
        notes_collapsible = self.query_one("#notes-collapsible", Collapsible)
        notes_collapsible.title = self._notes_title()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()

    def action_focus_section(self, section: str) -> None:
        id_map = {
            "tasks": "#tasks-collapsible",
            "open-points": "#open-points-collapsible",
            "follow-ups": "#follow-ups-collapsible",
            "notes": "#notes-collapsible",
        }
        selector = id_map.get(section)
        if selector:
            try:
                widget = self.query_one(selector)
                widget.focus()
            except Exception:
                pass
