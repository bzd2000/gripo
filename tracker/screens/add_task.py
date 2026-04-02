"""AddTaskScreen — modal for creating a new task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select
from textual.containers import Horizontal, Vertical


@dataclass
class TaskData:
    """Data returned from AddTaskScreen / EditTaskScreen."""

    text: str
    priority: str
    category: Optional[str]


_PRIORITY_OPTIONS = [
    ("Must do", "must"),
    ("Should do", "should"),
    ("If time", "if-time"),
]

_CATEGORY_OPTIONS = [
    ("Delivery", "delivery"),
    ("Admin", "admin"),
    ("People", "people"),
    ("Strategy", "strategy"),
    ("Meeting", "meeting"),
    ("Other", "other"),
]


class AddTaskScreen(ModalScreen["TaskData | None"]):
    """Modal screen for creating a new task.

    Dismisses with TaskData on success, or None on cancel.
    """

    DEFAULT_CSS = """
    AddTaskScreen {
        align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("New Task")
            yield Input(placeholder="Task description…", id="text-input")
            yield Select(
                _PRIORITY_OPTIONS,
                prompt="Priority",
                value="should",
                id="priority-select",
            )
            yield Select(
                _CATEGORY_OPTIONS,
                prompt="Category (optional)",
                allow_blank=True,
                id="category-select",
            )
            with Horizontal():
                yield Button("Add", variant="primary", id="add-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Allow pressing Enter from the text input to submit."""
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add-btn":
            self._submit()
        else:
            self.dismiss(None)

    def _submit(self) -> None:
        text = self.query_one("#text-input", Input).value.strip()
        if not text:
            self.query_one("#text-input", Input).focus()
            return

        priority_select = self.query_one("#priority-select", Select)
        priority = str(priority_select.value) if priority_select.value != Select.BLANK else "should"

        category_select = self.query_one("#category-select", Select)
        category: Optional[str] = (
            str(category_select.value)
            if category_select.value != Select.BLANK
            else None
        )

        self.dismiss(TaskData(text=text, priority=priority, category=category))
