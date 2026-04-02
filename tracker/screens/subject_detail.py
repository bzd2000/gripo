"""SubjectDetailScreen — shows all detail sections for a subject."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Collapsible, Footer, Header, Label
from textual.containers import ScrollableContainer

from tracker.db import Database
from tracker.messages import DataChanged
from tracker.widgets.follow_ups_list import FollowUpsList
from tracker.widgets.notes_list import NotesList
from tracker.widgets.open_points_list import OpenPointsList
from tracker.widgets.task_list import TaskList


class SubjectDetailScreen(Screen):
    """Detail screen for a single subject."""

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
        tasks = self._db.list_tasks(self._subject_id)
        return sum(1 for t in tasks if t.status not in ("done",))

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
            with Collapsible(title=self._open_points_title(), id="open-points-collapsible"):
                yield OpenPointsList(self._db, self._subject_id)
            with Collapsible(title=self._follow_ups_title(), id="follow-ups-collapsible"):
                yield FollowUpsList(self._db, self._subject_id)
            with Collapsible(title=self._notes_title(), id="notes-collapsible"):
                yield NotesList(self._db, self._subject_id)
        yield Footer()

    def _tasks_title(self) -> str:
        count = self._task_count()
        return f"Tasks ({count} open)"

    def _open_points_count(self) -> int:
        points = self._db.list_open_points(self._subject_id)
        return sum(1 for p in points if p.status == "open")

    def _open_points_title(self) -> str:
        count = self._open_points_count()
        return f"Open Points ({count} open)"

    def _follow_ups_count(self) -> int:
        fus = self._db.list_follow_ups(self._subject_id)
        return sum(1 for fu in fus if fu.status == "waiting")

    def _follow_ups_title(self) -> str:
        count = self._follow_ups_count()
        return f"Follow-Ups ({count} pending)"

    def _notes_count(self) -> int:
        return len(self._db.list_notes(self._subject_id))

    def _notes_title(self) -> str:
        count = self._notes_count()
        return f"Notes ({count} entries)"

    def on_data_changed(self, message: DataChanged) -> None:
        """Refresh all collapsible titles when data changes."""
        self.query_one("#tasks-collapsible", Collapsible).title = self._tasks_title()
        self.query_one("#open-points-collapsible", Collapsible).title = self._open_points_title()
        self.query_one("#follow-ups-collapsible", Collapsible).title = self._follow_ups_title()
        self.query_one("#notes-collapsible", Collapsible).title = self._notes_title()

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
