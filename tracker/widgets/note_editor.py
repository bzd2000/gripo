"""NoteEditor widget — markdown rendered content with edit toggle. First line = title."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Label

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.comment_editor import CommentEditor


class NoteEditor(Container):
    """Note editor using CommentEditor. First line of content is the title."""

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
        heading = "Edit Note" if self._note else "New Note"
        initial_content = self._note.content if self._note else ""

        yield Label(heading, classes="overview-col-header")
        yield CommentEditor(text=initial_content, id="note-content-editor")

    def on_mount(self) -> None:
        # Start in edit mode for new notes
        if not self._note:
            editor = self.query_one("#note-content-editor", CommentEditor)
            editor._enter_edit()

    def action_save(self) -> None:
        content = self.query_one("#note-content-editor", CommentEditor).text.strip()
        if not content:
            self.notify("Note content cannot be empty.", severity="error")
            return

        # First line is the title
        title = content.split("\n", 1)[0].strip().lstrip("#").strip()

        if self._note_id:
            self._db.update_note(self._note_id, content, title=title)
            saved_id = self._note_id
        else:
            saved_id = self._db.add_note(subject_id=self._subject_id, content=content, title=title)

        self.post_message(DataChanged())
        self.post_message(ContentSaved("note_editor", {"subject_id": self._subject_id, "note_id": saved_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
