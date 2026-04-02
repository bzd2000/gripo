"""SubjectForm widget — inline form for creating a new subject."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged


class SubjectForm(Container):
    """Single-pane form for adding a new subject."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db

    def compose(self) -> ComposeResult:
        yield Label("New Subject", classes="form-title")
        yield Input(placeholder="Subject name", id="subject-name-input")

    def on_mount(self) -> None:
        self.query_one("#subject-name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        name = event.value.strip()
        if not name:
            self.notify("Subject name cannot be empty.", severity="error")
            return
        subject_id = self._db.add_subject(name)
        self.post_message(DataChanged())
        self.post_message(ContentSaved("subject_form", {"subject_id": subject_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
