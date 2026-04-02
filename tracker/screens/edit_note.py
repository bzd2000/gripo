"""EditNoteScreen — modal for editing an existing markdown note."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea
from textual.containers import Horizontal, Vertical

from tracker.models import Note


class EditNoteScreen(ModalScreen["str | None"]):
    """Modal screen for editing an existing note.

    Takes a Note in constructor and pre-fills the TextArea with existing content.
    Dismisses with the updated content string on success, or None on cancel.
    """

    DEFAULT_CSS = """
    EditNoteScreen {
        align: center middle;
    }

    EditNoteScreen .modal-dialog {
        width: 80;
        height: 30;
    }

    EditNoteScreen TextArea {
        height: 1fr;
    }
    """

    def __init__(self, note: Note) -> None:
        super().__init__()
        self._note = note

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("Edit Note (Markdown)")
            yield TextArea(self._note.content, language="markdown", id="note-area")
            with Horizontal():
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#note-area", TextArea).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._submit()
        else:
            self.dismiss(None)

    def _submit(self) -> None:
        content = self.query_one("#note-area", TextArea).text.strip()
        if not content:
            self.query_one("#note-area", TextArea).focus()
            return
        self.dismiss(content)
