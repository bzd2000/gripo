"""OverviewView widget — grid dashboard: Today + Week + Milestones Gantt.

Works as both global dashboard (subject_id=None) and subject-filtered view.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Optional

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.widgets import Label, ListItem, ListView, Static

from tracker.db import Database
from tracker.messages import ContentCancelled, DataChanged, ShowContent
from tracker.constants import (
    DAYS,
    DAY_LABELS,
    FUTASK_STATUS_ICON,
    PRIORITY_CYCLE,
    STATUS_CYCLE,
    TASKTASK_STATUS_ICON,
)
from tracker.models import FollowUp, Milestone, Task


def _task_label(task: Task, show_subject: bool = False) -> str:
    icon = TASK_STATUS_ICON.get(task.status, "?")
    subject = f" [{task.subject_name}]" if show_subject and task.subject_name else ""
    return f"{icon} {task.text} [{task.priority}]{subject}"


def _short_task_label(task: Task) -> str:
    icon = TASK_STATUS_ICON.get(task.status, "?")
    return f"{icon} {task.text}"


def _follow_up_label(fu: FollowUp, show_subject: bool = False) -> str:
    icon = _FUTASK_STATUS_ICON.get(fu.status, "?")
    subject = f" [{fu.subject_name}]" if show_subject and fu.subject_name else ""
    return f"{icon} {fu.text} — {fu.owner}{subject}"


def _make_item(item_id: str, subject_id: str, item_type: str, label: Label) -> ListItem:
    li = ListItem(label)
    li._task_id = item_id  # type: ignore[attr-defined]
    li._subject_id = subject_id  # type: ignore[attr-defined]
    li._item_type = item_type  # type: ignore[attr-defined]
    return li


def _make_empty() -> ListItem:
    li = ListItem(Label("—", classes="empty-state"))
    li._task_id = None  # type: ignore[attr-defined]
    li._subject_id = None  # type: ignore[attr-defined]
    li._item_type = None  # type: ignore[attr-defined]
    return li


class _ItemList(ListView):
    """A ListView column that handles selection by posting ShowContent."""

    def on_focus(self, event) -> None:
        if self.index is None and len(self.children) > 0:
            self.index = 0

    def on_blur(self, event) -> None:
        self.index = None

    def on_list_view_selected(self, event: "ListView.Selected") -> None:
        item = event.item
        subject_id = getattr(item, "_subject_id", None)
        item_id = getattr(item, "_task_id", None)
        if not subject_id or not item_id:
            return
        item_type = getattr(item, "_item_type", None)
        if item_type == "follow_up":
            self.post_message(ShowContent(
                content_type="follow_up_form",
                data={"subject_id": subject_id, "follow_up_id": item_id},
            ))
        elif item_type == "task":
            self.post_message(ShowContent(
                content_type="task_form",
                data={"subject_id": subject_id, "task_id": item_id},
            ))


_GANTT_WEEKS = 52
_LABEL_WIDTH = 25


def _gantt_header() -> str:
    """Render the month header line for the Gantt chart."""
    today = date.today()
    month_positions = []
    for w in range(_GANTT_WEEKS):
        week_date = today + timedelta(weeks=w)
        if week_date.day <= 7 and (not month_positions or month_positions[-1][0] != week_date.month):
            month_positions.append((week_date.month, w, week_date.strftime("%b")))

    header_chars = [" "] * (_LABEL_WIDTH + _GANTT_WEEKS)
    for _, pos, label in month_positions:
        col = _LABEL_WIDTH + pos
        for i, ch in enumerate(label[:3]):
            if col + i < len(header_chars):
                header_chars[col + i] = ch
    return "".join(header_chars)


def _gantt_bar(ms: Milestone) -> str:
    """Render a single milestone's Gantt bar line with Rich markup."""
    today = date.today()
    target = date.fromisoformat(ms.target_date)
    lead = ms.lead_weeks or 0
    start = target - timedelta(weeks=lead) if lead else target

    target_week = (target - today).days // 7
    start_week = (start - today).days // 7

    subj = ms.subject_name or ""
    if subj:
        label_text = f"{subj}: {ms.name}"
    else:
        label_text = ms.name
    if len(label_text) > _LABEL_WIDTH - 2:
        label_text = label_text[:_LABEL_WIDTH - 3] + "…"
    label_text = label_text.ljust(_LABEL_WIDTH - 1) + " "

    if start_week < 0:
        color = "#ff3333"
    elif start_week <= 2:
        color = "#ffaa00"
    else:
        color = "#00ff41"

    bar = [" "] * _GANTT_WEEKS
    for w in range(max(0, start_week), min(_GANTT_WEEKS, target_week)):
        bar[w] = "━"
    if 0 <= target_week < _GANTT_WEEKS:
        bar[target_week] = "┃"

    bar_str = "".join(bar)
    return f"[dim]{label_text}[/dim][{color}]{bar_str}[/{color}]"


class _GanttList(ListView):
    """ListView for Gantt milestone rows — focusable with Enter to open."""

    def on_focus(self, event) -> None:
        if self.index is None and len(self.children) > 0:
            self.index = 0

    def on_blur(self, event) -> None:
        self.index = None

    def on_list_view_selected(self, event: "ListView.Selected") -> None:
        item = event.item
        subject_id = getattr(item, "_subject_id", None)
        milestone_id = getattr(item, "_milestone_id", None)
        if subject_id and milestone_id:
            self.post_message(ShowContent(
                "milestone_view",
                {"subject_id": subject_id, "milestone_id": milestone_id},
            ))


class OverviewView(Container, can_focus=True):
    """Grid dashboard: Today + Week + Milestones Gantt.

    If subject_id is provided, filters to that subject only.
    Otherwise shows cross-subject global view.
    """

    BINDINGS = [
        ("d", "toggle_done", "Toggle done"),
        ("s", "cycle_status", "Cycle status"),
        ("p", "cycle_priority", "Cycle priority"),
        ("escape", "back", "Back"),
    ]

    def __init__(self, db: Database, subject_id: Optional[str] = None) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id

    @property
    def _is_global(self) -> bool:
        return self._subject_id is None

    def compose(self) -> ComposeResult:
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())

        # Row 1: Today
        with Container(id="today-row"):
            with Vertical(id="today-tasks-col"):
                yield Label("TODAY", classes="overview-col-header")
                yield _ItemList(id="ov-today-tasks")
            with Vertical(id="today-fus-col"):
                yield Label("FOLLOW-UPS", classes="overview-col-header")
                yield _ItemList(id="ov-today-fus")

        # Row 2: Week (Mon-Fri)
        with Container(id="week-row"):
            for i, day in enumerate(DAYS):
                day_date = this_monday + timedelta(days=i)
                day_str = day_date.strftime("%d/%m")
                with Vertical(classes="week-day-col"):
                    yield Label(f"{DAY_LABELS[day]} {day_str}", classes="overview-col-header")
                    yield _ItemList(id=f"ov-week-{day}")

        # Row 3: Milestones Gantt
        with Vertical(id="milestones-row"):
            yield Label("MILESTONES", classes="overview-col-header")
            yield Static("", id="ov-gantt-header")
            yield _GanttList(id="ov-gantt-list")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        this_sunday = this_monday + timedelta(days=6)

        if self._is_global:
            today_tasks = self._db.list_today_tasks()
            today_fus = self._db.list_today_follow_ups()
            week_tasks = self._db.list_week_tasks()
            week_fus = self._db.list_week_follow_ups()
            all_milestones = self._db.list_all_active_milestones()
            show_subject = True
        else:
            sid = self._subject_id
            all_tasks = self._db.list_tasks(sid)
            all_follow_ups = self._db.list_follow_ups(sid)

            today_tasks = [
                t for t in all_tasks
                if t.status != "done"
                and (t.today or (t.due_date and t.due_date <= today.isoformat()))
            ]
            today_fus = [
                f for f in all_follow_ups
                if f.status in ("waiting", "overdue")
                and f.due_by and f.due_by <= today.isoformat()
            ]
            week_tasks = [
                t for t in all_tasks
                if t.status != "done"
                and (t.day is not None
                     or (t.due_date and this_monday.isoformat() <= t.due_date <= this_sunday.isoformat()))
            ]
            week_fus = [
                f for f in all_follow_ups
                if f.status in ("waiting", "overdue")
                and f.due_by and this_monday.isoformat() <= f.due_by <= this_sunday.isoformat()
            ]
            milestones = self._db.list_milestones(sid)
            all_milestones = [m for m in milestones if m.status == "active" and m.target_date]
            show_subject = False

        # ── Row 1: Today ──
        tl = self.query_one("#ov-today-tasks", _ItemList)
        tl.clear()
        if today_tasks:
            for task in today_tasks:
                label = Label(
                    _task_label(task, show_subject),
                    classes=f"priority-{task.priority} status-{task.status}",
                )
                tl.append(_make_item(task.id, task.subject_id, "task", label))
        else:
            tl.append(_make_empty())

        fl = self.query_one("#ov-today-fus", _ItemList)
        fl.clear()
        if today_fus:
            for fu in today_fus:
                label = Label(_follow_up_label(fu, show_subject))
                fl.append(_make_item(fu.id, fu.subject_id, "follow_up", label))
        else:
            fl.append(_make_empty())

        # ── Row 2: Week ──
        today_task_ids = {t.id for t in today_tasks}
        by_day: dict[str, List[Task]] = {d: [] for d in DAYS}
        for task in week_tasks:
            if task.id in today_task_ids:
                continue
            day = task.day if task.day in DAYS else None
            if day:
                by_day[day].append(task)
            elif task.due_date:
                try:
                    d = date.fromisoformat(task.due_date)
                    weekday_idx = d.weekday()
                    if weekday_idx < 5:
                        by_day[DAYS[weekday_idx]].append(task)
                except ValueError:
                    pass

        fus_by_day: dict[str, List[FollowUp]] = {d: [] for d in DAYS}
        for fu in week_fus:
            if fu.due_by:
                try:
                    d = date.fromisoformat(fu.due_by)
                    weekday_idx = d.weekday()
                    if weekday_idx < 5:
                        fus_by_day[DAYS[weekday_idx]].append(fu)
                except ValueError:
                    pass

        for day in DAYS:
            dl = self.query_one(f"#ov-week-{day}", _ItemList)
            dl.clear()
            day_tasks = by_day[day]
            day_fus = fus_by_day[day]
            if not day_tasks and not day_fus:
                dl.append(_make_empty())
            else:
                for task in day_tasks:
                    label = Label(
                        _short_task_label(task),
                        classes=f"priority-{task.priority} status-{task.status}",
                    )
                    dl.append(_make_item(task.id, task.subject_id, "task", label))
                for fu in day_fus:
                    icon = _FUTASK_STATUS_ICON.get(fu.status, "?")
                    label = Label(f"{icon} {fu.text}")
                    dl.append(_make_item(fu.id, fu.subject_id, "follow_up", label))

        # ── Row 3: Milestones Gantt ──
        gantt_header = self.query_one("#ov-gantt-header", Static)
        gantt_header.update(f"[bold #00aa33]{_gantt_header()}[/bold #00aa33]")

        gantt_list = self.query_one("#ov-gantt-list", _GanttList)
        gantt_list.clear()
        if not all_milestones:
            li = ListItem(Label("[dim]No active milestones with target dates.[/dim]"))
            li._subject_id = None  # type: ignore[attr-defined]
            li._milestone_id = None  # type: ignore[attr-defined]
            gantt_list.append(li)
        else:
            for ms in all_milestones:
                if not show_subject:
                    ms.subject_name = ""
                li = ListItem(Static(_gantt_bar(ms)))
                li._subject_id = ms.subject_id  # type: ignore[attr-defined]
                li._milestone_id = ms.id  # type: ignore[attr-defined]
                gantt_list.append(li)

    def _get_focused_list(self) -> _ItemList | None:
        for il in self.query(_ItemList):
            if il.has_focus or il.has_focus_within:
                return il
        return None

    def _highlighted_task(self) -> Task | None:
        il = self._get_focused_list()
        if not il or il.highlighted_child is None:
            return None
        item_type = getattr(il.highlighted_child, "_item_type", None)
        if item_type != "task":
            return None
        task_id = getattr(il.highlighted_child, "_task_id", None)
        if not task_id:
            return None
        return self._db.get_task(task_id)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_back(self) -> None:
        self.post_message(ContentCancelled())

    def action_toggle_done(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_status = "todo" if task.status == "done" else "done"
        self._db.update_task_status(task.id, new_status)
        self._refresh()
        self.post_message(DataChanged())
        self.notify("Task marked done" if new_status == "done" else "Task marked todo")

    def action_cycle_status(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        idx = STATUS_CYCLE.index(task.status) if task.status in STATUS_CYCLE else 0
        new_status = STATUS_CYCLE[(idx + 1) % len(STATUS_CYCLE)]
        self._db.update_task_status(task.id, new_status)
        self._refresh()
        self.post_message(DataChanged())
        self.notify(f"Status: {new_status}")

    def action_cycle_priority(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        idx = PRIORITY_CYCLE.index(task.priority) if task.priority in PRIORITY_CYCLE else 0
        new_priority = PRIORITY_CYCLE[(idx + 1) % len(PRIORITY_CYCLE)]
        self._db.update_task_priority(task.id, new_priority)
        self._refresh()
        self.post_message(DataChanged())
        self.notify(f"Priority: {new_priority}")

    # ------------------------------------------------------------------
    # External refresh
    # ------------------------------------------------------------------

    def refresh_view(self) -> None:
        self._refresh()
