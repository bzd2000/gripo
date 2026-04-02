"""AddOpenPointScreen — modal for creating or editing an open point."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Horizontal, Vertical


@dataclass
class OpenPointData:
    """Data returned from AddOpenPointScreen."""

    text: str
    context: Optional[str]


class AddOpenPointScreen(ModalScreen["OpenPointData | None"]):
    """Modal screen for creating or editing an open point.

    Dismisses with OpenPointData on success, or None on cancel.
    When pre-filled with existing text/context, title changes to 'Edit Open Point'.
    """

    DEFAULT_CSS = """
    AddOpenPointScreen {
        align: center middle;
    }
    """

    def __init__(self, text: str = "", context: str = "") -> None:
        super().__init__()
        self._initial_text = text
        self._initial_context = context

    def compose(self) -> ComposeResult:
        editing = bool(self._initial_text)
        title = "Edit Open Point" if editing else "New Open Point"
        btn_label = "Save" if editing else "Add"
        with Vertical(classes="modal-dialog"):
            yield Label(title)
            yield Input(
                value=self._initial_text,
                placeholder="What needs discussing or deciding?",
                id="text-input",
            )
            yield Input(
                value=self._initial_context,
                placeholder="Context (optional)",
                id="context-input",
            )
            with Horizontal():
                yield Button(btn_label, variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "text-input":
            self.query_one("#context-input", Input).focus()
        else:
            self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            self._submit()
        else:
            self.dismiss(None)

    def _submit(self) -> None:
        text = self.query_one("#text-input", Input).value.strip()
        if not text:
            self.query_one("#text-input", Input).focus()
            return
        context = self.query_one("#context-input", Input).value.strip() or None
        self.dismiss(OpenPointData(text=text, context=context))
