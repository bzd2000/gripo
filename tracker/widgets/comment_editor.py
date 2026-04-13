"""CommentEditor widget — markdown view/edit toggle for comments."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, Markdown, TextArea


class CommentEditor(VerticalScroll, can_focus=True):
    """Shows markdown rendered comment; Enter to edit, Escape to return to view."""

    def __init__(self, text: str = "", id: str | None = None) -> None:
        super().__init__(id=id)
        self._content = text
        self._editing = False

    @property
    def text(self) -> str:
        if self._editing:
            try:
                return self.query_one(TextArea).text
            except Exception:
                return self._content
        return self._content

    def compose(self) -> ComposeResult:
        yield Label("COMMENT", classes="overview-col-header")
        if self._content:
            yield Markdown(self._content)
        else:
            yield Label("(empty -- press Enter to edit)", classes="empty-state")

    def _enter_edit(self) -> None:
        if self._editing:
            return
        self._editing = True
        self.remove_children()
        area = TextArea(text=self._content, language="markdown", id="comment-area")
        self.mount(Label("COMMENT (Esc to finish)", classes="overview-col-header"))
        self.mount(area)
        area.focus()

    def _exit_edit(self) -> None:
        if not self._editing:
            return
        self._content = self.query_one(TextArea).text
        self._editing = False
        self.remove_children()
        self.mount(Label("COMMENT", classes="overview-col-header"))
        if self._content.strip():
            self.mount(Markdown(self._content))
        else:
            self.mount(Label("(empty -- press Enter to edit)", classes="empty-state"))
        self.focus()

    def on_key(self, event) -> None:
        if not self._editing and event.key == "enter":
            event.stop()
            event.prevent_default()
            self._enter_edit()
        elif self._editing and event.key == "escape":
            event.stop()
            event.prevent_default()
            self._exit_edit()
