"""ConfirmScreen — modal asking user to confirm a destructive action."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual.containers import Horizontal, Vertical


class ConfirmScreen(ModalScreen[bool]):
    """Modal screen presenting a confirmation dialog.

    Dismisses with True when the user confirms, False when cancelled.
    """

    DEFAULT_CSS = """
    ConfirmScreen {
        align: center middle;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label(self._message)
            with Horizontal():
                yield Button("Confirm", variant="error", id="confirm-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)
