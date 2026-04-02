"""TaskForm widget — inline form for adding or editing a task."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Input, Label, Select, TextArea

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.date_input import DateInput

_PRIORITY_OPTIONS = [
    ("must", "must"),
    ("should", "should"),
    ("if-time", "if-time"),
]

_CATEGORY_OPTIONS = [
    ("delivery", "delivery"),
    ("admin", "admin"),
    ("people", "people"),
    ("strategy", "strategy"),
    ("meeting", "meeting"),
    ("other", "other"),
]


class TaskForm(Widget):
    """Inline form for adding or editing a task."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: Database,
        subject_id: str,
        task_id: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id
        self._task_id = task_id
        self._task = db.get_task(task_id) if task_id else None

    def compose(self) -> ComposeResult:
        is_edit = self._task is not None
        title = "Edit Task" if is_edit else "New Task"

        initial_text = self._task.text if self._task else ""
        initial_priority = self._task.priority if self._task else "should"
        initial_category = self._task.category if self._task else None
        initial_comment = self._task.comment if self._task else ""

        if is_edit:
            initial_due_date = self._task.due_date or ""
        else:
            initial_due_date = None  # DateInput will default to today

        with Vertical(classes="form-container"):
            yield Label(title, classes="form-title")
            yield Input(value=initial_text, placeholder="Task text", id="task-text-input")
            with Horizontal(classes="form-row"):
                with Vertical():
                    yield Label("Priority", classes="field-label")
                    yield Select(
                        options=_PRIORITY_OPTIONS,
                        value=initial_priority,
                        id="task-priority-select",
                    )
                with Vertical():
                    yield Label("Category", classes="field-label")
                    yield Select(
                        options=_CATEGORY_OPTIONS,
                        value=initial_category if initial_category else Select.BLANK,
                        allow_blank=True,
                        id="task-category-select",
                    )
                with Vertical():
                    yield Label("Due date", classes="field-label")
                    yield DateInput(
                        value=initial_due_date,
                        placeholder="YYYY-MM-DD",
                        id="task-due-date-input",
                    )
            yield Label("Comment", classes="field-label")
            yield TextArea(
                text=initial_comment or "",
                language="markdown",
                id="task-comment-area",
            )

    def on_mount(self) -> None:
        self.query_one("#task-text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "task-text-input":
            self.action_save()

    def action_save(self) -> None:
        text_input = self.query_one("#task-text-input", Input)
        priority_select = self.query_one("#task-priority-select", Select)
        category_select = self.query_one("#task-category-select", Select)
        due_date_input = self.query_one("#task-due-date-input", DateInput)
        comment_area = self.query_one("#task-comment-area", TextArea)

        text = text_input.value.strip()
        if not text:
            self.notify("Task text cannot be empty.", severity="error")
            return

        priority = str(priority_select.value) if priority_select.value != Select.BLANK else "should"
        category_val = category_select.value
        category = str(category_val) if category_val != Select.BLANK else None
        due_date = due_date_input.date_value
        comment = comment_area.text.strip() or None

        if self._task_id:
            self._db.update_task(
                self._task_id,
                text=text,
                priority=priority,
                category=category,
                due_date=due_date,
                comment=comment,
            )
            saved_id = self._task_id
        else:
            saved_id = self._db.add_task(
                subject_id=self._subject_id,
                text=text,
                priority=priority,
                category=category,
                due_date=due_date,
                comment=comment,
            )

        self.post_message(DataChanged())
        self.post_message(
            ContentSaved(
                "task_form",
                {"subject_id": self._subject_id, "task_id": saved_id},
            )
        )

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
