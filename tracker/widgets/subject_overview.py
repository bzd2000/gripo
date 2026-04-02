"""SubjectOverview widget — summary view for a single subject."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widget import Widget
from textual.widgets import Label, Markdown, Static

from tracker.db import Database

_TASK_STATUS_ICON = {
    "todo": "○",
    "in-progress": "●",
    "done": "✓",
    "blocked": "✗",
}

_FU_STATUS_ICON = {
    "waiting": "⏳",
    "received": "✓",
    "overdue": "‼",
    "cancelled": "✗",
}


class SubjectOverview(Widget):
    """Summary view for a subject showing important items from each section."""

    def __init__(self, db: Database, subject_id: str) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id

    def compose(self) -> ComposeResult:
        subject = self._db.get_subject(self._subject_id)
        if subject is None:
            yield Label("Subject not found.")
            return

        pin_str = " [pinned]" if subject.pinned else ""
        archived_str = " [archived]" if subject.archived else ""

        today = date.today()
        three_days_later = today + timedelta(days=3)

        with ScrollableContainer():
            # Header
            yield Static(
                f"[bold]{subject.name}[/bold]{pin_str}{archived_str}",
                id="subject-overview-header",
            )

            # Important Tasks section
            yield Static("[bold]Important Tasks[/bold]", classes="section-header")
            tasks = self._db.list_tasks(self._subject_id)
            important_tasks = []
            for t in tasks:
                if t.status == "done":
                    continue
                is_must = t.priority == "must"
                is_due_soon = (
                    t.due_date is not None
                    and today <= date.fromisoformat(t.due_date) <= three_days_later
                )
                if is_must or is_due_soon:
                    important_tasks.append(t)
            important_tasks = important_tasks[:5]

            if important_tasks:
                for t in important_tasks:
                    icon = _TASK_STATUS_ICON.get(t.status, "?")
                    due_str = f" (due {t.due_date})" if t.due_date else ""
                    yield Label(f"{icon} {t.text} [{t.priority}]{due_str}")
            else:
                yield Label("None", classes="empty-state")

            # Open Points section
            yield Static("[bold]Open Points[/bold]", classes="section-header")
            open_points = self._db.list_open_points(self._subject_id)
            open_open_points = [p for p in open_points if p.status == "open"][:5]

            if open_open_points:
                for p in open_open_points:
                    yield Label(f"? {p.text}")
            else:
                yield Label("None", classes="empty-state")

            # Pending Follow-Ups section
            yield Static("[bold]Pending Follow-Ups[/bold]", classes="section-header")
            follow_ups = self._db.list_follow_ups(self._subject_id)
            pending_fus = [f for f in follow_ups if f.status in ("waiting", "overdue")][:5]

            if pending_fus:
                for fu in pending_fus:
                    icon = _FU_STATUS_ICON.get(fu.status, "?")
                    due_str = f" (due {fu.due_by})" if fu.due_by else ""
                    yield Label(f"{icon} {fu.text} from {fu.owner}{due_str}")
            else:
                yield Label("None", classes="empty-state")

            # Recent Notes section
            yield Static("[bold]Recent Notes[/bold]", classes="section-header")
            notes = self._db.list_notes(self._subject_id)
            recent_notes = notes[:3]

            if recent_notes:
                for note in recent_notes:
                    date_str = note.created_at[:10]
                    yield Static(f"[dim]{date_str}[/dim]")
                    yield Markdown(note.content)
            else:
                yield Label("None", classes="empty-state")
