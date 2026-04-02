"""AddNoteScreen — modal for creating a new markdown note."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea
from textual.containers import Horizontal, Vertical


class AddNoteScreen(ModalScreen["str | None"]):
    """Modal screen for creating a new note.

    Dismisses with the note content string on success, or None on cancel.
    """

    DEFAULT_CSS = """
    AddNoteScreen {
        align: center middle;
    }

    AddNoteScreen .modal-dialog {
        width: 80;
        height: 30;
    }

    AddNoteScreen TextArea {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("New Note (Markdown)")
            yield TextArea(language="markdown", id="note-area")
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
