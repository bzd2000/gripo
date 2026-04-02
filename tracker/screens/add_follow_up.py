"""AddFollowUpScreen — modal for creating or editing a follow-up."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Horizontal, Vertical


@dataclass
class FollowUpData:
    """Data returned from AddFollowUpScreen."""

    text: str
    owner: str
    due_by: Optional[str]


class AddFollowUpScreen(ModalScreen["FollowUpData | None"]):
    """Modal screen for creating or editing a follow-up.

    Dismisses with FollowUpData on success, or None on cancel.
    When pre-filled, title changes to 'Edit Follow-Up'.
    """

    DEFAULT_CSS = """
    AddFollowUpScreen {
        align: center middle;
    }
    """

    def __init__(self, text: str = "", owner: str = "", due_by: str = "") -> None:
        super().__init__()
        self._initial_text = text
        self._initial_owner = owner
        self._initial_due_by = due_by

    def compose(self) -> ComposeResult:
        editing = bool(self._initial_text or self._initial_owner)
        title = "Edit Follow-Up" if editing else "New Follow-Up"
        btn_label = "Save" if editing else "Add"
        with Vertical(classes="modal-dialog"):
            yield Label(title)
            yield Input(
                value=self._initial_text,
                placeholder="What are you waiting for?",
                id="text-input",
            )
            yield Input(
                value=self._initial_owner,
                placeholder="Owner (who owes you this)",
                id="owner-input",
            )
            yield Input(
                value=self._initial_due_by,
                placeholder="Due date YYYY-MM-DD (optional)",
                id="due-by-input",
            )
            with Horizontal():
                yield Button(btn_label, variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "text-input":
            self.query_one("#owner-input", Input).focus()
        elif event.input.id == "owner-input":
            self.query_one("#due-by-input", Input).focus()
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
        owner = self.query_one("#owner-input", Input).value.strip()
        if not owner:
            self.query_one("#owner-input", Input).focus()
            return
        due_by = self.query_one("#due-by-input", Input).value.strip() or None
        self.dismiss(FollowUpData(text=text, owner=owner, due_by=due_by))
