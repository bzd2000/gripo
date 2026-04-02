"""TrackerApp — main Textual application."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, TabbedContent, TabPane

from tracker.db import Database
from tracker.screens.subject_detail import SubjectDetailScreen
from tracker.widgets.subjects_list import SubjectSelected, SubjectsList

_DB_PATH = Path.home() / ".tracker" / "tracker.db"


class TrackerApp(App):
    """Tracker TUI application."""

    CSS_PATH = "tracker.tcss"
    TITLE = "Tracker"

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.db = Database(_DB_PATH)

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane("Subjects", id="subjects-tab"):
                yield SubjectsList(self.db)
            with TabPane("Today", id="today-tab"):
                yield Label("Today view — coming in Phase 2", classes="empty-state")
            with TabPane("This Week", id="week-tab"):
                yield Label("This Week view — coming in Phase 2", classes="empty-state")
        yield Footer()

    def on_subject_selected(self, message: SubjectSelected) -> None:
        self.push_screen(SubjectDetailScreen(self.db, message.subject_id))


def main() -> None:
    """Entry point for the tracker application."""
    app = TrackerApp()
    app.run()
