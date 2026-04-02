"""SubjectsList widget — displays all subjects with summary info."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Label, ListItem, ListView

from tracker.db import Database
from tracker.messages import DataChanged
from tracker.screens.add_subject import AddSubjectScreen
from tracker.screens.confirm import ConfirmScreen


class SubjectSelected(Message):
    """Posted when the user activates a subject (Enter key)."""

    def __init__(self, subject_id: str) -> None:
        super().__init__()
        self.subject_id = subject_id


class SubjectsList(ListView):
    """ListView that shows subjects loaded from the database."""

    BINDINGS = [
        ("a", "add_subject", "Add subject"),
        ("p", "toggle_pin", "Pin/unpin"),
        ("shift+a", "toggle_archived", "Show/hide archived"),
        ("x", "archive_subject", "Archive"),
    ]

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db
        self._show_archived = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _subject_label(self, subject) -> str:
        pin = "📌 " if subject.pinned else "   "
        name = subject.name
        parts = []
        if subject.open_tasks:
            parts.append(f"{subject.open_tasks}t")
        if subject.open_points_count:
            parts.append(f"{subject.open_points_count}op")
        if subject.follow_ups_count:
            parts.append(f"{subject.follow_ups_count}f")
        if subject.latest_note:
            # Show just the date part (first 10 chars of ISO string)
            parts.append(f"note:{subject.latest_note[:10]}")
        summary = "  [" + " · ".join(parts) + "]" if parts else ""
        archived_marker = " [archived]" if subject.archived else ""
        return f"{pin}{name}{archived_marker}{summary}"

    def _highlighted_subject_id(self) -> str | None:
        """Return the subject_id of the currently highlighted ListItem."""
        if self.highlighted_child is None:
            return None
        return getattr(self.highlighted_child, "_subject_id", None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Rebuild the list from the database."""
        self.clear()
        subjects = self._db.list_subjects(include_archived=self._show_archived)
        if not subjects:
            item = ListItem(Label("No subjects yet. Press a to create your first one.", classes="empty-state"))
            item._subject_id = None  # type: ignore[attr-defined]
            self.append(item)
        else:
            for subject in subjects:
                item = ListItem(Label(self._subject_label(subject)))
                item._subject_id = subject.id  # type: ignore[attr-defined]
                self.append(item)

    # ------------------------------------------------------------------
    # Bindings / actions
    # ------------------------------------------------------------------

    def action_add_subject(self) -> None:
        def _on_result(name: str | None) -> None:
            if name:
                self._db.add_subject(name)
                self._refresh_list()
                self.post_message(DataChanged())

        self.app.push_screen(AddSubjectScreen(), _on_result)

    def action_toggle_pin(self) -> None:
        subject_id = self._highlighted_subject_id()
        if not subject_id:
            return
        self._db.toggle_pin(subject_id)
        self._refresh_list()
        self.post_message(DataChanged())

    def action_toggle_archived(self) -> None:
        self._show_archived = not self._show_archived
        self._refresh_list()

    def action_archive_subject(self) -> None:
        subject_id = self._highlighted_subject_id()
        if not subject_id:
            return

        def _on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._db.archive_subject(subject_id)
                self._refresh_list()
                self.post_message(DataChanged())

        self.app.push_screen(ConfirmScreen("Archive this subject?"), _on_confirm)

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        subject_id = getattr(event.item, "_subject_id", None)
        if subject_id:
            self.post_message(SubjectSelected(subject_id))
