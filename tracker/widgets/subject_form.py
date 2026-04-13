"""SubjectForm widget — inline form for creating or editing a subject."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label, Select

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged

_TYPE_OPTIONS = [
    ("Person", "person"),
    ("Team", "team"),
    ("Project", "project"),
    ("Board", "board"),
]


class SubjectForm(Container):
    """Single-pane form for adding or editing a subject."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save"),
    ]

    def __init__(self, db: Database, subject_id: Optional[str] = None) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id
        self._subject = db.get_subject(subject_id) if subject_id else None

    def compose(self) -> ComposeResult:
        title = "Edit Subject" if self._subject else "New Subject"
        initial_name = self._subject.name if self._subject else ""
        current_type = self._subject.subject_type if self._subject else None

        yield Label(title, classes="overview-col-header")
        yield Label("Name", classes="field-label")
        yield Input(value=initial_name, placeholder="Subject name", id="subject-name-input")
        yield Label("Type", classes="field-label")
        yield Select(
            options=_TYPE_OPTIONS,
            value=current_type if current_type else Select.NULL,
            allow_blank=True,
            id="subject-type-select",
            compact=True,
        )

    def on_mount(self) -> None:
        self.query_one("#subject-name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "subject-name-input":
            self.action_save()

    def action_save(self) -> None:
        name = self.query_one("#subject-name-input", Input).value.strip()
        if not name:
            self.notify("Subject name cannot be empty.", severity="error")
            return

        type_select = self.query_one("#subject-type-select", Select)
        subject_type = str(type_select.value) if type_select.value != Select.NULL else None

        if self._subject_id:
            self._db.update_subject(self._subject_id, name, subject_type=subject_type)
            saved_id = self._subject_id
        else:
            saved_id = self._db.add_subject(name, subject_type=subject_type)

        self.post_message(DataChanged())
        self.post_message(ContentSaved("subject_form", {"subject_id": saved_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
