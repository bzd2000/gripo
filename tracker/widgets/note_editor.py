"""NoteEditor widget — inline editor for adding or editing a note."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Label, TextArea

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged


class NoteEditor(Widget):
    """Inline editor for adding or editing a note."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: Database,
        subject_id: str,
        note_id: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id
        self._note_id = note_id
        self._note = db.get_note(note_id) if note_id else None

    def compose(self) -> ComposeResult:
        title = "Edit Note" if self._note else "New Note"
        initial_content = self._note.content if self._note else ""

        with Vertical():
            yield Label(title)
            yield TextArea(
                text=initial_content,
                language="markdown",
                id="note-content-area",
            )

    def on_mount(self) -> None:
        self.query_one("#note-content-area", TextArea).focus()

    def action_save(self) -> None:
        content_area = self.query_one("#note-content-area", TextArea)
        content = content_area.text.strip()
        if not content:
            self.notify("Note content cannot be empty.", severity="error")
            return

        if self._note_id:
            self._db.update_note(self._note_id, content)
            saved_id = self._note_id
        else:
            saved_id = self._db.add_note(
                subject_id=self._subject_id,
                content=content,
            )

        self.post_message(DataChanged())
        self.post_message(
            ContentSaved(
                "note_editor",
                {"subject_id": self._subject_id, "note_id": saved_id},
            )
        )

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
