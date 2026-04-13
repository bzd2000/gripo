"""LinkPicker — modal to pick unlinked tasks/follow-ups to link to a milestone."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static

from tracker.db import Database


class LinkPicker(ModalScreen):
    """Modal showing unlinked tasks and follow-ups for a subject. Returns {type, id} or None."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: Database, subject_id: str, milestone_id: str) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id
        self._milestone_id = milestone_id

    def compose(self) -> ComposeResult:
        yield Static("Link item to milestone", classes="overview-col-header")
        yield ListView(id="link-picker-list")

    def on_mount(self) -> None:
        lv = self.query_one("#link-picker-list", ListView)

        # Unlinked tasks (no milestone or different milestone)
        tasks = self._db.list_tasks(self._subject_id)
        for t in tasks:
            if t.status == "done" or t.milestone_id == self._milestone_id:
                continue
            label = f"[task] {t.text} [{t.priority}]"
            item = ListItem(Label(label))
            item._result = {"type": "task", "id": t.id}  # type: ignore[attr-defined]
            lv.append(item)

        # Unlinked follow-ups
        fus = self._db.list_follow_ups(self._subject_id)
        for fu in fus:
            if fu.milestone_id == self._milestone_id:
                continue
            label = f"[follow-up] {fu.text} — {fu.owner}"
            item = ListItem(Label(label))
            item._result = {"type": "follow_up", "id": fu.id}  # type: ignore[attr-defined]
            lv.append(item)

        if not lv.children:
            item = ListItem(Label("No unlinked items available.", classes="empty-state"))
            item._result = None  # type: ignore[attr-defined]
            lv.append(item)

        lv.focus()
        if lv.index is None and len(lv.children) > 0:
            lv.index = 0

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        result = getattr(event.item, "_result", None)
        if result is not None:
            self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)
