"""MilestoneList widget — displays milestones for a subject."""

from __future__ import annotations

from textual.widgets import Label, ListItem, ListView

from tracker.db import Database
from tracker.messages import ContentCancelled, DataChanged, ShowContent
from tracker.models import Milestone
from tracker.screens.confirm import ConfirmScreen

_STATUS_ICON = {
    "active": "◎",
    "completed": "✓",
    "cancelled": "✗",
}

_STATUS_CYCLE = {
    "active": "completed",
    "completed": "cancelled",
    "cancelled": "active",
}


def _milestone_label(ms: Milestone) -> str:
    icon = _STATUS_ICON.get(ms.status, "?")
    due = f" due:{ms.target_date}" if ms.target_date else ""
    lead = f" ({ms.lead_weeks}w lead)" if ms.lead_weeks else ""
    return f"{icon} {ms.name}{due}{lead} [{ms.status}]"


class MilestoneList(ListView):
    """ListView showing milestones for a subject."""

    BINDINGS = [
        ("a", "add_milestone", "Add"),
        ("e", "edit_milestone", "Edit"),
        ("s", "cycle_status", "Cycle status"),
        ("x", "delete_milestone", "Delete"),
        ("escape", "back", "Back"),
    ]

    def __init__(self, db: Database, subject_id: str) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        self.clear()
        milestones = self._db.list_milestones(self._subject_id)
        if not milestones:
            item = ListItem(Label("No milestones. Press a to add one.", classes="empty-state"))
            item._milestone_id = None  # type: ignore[attr-defined]
            self.append(item)
        else:
            for ms in milestones:
                label = Label(_milestone_label(ms), classes=f"status-{ms.status}")
                item = ListItem(label)
                item._milestone_id = ms.id  # type: ignore[attr-defined]
                self.append(item)

    def _highlighted_milestone_id(self) -> str | None:
        if self.highlighted_child is None:
            return None
        return getattr(self.highlighted_child, "_milestone_id", None)

    def _highlighted_milestone(self) -> Milestone | None:
        ms_id = self._highlighted_milestone_id()
        if not ms_id:
            return None
        return self._db.get_milestone(ms_id)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        ms_id = getattr(event.item, "_milestone_id", None)
        if ms_id:
            self.post_message(ShowContent("milestone_view", {"subject_id": self._subject_id, "milestone_id": ms_id}))

    def action_add_milestone(self) -> None:
        self.post_message(ShowContent("milestone_form", {"subject_id": self._subject_id}))

    def action_edit_milestone(self) -> None:
        ms = self._highlighted_milestone()
        if ms:
            self.post_message(ShowContent("milestone_form", {"subject_id": self._subject_id, "milestone_id": ms.id}))

    def action_cycle_status(self) -> None:
        ms = self._highlighted_milestone()
        if not ms:
            return
        new_status = _STATUS_CYCLE.get(ms.status, "active")
        self._db.update_milestone_status(ms.id, new_status)
        self._refresh_list()
        self.post_message(DataChanged())
        self.notify(f"Status: {new_status}")

    def action_delete_milestone(self) -> None:
        ms = self._highlighted_milestone()
        if not ms:
            return

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._db.soft_delete_milestone(ms.id)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Milestone deleted")

        self.app.push_screen(ConfirmScreen("Delete this milestone?"), _on_confirm)

    def action_back(self) -> None:
        self.post_message(ContentCancelled())
