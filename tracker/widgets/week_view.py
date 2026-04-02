"""WeekView widget — cross-subject This Week panel."""

from __future__ import annotations

from collections import defaultdict
from typing import List

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
_DAY_CYCLE = ["mon", "tue", "wed", "thu", "fri", "anytime"]

_DAY_LABELS = {
    "mon": "MON",
    "tue": "TUE",
    "wed": "WED",
    "thu": "THU",
    "fri": "FRI",
    "anytime": "ANYTIME",
}


def _task_label(task: Task) -> str:
    icon = _STATUS_ICON.get(task.status, "?")
    subject = f" [{task.subject_name}]" if task.subject_name else ""
    return f"{icon} {task.text} [{task.priority}] ({task.status}){subject}"


class WeekView(Vertical):
    """Shows week-assigned tasks across all subjects grouped by day."""

    BINDINGS = [
        ("d", "toggle_done", "Toggle done"),
        ("s", "cycle_status", "Cycle status"),
        ("p", "cycle_priority", "Cycle priority"),
        ("w", "cycle_day", "Cycle day"),
        ("enter", "open_subject", "Open subject"),
    ]

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Static("THIS WEEK", id="week-header")
        yield ListView(id="week-list")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        tasks = self._db.list_week_tasks()

        list_view = self.query_one("#week-list", ListView)
        list_view.clear()

        if not tasks:
            item = ListItem(
                Label(
                    "No tasks scheduled for this week. Go to a subject task and press w to assign a day.",
                    classes="empty-state",
                )
            )
            item._task_id = None  # type: ignore[attr-defined]
            item._subject_id = None  # type: ignore[attr-defined]
            item._is_header = True  # type: ignore[attr-defined]
            list_view.append(item)
            return

        # Group tasks by day preserving order
        ordered_days: List[str] = []
        by_day: dict[str, List[Task]] = defaultdict(list)
        for task in tasks:
            day = task.day or "anytime"
            if day not in by_day:
                ordered_days.append(day)
            by_day[day].append(task)

        for day in ordered_days:
            # Day header (non-selectable)
            day_label = _DAY_LABELS.get(day, day.upper())
            header_item = ListItem(Label(f"── {day_label} ──", classes="day-header"))
            header_item._task_id = None  # type: ignore[attr-defined]
            header_item._subject_id = None  # type: ignore[attr-defined]
            header_item._is_header = True  # type: ignore[attr-defined]
            header_item.disabled = True
            list_view.append(header_item)

            for task in by_day[day]:
                label = Label(
                    _task_label(task),
                    classes=f"priority-{task.priority} status-{task.status}",
                )
                item = ListItem(label)
                item._task_id = task.id  # type: ignore[attr-defined]
                item._subject_id = task.subject_id  # type: ignore[attr-defined]
                item._is_header = False  # type: ignore[attr-defined]
                list_view.append(item)

    def _highlighted_task(self) -> Task | None:
        list_view = self.query_one("#week-list", ListView)
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

    def action_cycle_day(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        current_day = task.day or "anytime"
        idx = _DAY_CYCLE.index(current_day) if current_day in _DAY_CYCLE else 0
        new_day = _DAY_CYCLE[(idx + 1) % len(_DAY_CYCLE)]
        self._db.update_task_day(task.id, new_day)
        self._refresh()
        self.post_message(DataChanged())
        self.notify(f"Day: {new_day}")

    def action_open_subject(self) -> None:
        from tracker.screens.subject_detail import SubjectDetailScreen

        list_view = self.query_one("#week-list", ListView)
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
