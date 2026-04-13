"""SubjectForm widget — inline form for creating or editing a subject."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged


class SubjectForm(Container):
    """Single-pane form for adding or editing a subject."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: Database, subject_id: Optional[str] = None) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id
        self._subject = db.get_subject(subject_id) if subject_id else None

    def compose(self) -> ComposeResult:
        title = "Edit Subject" if self._subject else "New Subject"
        initial_name = self._subject.name if self._subject else ""
        yield Label(title, classes="overview-col-header")
        yield Label("Name", classes="field-label")
        yield Input(value=initial_name, placeholder="Subject name", id="subject-name-input")

    def on_mount(self) -> None:
        self.query_one("#subject-name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if not name:
            self.notify("Subject name cannot be empty.", severity="error")
            return

        if self._subject_id:
            self._db.rename_subject(self._subject_id, name)
            saved_id = self._subject_id
        else:
            saved_id = self._db.add_subject(name)

        self.post_message(DataChanged())
        self.post_message(ContentSaved("subject_form", {"subject_id": saved_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
