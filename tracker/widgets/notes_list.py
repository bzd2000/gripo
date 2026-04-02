"""NotesList widget — displays notes for a subject."""

from __future__ import annotations

import re

from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView

from tracker.db import Database
from tracker.messages import DataChanged
from tracker.models import Note
from tracker.screens.add_note import AddNoteScreen
from tracker.screens.confirm import ConfirmScreen
from tracker.screens.edit_note import EditNoteScreen

_MD_STRIP_RE = re.compile(r"[#*_`~\[\]>]")


def _strip_markdown(text: str) -> str:
    """Remove common markdown syntax characters and collapse newlines."""
    text = _MD_STRIP_RE.sub("", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return text.strip()


def _note_label(note: Note) -> str:
    date = note.created_at[:10]
    preview = _strip_markdown(note.content)
    if len(preview) > 80:
        preview = preview[:77] + "..."
    return f"{date}  {preview}"


class NotesList(ListView):
    """ListView that shows notes for a given subject, newest first."""

    BINDINGS = [
        ("a", "add_note", "Add note"),
        ("n", "add_note", "Add note"),
        ("e", "edit_note", "Edit note"),
        ("x", "delete_note", "Delete note"),
    ]

    def __init__(self, db: Database, subject_id: str) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Rebuild the list from the database."""
        self.clear()
        notes = self._db.list_notes(self._subject_id)
        if not notes:
            item = ListItem(Label("No notes yet. Press n to start a log.", classes="empty-state"))
            item._note_id = None  # type: ignore[attr-defined]
            self.append(item)
        else:
            for note in notes:
                label = Label(_note_label(note))
                item = ListItem(label)
                item._note_id = note.id  # type: ignore[attr-defined]
                self.append(item)

    def _highlighted_note_id(self) -> str | None:
        if self.highlighted_child is None:
            return None
        return getattr(self.highlighted_child, "_note_id", None)

    def _highlighted_note(self) -> Note | None:
        note_id = self._highlighted_note_id()
        if not note_id:
            return None
        return self._db.get_note(note_id)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_add_note(self) -> None:
        def _on_result(content: str | None) -> None:
            if content:
                self._db.add_note(subject_id=self._subject_id, content=content)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Note added")

        self.app.push_screen(AddNoteScreen(), _on_result)

    def action_edit_note(self) -> None:
        note = self._highlighted_note()
        if not note:
            return

        def _on_result(content: str | None) -> None:
            if content:
                self._db.update_note(note.id, content=content)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Note updated")

        self.app.push_screen(EditNoteScreen(note), _on_result)

    def action_delete_note(self) -> None:
        note = self._highlighted_note()
        if not note:
            return

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._db.soft_delete_note(note.id)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Note deleted")

        self.app.push_screen(ConfirmScreen("Delete this note?"), _on_confirm)
