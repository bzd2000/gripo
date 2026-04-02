"""TaskList widget — displays tasks for a subject."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Label, ListItem, ListView

from tracker.db import Database
from tracker.messages import DataChanged
from tracker.models import Task
from tracker.screens.add_task import AddTaskScreen
from tracker.screens.confirm import ConfirmScreen
from tracker.screens.edit_task import EditTaskScreen

_STATUS_ICON = {
    "todo": "○",
    "in-progress": "●",
    "done": "✓",
    "blocked": "✗",
}

_STATUS_CYCLE = {
    "todo": "in-progress",
    "in-progress": "done",
    "done": "blocked",
    "blocked": "todo",
}

_PRIORITY_CYCLE = {
    "must": "should",
    "should": "if-time",
    "if-time": "must",
}

_DAY_CYCLE = {
    "mon": "tue",
    "tue": "wed",
    "wed": "thu",
    "thu": "fri",
    "fri": "anytime",
    "anytime": None,
    None: "mon",
}


def _task_label(task: Task) -> str:
    icon = _STATUS_ICON.get(task.status, "?")
    today_flag = " ☆" if task.today else ""
    day_label = f" [{task.day}]" if task.day else ""
    cat_label = f" ({task.category})" if task.category else ""
    due_label = f" due:{task.due_date}" if task.due_date else ""
    return f"{icon} {task.text}{cat_label} [{task.priority}]{today_flag}{day_label}{due_label}"


def _css_classes(task: Task) -> str:
    classes = [f"priority-{task.priority}", f"status-{task.status}"]
    return " ".join(classes)


class TaskList(ListView):
    """ListView that shows tasks for a given subject."""

    BINDINGS = [
        ("a", "add_task", "Add task"),
        ("e", "edit_task", "Edit task"),
        ("d", "toggle_done", "Toggle done"),
        ("b", "toggle_blocked", "Toggle blocked"),
        ("s", "cycle_status", "Cycle status"),
        ("p", "cycle_priority", "Cycle priority"),
        ("t", "toggle_today", "Toggle today"),
        ("w", "cycle_day", "Cycle day"),
        ("x", "delete_task", "Delete task"),
    ]

    def __init__(self, db: Database, subject_id: str) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Rebuild the list from the database."""
        self.clear()
        tasks = self._db.list_tasks(self._subject_id)
        if not tasks:
            item = ListItem(Label("No tasks yet. Press a to add one.", classes="empty-state"))
            item._task_id = None  # type: ignore[attr-defined]
            self.append(item)
        else:
            for task in tasks:
                label = Label(_task_label(task), classes=_css_classes(task))
                item = ListItem(label)
                item._task_id = task.id  # type: ignore[attr-defined]
                self.append(item)

    def _highlighted_task_id(self) -> str | None:
        if self.highlighted_child is None:
            return None
        return getattr(self.highlighted_child, "_task_id", None)

    def _highlighted_task(self) -> Task | None:
        task_id = self._highlighted_task_id()
        if not task_id:
            return None
        return self._db.get_task(task_id)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_add_task(self) -> None:
        def _on_result(data) -> None:
            if data:
                self._db.add_task(
                    subject_id=self._subject_id,
                    text=data.text,
                    priority=data.priority,
                    category=data.category,
                    due_date=data.due_date,
                )
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Task added")

        self.app.push_screen(AddTaskScreen(), _on_result)

    def action_edit_task(self) -> None:
        task = self._highlighted_task()
        if not task:
            return

        def _on_result(data) -> None:
            if data:
                self._db.update_task(task.id, text=data.text, priority=data.priority, category=data.category, due_date=data.due_date)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Task updated")

        self.app.push_screen(EditTaskScreen(task), _on_result)

    def action_toggle_done(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_status = "todo" if task.status == "done" else "done"
        self._db.update_task_status(task.id, new_status)
        self._refresh_list()
        self.post_message(DataChanged())
        msg = "Task marked done" if new_status == "done" else "Task marked todo"
        self.notify(msg)

    def action_toggle_blocked(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_status = "todo" if task.status == "blocked" else "blocked"
        self._db.update_task_status(task.id, new_status)
        self._refresh_list()
        self.post_message(DataChanged())
        msg = "Task blocked" if new_status == "blocked" else "Task unblocked"
        self.notify(msg)

    def action_cycle_status(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_status = _STATUS_CYCLE.get(task.status, "todo")
        self._db.update_task_status(task.id, new_status)
        self._refresh_list()
        self.post_message(DataChanged())
        self.notify(f"Status: {new_status}")

    def action_cycle_priority(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_priority = _PRIORITY_CYCLE.get(task.priority, "should")
        self._db.update_task_priority(task.id, new_priority)
        self._refresh_list()
        self.post_message(DataChanged())
        self.notify(f"Priority: {new_priority}")

    def action_toggle_today(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        self._db.toggle_today(task.id)
        self._refresh_list()
        self.post_message(DataChanged())
        updated = self._db.get_task(task.id)
        msg = "Added to today" if updated and updated.today else "Removed from today"
        self.notify(msg)

    def action_cycle_day(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_day = _DAY_CYCLE.get(task.day)
        self._db.update_task_day(task.id, new_day)
        self._refresh_list()
        self.post_message(DataChanged())
        day_display = new_day if new_day else "none"
        self.notify(f"Day: {day_display}")

    def action_delete_task(self) -> None:
        task = self._highlighted_task()
        if not task:
            return

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._db.soft_delete_task(task.id)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Task deleted")

        self.app.push_screen(ConfirmScreen("Delete this task?"), _on_confirm)
