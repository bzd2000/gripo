"""SearchScreen — modal search across all content."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListItem, ListView

from tracker.db import Database

_TYPE_ICON = {
    "subject": "📁",
    "task": "☐",
    "note": "📝",
    "open_point": "?",
    "follow_up": "⏳",
}

_TYPE_LABEL = {
    "subject": "subject",
    "task": "task",
    "note": "note",
    "open_point": "open point",
    "follow_up": "follow-up",
}

_MIN_CHARS = 2


def _result_label(result: dict) -> str:
    icon = _TYPE_ICON.get(result["type"], "?")
    type_label = _TYPE_LABEL.get(result["type"], result["type"])
    preview = result["match_text"]
    if len(preview) > 60:
        preview = preview[:57] + "..."
    return f"{icon} [{type_label}] {preview}"


class SearchScreen(ModalScreen):
    """Modal search screen — type to find subjects, tasks, notes, etc."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, db: Database) -> None:
        super().__init__()
        self._db = db
        self._results: list[dict] = []

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Search... (min 2 chars)", id="search-input")
        yield ListView(id="search-results")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        query = event.value.strip()
        list_view = self.query_one("#search-results", ListView)
        list_view.clear()
        self._results = []

        if len(query) < _MIN_CHARS:
            return

        results = self._db.search(query)
        self._results = results

        if not results:
            item = ListItem(Label("No results found.", classes="empty-state"))
            item._result = None  # type: ignore[attr-defined]
            list_view.append(item)
            return

        for result in results:
            item = ListItem(Label(_result_label(result)))
            item._result = result  # type: ignore[attr-defined]
            list_view.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        result = getattr(event.item, "_result", None)
        if result is not None:
            self.dismiss(result)

    def action_cancel(self) -> None:
        self.dismiss(None)
