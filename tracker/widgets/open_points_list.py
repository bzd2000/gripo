"""OpenPointsList widget — displays open points for a subject."""

from __future__ import annotations

from textual.widgets import Label, ListItem, ListView

from tracker.db import Database
from tracker.messages import ContentCancelled, DataChanged, ShowContent
from tracker.models import OpenPoint
from tracker.screens.confirm import ConfirmScreen

_STATUS_ICON = {
    "open": "?",
    "resolved": "✓",
    "parked": "—",
}

_STATUS_CYCLE = {
    "open": "parked",
    "parked": "resolved",
    "resolved": "open",
}


def _point_label(point: OpenPoint) -> str:
    icon = _STATUS_ICON.get(point.status, "?")
    context_part = f" ({point.context})" if point.context else ""
    return f"{icon} {point.text}{context_part} [{point.status}]"


def _css_classes(point: OpenPoint) -> str:
    return f"status-{point.status}"


class OpenPointsList(ListView):
    """ListView that shows open points for a given subject."""

    BINDINGS = [
        ("a", "add_point", "Add"),
        ("o", "add_point", "Add"),
        ("e", "edit_point", "Edit"),
        ("c", "edit_context", "Edit context"),
        ("r", "resolve_point", "Resolve"),
        ("s", "cycle_status", "Cycle status"),
        ("x", "delete_point", "Delete"),
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
        points = self._db.list_open_points(self._subject_id)
        if not points:
            item = ListItem(
                Label(
                    "No open questions. Press o to add something that needs discussing or deciding.",
                    classes="empty-state",
                )
            )
            item._point_id = None  # type: ignore[attr-defined]
            self.append(item)
        else:
            for point in points:
                label = Label(_point_label(point), classes=_css_classes(point))
                item = ListItem(label)
                item._point_id = point.id  # type: ignore[attr-defined]
                self.append(item)

    def _highlighted_point_id(self) -> str | None:
        if self.highlighted_child is None:
            return None
        return getattr(self.highlighted_child, "_point_id", None)

    def _highlighted_point(self) -> OpenPoint | None:
        point_id = self._highlighted_point_id()
        if not point_id:
            return None
        return self._db.get_open_point(point_id)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        point_id = getattr(event.item, "_point_id", None)
        if point_id:
            self.post_message(ShowContent(content_type="open_point_form", data={"subject_id": self._subject_id, "point_id": point_id}))

    def action_add_point(self) -> None:
        self.post_message(ShowContent(content_type="open_point_form", data={"subject_id": self._subject_id}))

    def action_edit_point(self) -> None:
        point = self._highlighted_point()
        if not point:
            return
        self.post_message(ShowContent(content_type="open_point_form", data={"subject_id": self._subject_id, "point_id": point.id}))

    def action_edit_context(self) -> None:
        point = self._highlighted_point()
        if not point:
            return
        self.post_message(ShowContent(content_type="open_point_form", data={"subject_id": self._subject_id, "point_id": point.id}))

    def action_resolve_point(self) -> None:
        point = self._highlighted_point()
        if not point:
            return
        self.post_message(ShowContent(content_type="open_point_form", data={"subject_id": self._subject_id, "point_id": point.id}))

    def action_cycle_status(self) -> None:
        point = self._highlighted_point()
        if not point:
            return
        new_status = _STATUS_CYCLE.get(point.status, "open")
        self._db.update_open_point_status(point.id, new_status)
        self._refresh_list()
        self.post_message(DataChanged())
        self.notify(f"Status: {new_status}")

    def action_delete_point(self) -> None:
        point = self._highlighted_point()
        if not point:
            return

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._db.soft_delete_open_point(point.id)
                self._refresh_list()
                self.post_message(DataChanged())
                self.notify("Open point deleted")

        self.app.push_screen(ConfirmScreen("Delete this open point?"), _on_confirm)

    def action_back(self) -> None:
        self.post_message(ContentCancelled())
