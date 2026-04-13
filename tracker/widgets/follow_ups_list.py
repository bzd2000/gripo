"""FollowUpsList widget — displays follow-ups for a subject."""

from __future__ import annotations

from textual.widgets import Label, ListItem, ListView

from tracker.db import Database
from tracker.messages import ContentCancelled, DataChanged, ShowContent
from tracker.models import FollowUp
from tracker.screens.confirm import ConfirmScreen

_STATUS_ICON = {
    "waiting": "⏳",
    "received": "✓",
    "overdue": "‼",
    "cancelled": "✗",
}

_STATUS_CYCLE = {
    "waiting": "received",
    "received": "overdue",
    "overdue": "cancelled",
    "cancelled": "waiting",
}


def _follow_up_label(fu: FollowUp) -> str:
    icon = _STATUS_ICON.get(fu.status, "?")
    due_part = f" due {fu.due_by}" if fu.due_by else ""
    return f"{icon} {fu.text} from {fu.owner}{due_part} [{fu.status}]"


def _css_classes(fu: FollowUp) -> str:
    return f"status-{fu.status}"


class FollowUpsList(ListView):
    """ListView that shows follow-ups for a given subject."""

    BINDINGS = [
        ("a", "add_follow_up", "Add"),
        ("e", "edit_follow_up", "Edit"),
        ("s", "cycle_status", "Cycle status"),
        ("n", "edit_notes", "Edit notes"),
        ("x", "delete_follow_up", "Delete"),
        ("escape", "back", "Back"),
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
        follow_ups = self._db.list_follow_ups(self._subject_id)
        if not follow_ups:
            item = ListItem(
                Label("Nothing pending from anyone.", classes="empty-state")
            )
            item._follow_up_id = None  # type: ignore[attr-defined]
            self.append(item)
        else:
            for fu in follow_ups:
                label = Label(_follow_up_label(fu), classes=_css_classes(fu))
                item = ListItem(label)
                item._follow_up_id = fu.id  # type: ignore[attr-defined]
                self.append(item)

    def _highlighted_follow_up_id(self) -> str | None:
        if self.highlighted_child is None:
            return None
        return getattr(self.highlighted_child, "_follow_up_id", None)

    def _highlighted_follow_up(self) -> FollowUp | None:
        fu_id = self._highlighted_follow_up_id()
        if not fu_id:
            return None
        return self._db.get_follow_up(fu_id)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        fu_id = getattr(event.item, "_follow_up_id", None)
        if fu_id:
            self.post_message(ShowContent(content_type="follow_up_form", data={"subject_id": self._subject_id, "follow_up_id": fu_id}))

    def action_add_follow_up(self) -> None:
        self.post_message(ShowContent(content_type="follow_up_form", data={"subject_id": self._subject_id}))

    def action_edit_follow_up(self) -> None:
        fu = self._highlighted_follow_up()
        if not fu:
            return
        self.post_message(ShowContent(content_type="follow_up_form", data={"subject_id": self._subject_id, "follow_up_id": fu.id}))

    def action_cycle_status(self) -> None:
        fu = self._highlighted_follow_up()
        if not fu:
            return
        new_status = _STATUS_CYCLE.get(fu.status, "waiting")
        self._db.update_follow_up_status(fu.id, new_status)
        self._refresh_list()
        self.post_message(DataChanged())
        self.notify(f"Status: {new_status}")

    def action_edit_notes(self) -> None:
        fu = self._highlighted_follow_up()
        if not fu:
            return
        self.post_message(ShowContent(content_type="follow_up_form", data={"subject_id": self._subject_id, "follow_up_id": fu.id}))

    def action_delete_follow_up(self) -> None:
        fu = self._highlighted_follow_up()
        if not fu:
            return

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._db.soft_delete_follow_up(fu.id)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Follow-up deleted")

        self.app.push_screen(ConfirmScreen("Delete this follow-up?"), _on_confirm)

    def action_back(self) -> None:
        self.post_message(ContentCancelled())
