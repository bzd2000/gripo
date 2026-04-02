"""ContentArea widget — manages the right content pane."""

from __future__ import annotations

from textual.containers import Container
from textual.widget import Widget

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, ShowContent


class ContentArea(Container):
    """Container that manages the right-pane content, swapping widgets on demand."""

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db
        self._current_content_type: str | None = None
        self._current_data: dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show(self, widget: Widget) -> None:
        """Replace current content with the given widget."""
        self.remove_children()
        self.mount(widget)

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    def on_show_content(self, message: ShowContent) -> None:
        """Create and display the appropriate widget for the given content_type."""
        self._current_content_type = message.content_type
        self._current_data = message.data
        widget = self._create_widget(message.content_type, message.data)
        if widget is not None:
            self.show(widget)

    def on_content_saved(self, message: ContentSaved) -> None:
        """Navigate back to the parent list after a save."""
        self._navigate_to_parent(message.content_type, message.data)

    def on_content_cancelled(self, message: ContentCancelled) -> None:
        """Navigate back to the parent list after cancellation."""
        if self._current_content_type is not None:
            self._navigate_to_parent(self._current_content_type, self._current_data)

    # ------------------------------------------------------------------
    # Widget factory
    # ------------------------------------------------------------------

    def _create_widget(self, content_type: str, data: dict) -> Widget | None:
        """Instantiate the widget matching content_type."""
        subject_id = data.get("subject_id")

        if content_type == "today":
            from tracker.widgets.today_view import TodayView
            return TodayView(self._db)

        elif content_type == "week":
            from tracker.widgets.week_view import WeekView
            return WeekView(self._db)

        elif content_type == "subject_overview":
            try:
                from tracker.widgets.subject_overview import SubjectOverview
                return SubjectOverview(self._db, subject_id)
            except ImportError:
                from textual.widgets import Label
                return Label(f"Subject overview for {subject_id}")

        elif content_type == "task_list":
            from tracker.widgets.task_list import TaskList
            return TaskList(self._db, subject_id)

        elif content_type == "task_form":
            try:
                from tracker.widgets.task_form import TaskForm
                task_id = data.get("task_id")
                return TaskForm(self._db, subject_id, task_id)
            except ImportError:
                from textual.widgets import Label
                return Label(f"Task form (subject={subject_id})")

        elif content_type == "open_points_list":
            from tracker.widgets.open_points_list import OpenPointsList
            return OpenPointsList(self._db, subject_id)

        elif content_type == "open_point_form":
            try:
                from tracker.widgets.open_point_form import OpenPointForm
                point_id = data.get("point_id")
                return OpenPointForm(self._db, subject_id, point_id)
            except ImportError:
                from textual.widgets import Label
                return Label(f"Open point form (subject={subject_id})")

        elif content_type == "follow_ups_list":
            from tracker.widgets.follow_ups_list import FollowUpsList
            return FollowUpsList(self._db, subject_id)

        elif content_type == "follow_up_form":
            try:
                from tracker.widgets.follow_up_form import FollowUpForm
                follow_up_id = data.get("follow_up_id")
                return FollowUpForm(self._db, subject_id, follow_up_id)
            except ImportError:
                from textual.widgets import Label
                return Label(f"Follow-up form (subject={subject_id})")

        elif content_type == "notes_list":
            from tracker.widgets.notes_list import NotesList
            return NotesList(self._db, subject_id)

        elif content_type == "note_editor":
            try:
                from tracker.widgets.note_editor import NoteEditor
                note_id = data.get("note_id")
                return NoteEditor(self._db, subject_id, note_id)
            except ImportError:
                from textual.widgets import Label
                return Label(f"Note editor (subject={subject_id})")

        elif content_type == "subject_form":
            try:
                from tracker.widgets.subject_form import SubjectForm
                return SubjectForm(self._db)
            except ImportError:
                from textual.widgets import Label
                return Label("Subject form")

        return None

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _navigate_to_parent(self, content_type: str, data: dict) -> None:
        """Navigate back to the appropriate parent list after save/cancel."""
        subject_id = data.get("subject_id")

        parent_mapping = {
            "task_form": ("task_list", {"subject_id": subject_id}),
            "open_point_form": ("open_points_list", {"subject_id": subject_id}),
            "follow_up_form": ("follow_ups_list", {"subject_id": subject_id}),
            "note_editor": ("notes_list", {"subject_id": subject_id}),
            "subject_form": ("today", {}),
        }

        if content_type in parent_mapping:
            parent_type, parent_data = parent_mapping[content_type]
            widget = self._create_widget(parent_type, parent_data)
            if widget is not None:
                self._current_content_type = parent_type
                self._current_data = parent_data
                self.show(widget)
