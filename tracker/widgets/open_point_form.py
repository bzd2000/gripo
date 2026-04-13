"""OpenPointForm widget — inline form for adding or editing an open point."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.comment_editor import CommentEditor


class OpenPointForm(Container):
    """Inline form: top container (fields) + bottom container (comment)."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: Database,
        subject_id: str,
        point_id: Optional[str] = None,
    ) -> None:
        super().__init__(classes="item-form")
        self._db = db
        self._subject_id = subject_id
        self._point_id = point_id
        self._point = db.get_open_point(point_id) if point_id else None

    def compose(self) -> ComposeResult:
        is_edit = self._point is not None
        title = "Edit Open Point" if is_edit else "New Open Point"

        initial_text = self._point.text if self._point else ""
        initial_context = self._point.context or "" if self._point else ""
        initial_comment = self._point.comment or "" if self._point else ""
        initial_resolved_note = self._point.resolved_note or "" if self._point else ""
        is_resolved = self._point.status == "resolved" if self._point else False

        with Container(classes="item-form-fields"):
            yield Label(title, classes="overview-col-header")
            yield Label("Text", classes="field-label")
            yield Input(value=initial_text, placeholder="Open point text", id="op-text-input")
            yield Label("Context", classes="field-label")
            yield Input(value=initial_context, placeholder="Context (optional)", id="op-context-input")
            if is_resolved:
                yield Label("Resolution note", classes="field-label")
                yield Input(value=initial_resolved_note, placeholder="Resolution note", id="op-resolved-note-input")
        yield CommentEditor(text=initial_comment, id="op-comment-editor")

    def on_mount(self) -> None:
        self.query_one("#op-text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "op-text-input":
            self.action_save()

    def action_save(self) -> None:
        text = self.query_one("#op-text-input", Input).value.strip()
        if not text:
            self.notify("Open point text cannot be empty.", severity="error")
            return

        context = self.query_one("#op-context-input", Input).value.strip() or None
        comment = self.query_one("#op-comment-editor", CommentEditor).text.strip() or None

        if self._point_id:
            self._db.update_open_point_text(self._point_id, text)
            self._db.update_open_point_context(self._point_id, context)
            self._db.update_open_point_comment(self._point_id, comment)
            try:
                resolved_note_input = self.query_one("#op-resolved-note-input", Input)
                resolved_note = resolved_note_input.value.strip() or None
                if resolved_note:
                    self._db.resolve_open_point(self._point_id, resolved_note)
            except Exception:
                pass
            saved_id = self._point_id
        else:
            saved_id = self._db.add_open_point(
                subject_id=self._subject_id, text=text, context=context, comment=comment,
            )

        self.post_message(DataChanged())
        self.post_message(ContentSaved("open_point_form", {"subject_id": self._subject_id, "point_id": saved_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
