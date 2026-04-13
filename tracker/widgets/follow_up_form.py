"""FollowUpForm widget — inline form for adding or editing a follow-up."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label, Select, TextArea

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.comment_editor import CommentEditor
from tracker.widgets.date_input import DateInput


class FollowUpForm(Container):
    """Inline form: top container (fields) + bottom container (comment)."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: Database,
        subject_id: str,
        follow_up_id: Optional[str] = None,
        milestone_id: Optional[str] = None,
    ) -> None:
        super().__init__(classes="item-form")
        self._db = db
        self._subject_id = subject_id
        self._follow_up_id = follow_up_id
        self._follow_up = db.get_follow_up(follow_up_id) if follow_up_id else None
        self._default_milestone_id = milestone_id

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
            initial_due_by = None
            initial_asked_on = None

        with Container(classes="item-form-fields"):
            yield Label(title, classes="overview-col-header")
            yield Label("What", classes="field-label")
            yield Input(value=initial_text, placeholder="What are you waiting for?", id="fu-text-input")
            yield Label("Owner", classes="field-label")
            yield Input(value=initial_owner, placeholder="Who?", id="fu-owner-input")
            yield Label("Due by", classes="field-label")
            yield DateInput(value=initial_due_by, placeholder="YYYY-MM-DD", id="fu-due-by-input")
            yield Label("Asked on", classes="field-label")
            yield DateInput(value=initial_asked_on, placeholder="YYYY-MM-DD", id="fu-asked-on-input")
            yield Label("Notes", classes="field-label")
            yield TextArea(text=initial_notes, id="fu-notes-area")
            # Milestone link
            milestones = self._db.list_milestones(self._subject_id)
            active_ms = [(m.name, m.id) for m in milestones if m.status == "active"]
            if active_ms:
                current_ms_id = self._follow_up.milestone_id if self._follow_up else self._default_milestone_id
                yield Label("Milestone", classes="field-label")
                yield Select(
                    options=active_ms,
                    value=current_ms_id if current_ms_id else Select.NULL,
                    allow_blank=True,
                    id="fu-milestone-select",
                    compact=True,
                )
        yield CommentEditor(text=initial_comment or "", id="fu-comment-editor")

    def on_mount(self) -> None:
        self.query_one("#fu-text-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "fu-text-input":
            self.action_save()

    def action_save(self) -> None:
        text = self.query_one("#fu-text-input", Input).value.strip()
        if not text:
            self.notify("Follow-up text cannot be empty.", severity="error")
            return

        owner = self.query_one("#fu-owner-input", Input).value.strip()
        if not owner:
            self.notify("Owner cannot be empty.", severity="error")
            return

        due_by = self.query_one("#fu-due-by-input", DateInput).date_value
        asked_on = self.query_one("#fu-asked-on-input", DateInput).date_value
        notes = self.query_one("#fu-notes-area", TextArea).text.strip() or None
        comment = self.query_one("#fu-comment-editor", CommentEditor).text.strip() or None

        # Milestone link (optional)
        milestone_id = None
        try:
            ms_select = self.query_one("#fu-milestone-select", Select)
            milestone_id = str(ms_select.value) if ms_select.value != Select.NULL else None
        except Exception:
            pass

        if self._follow_up_id:
            self._db.update_follow_up(self._follow_up_id, text=text, owner=owner, due_by=due_by, asked_on=asked_on)
            self._db.update_follow_up_notes(self._follow_up_id, notes)
            self._db.update_follow_up_comment(self._follow_up_id, comment)
            self._db.link_follow_up_to_milestone(self._follow_up_id, milestone_id)
            saved_id = self._follow_up_id
        else:
            saved_id = self._db.add_follow_up(
                subject_id=self._subject_id, text=text, owner=owner, due_by=due_by, comment=comment,
            )
            if notes:
                self._db.update_follow_up_notes(saved_id, notes)
            if milestone_id:
                self._db.link_follow_up_to_milestone(saved_id, milestone_id)

        self.post_message(DataChanged())
        saved_data = {"subject_id": self._subject_id, "follow_up_id": saved_id}
        if milestone_id:
            saved_data["milestone_id"] = milestone_id
        self.post_message(ContentSaved("follow_up_form", saved_data))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
