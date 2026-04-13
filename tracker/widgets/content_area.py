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

    def set_content(self, widget: Widget) -> None:
        """Replace current content with the given widget."""
        self.remove_children()
        self.mount(widget)
        widget.focus()

    # ------------------------------------------------------------------
    # Message handlers
    # ------------------------------------------------------------------

    def on_show_content(self, message: ShowContent) -> None:
        """Create and display the appropriate widget for the given content_type."""
        self._current_content_type = message.content_type
        self._current_data = message.data
        widget = self._create_widget(message.content_type, message.data)
        if widget is not None:
            self.set_content(widget)

    def on_content_saved(self, message: ContentSaved) -> None:
        """Navigate back to the parent list after a save, then reveal the item in tree."""
        self._navigate_to_parent(message.content_type, message.data)
        # Reveal the saved item in the tree after a short delay (tree needs to rebuild first)
        from tracker.widgets.nav_tree import NavTree
        try:
            nav = self.app.query_one(NavTree)
            nav.set_timer(0.15, lambda: nav.reveal_content(message.content_type, message.data))
        except Exception:
            pass

    def on_content_cancelled(self, message: ContentCancelled) -> None:
        """First Escape: focus tree on current node. Tree handles further navigation."""
        from tracker.widgets.nav_tree import NavTree
        try:
            nav = self.app.query_one(NavTree)
            nav.focus()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Widget factory
    # ------------------------------------------------------------------

    def _create_widget(self, content_type: str, data: dict) -> Widget | None:
        """Instantiate the widget matching content_type."""
        subject_id = data.get("subject_id")

        if content_type in ("today", "week", "overview"):
            from tracker.widgets.overview_view import OverviewView
            return OverviewView(self._db)

        elif content_type == "subject_overview":
            from tracker.widgets.overview_view import OverviewView
            return OverviewView(self._db, subject_id=subject_id)

        elif content_type == "task_list":
            from tracker.widgets.task_list import TaskList
            return TaskList(self._db, subject_id)

        elif content_type == "task_form":
            try:
                from tracker.widgets.task_form import TaskForm
                task_id = data.get("task_id")
                milestone_id = data.get("milestone_id")
                return TaskForm(self._db, subject_id, task_id, milestone_id=milestone_id)
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
                milestone_id = data.get("milestone_id")
                return FollowUpForm(self._db, subject_id, follow_up_id, milestone_id=milestone_id)
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
                return SubjectForm(self._db, subject_id=data.get("subject_id"))
            except ImportError:
                from textual.widgets import Label
                return Label("Subject form")

        elif content_type == "milestone_list":
            from tracker.widgets.milestone_list import MilestoneList
            return MilestoneList(self._db, subject_id)

        elif content_type == "milestone_form":
            from tracker.widgets.milestone_form import MilestoneForm
            milestone_id = data.get("milestone_id")
            return MilestoneForm(self._db, subject_id, milestone_id)

        elif content_type == "milestone_view":
            from tracker.widgets.milestone_view import MilestoneView
            milestone_id = data.get("milestone_id")
            return MilestoneView(self._db, subject_id, milestone_id)

        return None

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def _navigate_to_parent(self, content_type: str, data: dict) -> None:
        """Navigate back to the appropriate parent list after save/cancel."""
        subject_id = data.get("subject_id")

        milestone_id = data.get("milestone_id")

        parent_mapping = {
            # Forms → parent list (or milestone view if created from milestone)
            "task_form": ("milestone_view", {"subject_id": subject_id, "milestone_id": milestone_id}) if milestone_id else ("task_list", {"subject_id": subject_id}),
            "open_point_form": ("open_points_list", {"subject_id": subject_id}),
            "follow_up_form": ("milestone_view", {"subject_id": subject_id, "milestone_id": milestone_id}) if milestone_id else ("follow_ups_list", {"subject_id": subject_id}),
            "note_editor": ("notes_list", {"subject_id": subject_id}),
            "subject_form": ("subject_overview", {"subject_id": subject_id}) if subject_id else ("overview", {}),
            "milestone_form": ("milestone_view", {"subject_id": subject_id, "milestone_id": data.get("milestone_id")}) if data.get("milestone_id") else ("milestone_list", {"subject_id": subject_id}),
            # Lists → subject overview
            "task_list": ("subject_overview", {"subject_id": subject_id}),
            "open_points_list": ("subject_overview", {"subject_id": subject_id}),
            "follow_ups_list": ("subject_overview", {"subject_id": subject_id}),
            "notes_list": ("subject_overview", {"subject_id": subject_id}),
            "milestone_list": ("subject_overview", {"subject_id": subject_id}),
            # Milestone view → milestone list
            "milestone_view": ("milestone_list", {"subject_id": subject_id}),
            # Subject overview → overview
            "subject_overview": ("overview", {}),
        }

        from tracker.widgets.nav_tree import NavTree

        if content_type in parent_mapping:
            parent_type, parent_data = parent_mapping[content_type]
            widget = self._create_widget(parent_type, parent_data)
            if widget is not None:
                self._current_content_type = parent_type
                self._current_data = parent_data
                self.set_content(widget)
                # Update tree cursor to match
                try:
                    nav = self.app.query_one(NavTree)
                    if parent_type == "overview":
                        nav.move_cursor(nav.root)
                    elif parent_type == "subject_overview":
                        nav.reveal_content(parent_type, parent_data)
                    elif parent_type in ("task_list", "open_points_list", "follow_ups_list",
                                         "notes_list", "milestone_list"):
                        # Select the section node in the tree
                        nav.reveal_section(parent_type, parent_data)
                except Exception:
                    pass
        else:
            # No parent — focus the tree
            try:
                nav = self.app.query_one(NavTree)
                nav.move_cursor(nav.root)
                nav.focus()
            except Exception:
                pass
