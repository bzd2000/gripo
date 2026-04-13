"""TrackerApp — main Textual application."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer, Header

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged, ShowContent
from tracker.screens.help import HelpScreen
from tracker.screens.search import SearchScreen
from tracker.widgets.content_area import ContentArea
from tracker.widgets.nav_tree import NavTree

_DB_PATH = Path.home() / ".tracker" / "tracker.db"


class TrackerApp(App):
    """Tracker TUI application."""

    CSS_PATH = "tracker.tcss"
    TITLE = "Tracker"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("/", "search", "Search"),
        ("question_mark", "help", "Help"),
        Binding("ctrl+w", "focus_tree", "Focus tree", priority=True),
    ]

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        super().__init__()
        self.db = Database(db_path)

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-grid"):
            yield NavTree(self.db)
            yield ContentArea(self.db)
        yield Footer()

    def on_mount(self) -> None:
        rolled = self.db.perform_week_rollover()
        if rolled:
            self.notify("Week rolled over — tasks reset for the new week.")
        self.query_one(NavTree).rebuild()
        # Show Today view initially
        self.query_one(ContentArea).on_show_content(
            ShowContent(content_type="overview", data={})
        )

    def on_show_content(self, message: ShowContent) -> None:
        """Forward ShowContent to ContentArea and reveal in tree."""
        self.query_one(ContentArea).on_show_content(message)
        nav = self.query_one(NavTree)
        # Only reveal in tree if the action didn't come from the tree itself
        if not nav.has_focus:
            nav.reveal_content(message.content_type, message.data)

    def on_data_changed(self, message: DataChanged) -> None:
        """Refresh the nav tree when data changes."""
        self.query_one(NavTree).refresh_tree()

    def on_unmount(self) -> None:
        self.db.close()

    def action_focus_tree(self) -> None:
        try:
            self.query_one(NavTree).focus()
        except Exception:
            pass

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_search(self) -> None:
        def _on_result(result: dict | None) -> None:
            if result is None:
                return
            if result["type"] == "subject":
                subject_id = result["id"]
                self.post_message(ShowContent(content_type="subject_overview", data={"subject_id": subject_id}))
            elif result["type"] == "task":
                self.post_message(ShowContent(content_type="task_form", data={"subject_id": result["subject_id"], "task_id": result["id"]}))
            elif result["type"] == "note":
                self.post_message(ShowContent(content_type="note_editor", data={"subject_id": result["subject_id"], "note_id": result["id"]}))
            elif result["type"] == "open_point":
                self.post_message(ShowContent(content_type="open_point_form", data={"subject_id": result["subject_id"], "point_id": result["id"]}))
            elif result["type"] == "follow_up":
                self.post_message(ShowContent(content_type="follow_up_form", data={"subject_id": result["subject_id"], "follow_up_id": result["id"]}))
            elif result["type"] == "milestone":
                self.post_message(ShowContent(content_type="milestone_view", data={"subject_id": result["subject_id"], "milestone_id": result["id"]}))

        self.push_screen(SearchScreen(self.db), _on_result)


def main() -> None:
    """Entry point for the tracker application."""
    app = TrackerApp()
    app.run()
