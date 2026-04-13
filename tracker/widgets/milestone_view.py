"""MilestoneView widget — dashboard showing linked tasks + follow-ups."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Label, ListItem, ListView, Static

from tracker.db import Database
from tracker.messages import ContentCancelled, DataChanged, ShowContent

_TASK_STATUS_ICON = {
    "todo": "○",
    "in-progress": "●",
    "done": "✓",
    "blocked": "✗",
}

_FU_STATUS_ICON = {
    "waiting": "⏳",
    "received": "✓",
    "overdue": "‼",
    "cancelled": "✗",
}

_STATUS_CYCLE = ["todo", "in-progress", "done", "blocked"]
_PRIORITY_CYCLE = ["must", "should", "if-time"]


class _ItemList(ListView):
    def on_focus(self, event) -> None:
        if self.index is None and len(self.children) > 0:
            self.index = 0

    def on_blur(self, event) -> None:
        self.index = None

    def on_list_view_selected(self, event: "ListView.Selected") -> None:
        item = event.item
        subject_id = getattr(item, "_subject_id", None)
        item_id = getattr(item, "_item_id", None)
        item_type = getattr(item, "_item_type", None)
        if not subject_id or not item_id:
            return
        if item_type == "task":
            self.post_message(ShowContent("task_form", {"subject_id": subject_id, "task_id": item_id}))
        elif item_type == "follow_up":
            self.post_message(ShowContent("follow_up_form", {"subject_id": subject_id, "follow_up_id": item_id}))


def _make_item(label: Label, item_id: str, subject_id: str, item_type: str) -> ListItem:
    li = ListItem(label)
    li._item_id = item_id  # type: ignore[attr-defined]
    li._subject_id = subject_id  # type: ignore[attr-defined]
    li._item_type = item_type  # type: ignore[attr-defined]
    return li


def _make_empty() -> ListItem:
    li = ListItem(Label("—", classes="empty-state"))
    li._item_id = None  # type: ignore[attr-defined]
    li._subject_id = None  # type: ignore[attr-defined]
    li._item_type = None  # type: ignore[attr-defined]
    return li


class MilestoneView(Container, can_focus=True):
    """2-column dashboard: linked TASKS | FOLLOW-UPS for a milestone."""

    BINDINGS = [
        ("escape", "back", "Back"),
        ("e", "edit", "Edit milestone"),
        ("a", "add_new", "Add new"),
        ("l", "link_existing", "Link existing"),
        ("u", "unlink", "Unlink"),
        ("d", "toggle_done", "Toggle done"),
        ("s", "cycle_status", "Cycle status"),
        ("p", "cycle_priority", "Cycle priority"),
    ]

    def __init__(self, db: Database, subject_id: str, milestone_id: str) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id
        self._milestone_id = milestone_id

    def compose(self) -> ComposeResult:
        ms = self._db.get_milestone(self._milestone_id)
        title = ms.name if ms else "Milestone"
        due = f" — due {ms.target_date}" if ms and ms.target_date else ""
        lead = f" — start {ms.lead_weeks}w before" if ms and ms.lead_weeks else ""

        yield Static(f"{title}{due}{lead}", id="mv-header", classes="overview-col-header")
        with Container(id="mv-columns"):
            with Vertical(classes="milestone-col"):
                yield Label("TASKS", classes="overview-col-header")
                yield _ItemList(id="mv-tasks-list")
            with Vertical(classes="milestone-col"):
                yield Label("FOLLOW-UPS", classes="overview-col-header")
                yield _ItemList(id="mv-fus-list")

    def on_mount(self) -> None:
        self._refresh()

    def _refresh(self) -> None:
        sid = self._subject_id
        mid = self._milestone_id

        tl = self.query_one("#mv-tasks-list", _ItemList)
        tl.clear()
        tasks = self._db.list_milestone_tasks(mid)
        if tasks:
            for t in tasks:
                icon = _TASK_STATUS_ICON.get(t.status, "?")
                label = Label(
                    f"{icon} {t.text} [{t.priority}]",
                    classes=f"priority-{t.priority} status-{t.status}",
                )
                tl.append(_make_item(label, t.id, sid, "task"))
        else:
            tl.append(_make_empty())

        fl = self.query_one("#mv-fus-list", _ItemList)
        fl.clear()
        fus = self._db.list_milestone_follow_ups(mid)
        if fus:
            for fu in fus:
                icon = _FU_STATUS_ICON.get(fu.status, "?")
                due = f" due:{fu.due_by}" if fu.due_by else ""
                label = Label(f"{icon} {fu.text} — {fu.owner}{due}")
                fl.append(_make_item(label, fu.id, sid, "follow_up"))
        else:
            fl.append(_make_empty())

    def _get_focused_list(self) -> _ItemList | None:
        for il in self.query(_ItemList):
            if il.has_focus or il.has_focus_within:
                return il
        return None

    def _highlighted_task(self):
        il = self._get_focused_list()
        if not il or il.highlighted_child is None:
            return None
        if getattr(il.highlighted_child, "_item_type", None) != "task":
            return None
        task_id = getattr(il.highlighted_child, "_item_id", None)
        return self._db.get_task(task_id) if task_id else None

    def action_back(self) -> None:
        self.post_message(ContentCancelled())

    def action_edit(self) -> None:
        self.post_message(ShowContent("milestone_form", {
            "subject_id": self._subject_id, "milestone_id": self._milestone_id,
        }))

    def action_toggle_done(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        new_status = "todo" if task.status == "done" else "done"
        self._db.update_task_status(task.id, new_status)
        self._refresh()
        self.post_message(DataChanged())

    def action_cycle_status(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        idx = _STATUS_CYCLE.index(task.status) if task.status in _STATUS_CYCLE else 0
        new_status = _STATUS_CYCLE[(idx + 1) % len(_STATUS_CYCLE)]
        self._db.update_task_status(task.id, new_status)
        self._refresh()
        self.post_message(DataChanged())

    def action_cycle_priority(self) -> None:
        task = self._highlighted_task()
        if not task:
            return
        idx = _PRIORITY_CYCLE.index(task.priority) if task.priority in _PRIORITY_CYCLE else 0
        new_priority = _PRIORITY_CYCLE[(idx + 1) % len(_PRIORITY_CYCLE)]
        self._db.update_task_priority(task.id, new_priority)
        self._refresh()
        self.post_message(DataChanged())

    def _focused_column_type(self) -> str | None:
        """Return 'task' or 'follow_up' based on which column has focus."""
        try:
            tl = self.query_one("#mv-tasks-list", _ItemList)
            if tl.has_focus or tl.has_focus_within:
                return "task"
        except Exception:
            pass
        try:
            fl = self.query_one("#mv-fus-list", _ItemList)
            if fl.has_focus or fl.has_focus_within:
                return "follow_up"
        except Exception:
            pass
        return "task"  # default

    def _highlighted_item(self) -> tuple[str | None, str | None]:
        """Return (item_type, item_id) for the highlighted item in the focused list."""
        il = self._get_focused_list()
        if not il or il.highlighted_child is None:
            return None, None
        item_type = getattr(il.highlighted_child, "_item_type", None)
        item_id = getattr(il.highlighted_child, "_item_id", None)
        return item_type, item_id

    def action_add_new(self) -> None:
        col = self._focused_column_type()
        if col == "follow_up":
            self.post_message(ShowContent("follow_up_form", {
                "subject_id": self._subject_id,
                "milestone_id": self._milestone_id,
            }))
        else:
            self.post_message(ShowContent("task_form", {
                "subject_id": self._subject_id,
                "milestone_id": self._milestone_id,
            }))

    def action_link_existing(self) -> None:
        from tracker.screens.link_picker import LinkPicker

        def _on_pick(result: dict | None) -> None:
            if result is None:
                return
            if result["type"] == "task":
                self._db.link_task_to_milestone(result["id"], self._milestone_id)
            elif result["type"] == "follow_up":
                self._db.link_follow_up_to_milestone(result["id"], self._milestone_id)
            self._refresh()
            self.post_message(DataChanged())

        self.app.push_screen(
            LinkPicker(self._db, self._subject_id, self._milestone_id),
            _on_pick,
        )

    def action_unlink(self) -> None:
        item_type, item_id = self._highlighted_item()
        if not item_type or not item_id:
            return
        if item_type == "task":
            self._db.link_task_to_milestone(item_id, None)
        elif item_type == "follow_up":
            self._db.link_follow_up_to_milestone(item_id, None)
        self._refresh()
        self.post_message(DataChanged())
        self.notify("Item unlinked")

    def refresh_view(self) -> None:
        self._refresh()
