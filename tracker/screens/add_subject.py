"""AddSubjectScreen — modal for creating a new subject."""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Horizontal, Vertical


class AddSubjectScreen(ModalScreen[str | None]):
    """Modal screen for creating a new subject.

    Dismisses with the subject name string on success, or None on cancel.
    """

    DEFAULT_CSS = """
    AddSubjectScreen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("New Subject")
            yield Input(placeholder="Subject name…", id="name-input")
            with Horizontal():
                yield Button("Add", variant="primary", id="add-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Allow pressing Enter from the input to submit."""
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            self._submit()
        else:
            self.dismiss(None)

    def _submit(self) -> None:
        name = self.query_one("#name-input", Input).value.strip()
        if name:
            self.dismiss(name)
        else:
            self.query_one("#name-input", Input).focus()
