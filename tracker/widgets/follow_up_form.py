"""FollowUpForm widget — inline form for adding or editing a follow-up."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Input, Label, TextArea

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.date_input import DateInput


class FollowUpForm(Widget):
    """Inline form for adding or editing a follow-up."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: Database,
        subject_id: str,
        follow_up_id: Optional[str] = None,
    ) -> None:
        super().__init__()
        self._db = db
        self._subject_id = subject_id
        self._follow_up_id = follow_up_id
        self._follow_up = db.get_follow_up(follow_up_id) if follow_up_id else None

    def compose(self) -> ComposeResult:
        fu = self._follow_up
        is_edit = fu is not None
        title = "Edit Follow-Up" if is_edit else "New Follow-Up"

        initial_text = fu.text if fu else ""
        initial_owner = fu.owner if fu else ""
        initial_notes = fu.notes or "" if fu else ""
        initial_comment = fu.comment or "" if fu else ""

        if fu:
            initial_due_by = fu.due_by or ""
            initial_asked_on = fu.asked_on
        else:
            initial_due_by = None  # DateInput defaults to today
            initial_asked_on = None

        with Vertical(classes="form-container"):
            yield Label(title, classes="form-title")
            with Horizontal(classes="form-row"):
                with Vertical():
                    yield Label("What", classes="field-label")
                    yield Input(value=initial_text, placeholder="What are you waiting for?", id="fu-text-input")
                with Vertical():
                    yield Label("Owner", classes="field-label")
                    yield Input(value=initial_owner, placeholder="Who?", id="fu-owner-input")
            with Horizontal(classes="form-row"):
                with Vertical():
                    yield Label("Due by", classes="field-label")
                    yield DateInput(value=initial_due_by, placeholder="YYYY-MM-DD", id="fu-due-by-input")
                with Vertical():
                    yield Label("Asked on", classes="field-label")
                    yield DateInput(value=initial_asked_on, placeholder="YYYY-MM-DD", id="fu-asked-on-input")
            yield Label("Notes", classes="field-label")
            yield TextArea(text=initial_notes, id="fu-notes-area")
            yield Label("Comment", classes="field-label")
            yield TextArea(text=initial_comment, language="markdown", id="fu-comment-area")

    def on_mount(self) -> None:
        self.query_one("#fu-text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "fu-text-input":
            self.action_save()

    def action_save(self) -> None:
        text_input = self.query_one("#fu-text-input", Input)
        owner_input = self.query_one("#fu-owner-input", Input)
        due_by_input = self.query_one("#fu-due-by-input", DateInput)
        notes_area = self.query_one("#fu-notes-area", TextArea)
        comment_area = self.query_one("#fu-comment-area", TextArea)

        text = text_input.value.strip()
        if not text:
            self.notify("Follow-up text cannot be empty.", severity="error")
            return

        owner = owner_input.value.strip()
        if not owner:
            self.notify("Owner cannot be empty.", severity="error")
            return

        due_by = due_by_input.date_value
        notes = notes_area.text.strip() or None
        comment = comment_area.text.strip() or None

        if self._follow_up_id:
            self._db.update_follow_up(self._follow_up_id, text=text, owner=owner, due_by=due_by)
            self._db.update_follow_up_notes(self._follow_up_id, notes)
            self._db.update_follow_up_comment(self._follow_up_id, comment)
            saved_id = self._follow_up_id
        else:
            saved_id = self._db.add_follow_up(
                subject_id=self._subject_id, text=text, owner=owner, due_by=due_by, comment=comment,
            )
            if notes:
                self._db.update_follow_up_notes(saved_id, notes)

        self.post_message(DataChanged())
        self.post_message(ContentSaved("follow_up_form", {"subject_id": self._subject_id, "follow_up_id": saved_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
