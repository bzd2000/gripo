"""TaskForm widget — inline form for adding or editing a task."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label, Select

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.comment_editor import CommentEditor
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


class TaskForm(Container):
    """Inline form: top container (fields) + bottom container (comment)."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: Database,
        subject_id: str,
        task_id: Optional[str] = None,
        milestone_id: Optional[str] = None,
    ) -> None:
        super().__init__(classes="item-form")
        self._db = db
        self._subject_id = subject_id
        self._task_id = task_id
        self._task_record = db.get_task(task_id) if task_id else None
        self._default_milestone_id = milestone_id

    def compose(self) -> ComposeResult:
        is_edit = self._task_record is not None
        title = "Edit Task" if is_edit else "New Task"

        initial_text = self._task_record.text if self._task_record else ""
        initial_priority = self._task_record.priority if self._task_record else "should"
        initial_category = self._task_record.category if self._task_record else None
        initial_comment = self._task_record.comment if self._task_record else ""

        if is_edit:
            initial_due_date = self._task_record.due_date or ""
        else:
            initial_due_date = None

        with Container(classes="item-form-fields"):
            yield Label(title, classes="overview-col-header")
            yield Label("Text", classes="field-label")
            yield Input(value=initial_text, placeholder="Task text", id="task-text-input")
            yield Label("Priority", classes="field-label")
            yield Select(
                options=_PRIORITY_OPTIONS,
                value=initial_priority,
                id="task-priority-select",
                compact=True,
            )
            yield Label("Category", classes="field-label")
            yield Select(
                options=_CATEGORY_OPTIONS,
                value=initial_category if initial_category else Select.NULL,
                allow_blank=True,
                id="task-category-select",
                compact=True,
            )
            yield Label("Due date", classes="field-label")
            yield DateInput(
                value=initial_due_date,
                placeholder="YYYY-MM-DD",
                id="task-due-date-input",
            )
            # Milestone link
            milestones = self._db.list_milestones(self._subject_id)
            active_ms = [(m.name, m.id) for m in milestones if m.status == "active"]
            if active_ms:
                current_ms_id = self._task_record.milestone_id if self._task_record else self._default_milestone_id
                yield Label("Milestone", classes="field-label")
                yield Select(
                    options=active_ms,
                    value=current_ms_id if current_ms_id else Select.NULL,
                    allow_blank=True,
                    id="task-milestone-select",
                    compact=True,
                )
        yield CommentEditor(text=initial_comment or "", id="task-comment-editor")

    def on_mount(self) -> None:
        self.query_one("#task-text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "task-text-input":
            self.action_save()

    def action_save(self) -> None:
        text = self.query_one("#task-text-input", Input).value.strip()
        if not text:
            self.notify("Task text cannot be empty.", severity="error")
            return

        priority_select = self.query_one("#task-priority-select", Select)
        category_select = self.query_one("#task-category-select", Select)
        due_date_input = self.query_one("#task-due-date-input", DateInput)
        comment_editor = self.query_one("#task-comment-editor", CommentEditor)

        priority = str(priority_select.value) if priority_select.value != Select.NULL else "should"
        category = str(category_select.value) if category_select.value != Select.NULL else None
        due_date = due_date_input.date_value
        comment = comment_editor.text.strip() or None

        # Milestone link (optional)
        milestone_id = None
        try:
            ms_select = self.query_one("#task-milestone-select", Select)
            milestone_id = str(ms_select.value) if ms_select.value != Select.NULL else None
        except Exception:
            pass

        if self._task_id:
            self._db.update_task(
                self._task_id, text=text, priority=priority,
                category=category, due_date=due_date, comment=comment,
            )
            self._db.link_task_to_milestone(self._task_id, milestone_id)
            saved_id = self._task_id
        else:
            saved_id = self._db.add_task(
                subject_id=self._subject_id, text=text, priority=priority,
                category=category, due_date=due_date, comment=comment,
            )
            if milestone_id:
                self._db.link_task_to_milestone(saved_id, milestone_id)

        self.post_message(DataChanged())
        saved_data = {"subject_id": self._subject_id, "task_id": saved_id}
        if milestone_id:
            saved_data["milestone_id"] = milestone_id
        self.post_message(ContentSaved("task_form", saved_data))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
