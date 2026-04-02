"""TodayView widget — cross-subject Today's Focus panel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, ListItem, ListView, Static

from tracker.db import Database
from tracker.messages import DataChanged
from tracker.models import Task

_STATUS_ICON = {
    "todo": "○",
    "in-progress": "●",
    "done": "✓",
    "blocked": "✗",
}

_STATUS_CYCLE = ["todo", "in-progress", "done", "blocked"]
_PRIORITY_CYCLE = ["must", "should", "if-time"]

_MAX_DISPLAY = 5


def _task_label(task: Task) -> str:
    icon = _STATUS_ICON.get(task.status, "?")
    subject = f" [{task.subject_name}]" if task.subject_name else ""
    return f"{icon} {task.text} [{task.priority}] ({task.status}){subject}"


class TodayView(Vertical):
    """Shows today-flagged tasks across all subjects (max 5)."""

    BINDINGS = [
        ("d", "toggle_done", "Toggle done"),
        ("s", "cycle_status", "Cycle status"),
        ("p", "cycle_priority", "Cycle priority"),
        ("enter", "open_subject", "Open subject"),
    ]

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("TODAY'S FOCUS", id="today-header")
        yield ListView(id="today-list")
        yield Static("", id="today-summary")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        tasks = self._db.list_today_tasks()
        display_tasks = tasks[:_MAX_DISPLAY]
        total, done, blocked = self._db.today_counts()

        list_view = self.query_one("#today-list", ListView)
        list_view.clear()

        if not display_tasks:
            item = ListItem(
                Label(
                    "Nothing planned for today. Go to a subject and press t to pull tasks in.",
                    classes="empty-state",
                )
            )
            item._task_id = None  # type: ignore[attr-defined]
            item._subject_id = None  # type: ignore[attr-defined]
            list_view.append(item)
        else:
            for task in display_tasks:
                label = Label(_task_label(task), classes=f"priority-{task.priority} status-{task.status}")
                item = ListItem(label)
                item._task_id = task.id  # type: ignore[attr-defined]
                item._subject_id = task.subject_id  # type: ignore[attr-defined]
                list_view.append(item)

        summary = self.query_one("#today-summary", Static)
        summary.update(f"Done: {done}/{total}    Blocked: {blocked}")

    def _highlighted_task(self) -> Task | None:
        list_view = self.query_one("#today-list", ListView)
        if list_view.highlighted_child is None:
            return None
        task_id = getattr(list_view.highlighted_child, "_task_id", None)
        if not task_id:
            return None
        return self._db.get_task(task_id)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_toggle_done(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_status = "todo" if task.status == "done" else "done"
        self._db.update_task_status(task.id, new_status)
        self._refresh()
        self.post_message(DataChanged())
        msg = "Task marked done" if new_status == "done" else "Task marked todo"
        self.notify(msg)

    def action_cycle_status(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        idx = _STATUS_CYCLE.index(task.status) if task.status in _STATUS_CYCLE else 0
        new_status = _STATUS_CYCLE[(idx + 1) % len(_STATUS_CYCLE)]
        self._db.update_task_status(task.id, new_status)
        self._refresh()
        self.post_message(DataChanged())
        self.notify(f"Status: {new_status}")

    def action_cycle_priority(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        idx = _PRIORITY_CYCLE.index(task.priority) if task.priority in _PRIORITY_CYCLE else 0
        new_priority = _PRIORITY_CYCLE[(idx + 1) % len(_PRIORITY_CYCLE)]
        self._db.update_task_priority(task.id, new_priority)
        self._refresh()
        self.post_message(DataChanged())
        self.notify(f"Priority: {new_priority}")

    def action_open_subject(self) -> None:
        from tracker.screens.subject_detail import SubjectDetailScreen

        list_view = self.query_one("#today-list", ListView)
        if list_view.highlighted_child is None:
            return
        subject_id = getattr(list_view.highlighted_child, "_subject_id", None)
        if not subject_id:
            return
        self.app.push_screen(SubjectDetailScreen(self._db, subject_id))

    # ------------------------------------------------------------------
    # External refresh (called by app after DataChanged)
    # ------------------------------------------------------------------

    def refresh_view(self) -> None:
        """Public method for external callers to trigger a refresh."""
        self._refresh()
