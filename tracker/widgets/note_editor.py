"""NoteEditor widget — title input + markdown rendered content."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Input, Label

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.comment_editor import CommentEditor


class NoteEditor(Vertical):
    """Note editor: title on top, markdown content below."""

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
        initial_title = self._note.title if self._note else ""
        initial_content = self._note.content if self._note else ""

        yield Input(value=initial_title, placeholder="Title", id="note-title-input")
        yield CommentEditor(text=initial_content, id="note-content-editor")

    def on_mount(self) -> None:
        if self._note:
            self.query_one("#note-content-editor", CommentEditor).focus()
        else:
            self.query_one("#note-title-input", Input).focus()

    def action_save(self) -> None:
        title = self.query_one("#note-title-input", Input).value.strip()
        content = self.query_one("#note-content-editor", CommentEditor).text.strip()
        if not content:
            self.notify("Note content cannot be empty.", severity="error")
            return

        if self._note_id:
            self._db.update_note(self._note_id, content, title=title)
            saved_id = self._note_id
        else:
            saved_id = self._db.add_note(subject_id=self._subject_id, content=content, title=title)

        self.post_message(DataChanged())
        self.post_message(ContentSaved("note_editor", {"subject_id": self._subject_id, "note_id": saved_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
