"""ResolveScreen — modal for entering a resolution note on an open point."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea
from textual.containers import Horizontal, Vertical


class ResolveScreen(ModalScreen["str | None"]):
    """Modal screen for recording how an open point was resolved.

    Dismisses with the resolution note string on success, or None on cancel.
    """

    DEFAULT_CSS = """
    ResolveScreen {
        align: center middle;
    }

    ResolveScreen .modal-dialog {
        width: 80;
        height: 24;
    }

    ResolveScreen TextArea {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("Resolution Note")
            yield TextArea(id="note-area")
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
        note = self.query_one("#note-area", TextArea).text.strip()
        if not note:
            self.query_one("#note-area", TextArea).focus()
            return
        self.dismiss(note)
