from textual.app import App


class TrackerApp(App):
    """Tracker TUI application."""

    def main() -> None:
        pass


def main() -> None:
    """Entry point for the tracker application."""
    app = TrackerApp()
    app.run()
