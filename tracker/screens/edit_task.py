"""EditTaskScreen — modal for editing an existing task."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select
from textual.containers import Horizontal, Vertical

from tracker.models import Task
from tracker.screens.add_task import TaskData, _PRIORITY_OPTIONS, _CATEGORY_OPTIONS


class EditTaskScreen(ModalScreen["TaskData | None"]):
    """Modal screen for editing an existing task.

    Takes a Task in constructor and pre-fills all fields.
    Dismisses with TaskData on success, or None on cancel.
    """

    DEFAULT_CSS = """
    EditTaskScreen {
        align: center middle;
    }
    """

    def __init__(self, task: Task) -> None:
        super().__init__()
        self._task = task

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("Edit Task")
            yield Input(value=self._task.text, id="text-input")
            yield Select(
                _PRIORITY_OPTIONS,
                prompt="Priority",
                value=self._task.priority,
                id="priority-select",
            )
            yield Select(
                _CATEGORY_OPTIONS,
                prompt="Category (optional)",
                allow_blank=True,
                value=self._task.category if self._task.category else Select.BLANK,
                id="category-select",
            )
            yield Input(
                value=self._task.due_date or "",
                placeholder="Due date (YYYY-MM-DD, optional)",
                id="due-date-input",
            )
            with Horizontal():
                yield Button("Save", variant="primary", id="save-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Allow pressing Enter from the text input to submit."""
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

        priority_select = self.query_one("#priority-select", Select)
        priority = str(priority_select.value) if priority_select.value != Select.BLANK else "should"

        category_select = self.query_one("#category-select", Select)
        category: Optional[str] = (
            str(category_select.value)
            if category_select.value != Select.BLANK
            else None
        )

        due_date = self.query_one("#due-date-input", Input).value.strip() or None
        self.dismiss(TaskData(text=text, priority=priority, category=category, due_date=due_date))
