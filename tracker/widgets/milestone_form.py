"""MilestoneForm widget — inline form for adding or editing a milestone."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Input, Label, Select

from tracker.db import Database
from tracker.messages import ContentCancelled, ContentSaved, DataChanged
from tracker.widgets.comment_editor import CommentEditor
from tracker.widgets.date_input import DateInput

_STATUS_OPTIONS = [
    ("active", "active"),
    ("completed", "completed"),
    ("cancelled", "cancelled"),
]


class MilestoneForm(Container):
    """Inline form: fields | comment."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        db: Database,
        subject_id: str,
        milestone_id: Optional[str] = None,
    ) -> None:
        super().__init__(classes="item-form")
        self._db = db
        self._subject_id = subject_id
        self._milestone_id = milestone_id
        self._milestone = db.get_milestone(milestone_id) if milestone_id else None

    def compose(self) -> ComposeResult:
        ms = self._milestone
        is_edit = ms is not None
        title = "Edit Milestone" if is_edit else "New Milestone"

        with Container(classes="item-form-fields"):
            yield Label(title, classes="overview-col-header")
            yield Label("Name", classes="field-label")
            yield Input(
                value=ms.name if ms else "",
                placeholder="Milestone name",
                id="ms-name-input",
            )
            yield Label("Target date", classes="field-label")
            yield DateInput(
                value=ms.target_date if ms else None,
                placeholder="YYYY-MM-DD",
                id="ms-date-input",
            )
            yield Label("Lead weeks", classes="field-label")
            yield Input(
                value=str(ms.lead_weeks) if ms and ms.lead_weeks else "",
                placeholder="Weeks before target to start",
                id="ms-lead-weeks-input",
            )
            if is_edit:
                yield Label("Status", classes="field-label")
                yield Select(
                    options=_STATUS_OPTIONS,
                    value=ms.status,
                    id="ms-status-select",
                    compact=True,
                )
        yield CommentEditor(
            text=ms.comment or "" if ms else "",
            id="ms-comment-editor",
        )

    def on_mount(self) -> None:
        self.query_one("#ms-name-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "ms-name-input":
            self.action_save()

    def action_save(self) -> None:
        name = self.query_one("#ms-name-input", Input).value.strip()
        if not name:
            self.notify("Milestone name cannot be empty.", severity="error")
            return

        target_date = self.query_one("#ms-date-input", DateInput).date_value
        lead_weeks_str = self.query_one("#ms-lead-weeks-input", Input).value.strip()
        lead_weeks = int(lead_weeks_str) if lead_weeks_str.isdigit() else None
        comment = self.query_one("#ms-comment-editor", CommentEditor).text.strip() or None

        if self._milestone_id:
            self._db.update_milestone(self._milestone_id, name=name, target_date=target_date, lead_weeks=lead_weeks, comment=comment)
            try:
                status_select = self.query_one("#ms-status-select", Select)
                status = str(status_select.value)
                self._db.update_milestone_status(self._milestone_id, status)
            except Exception:
                pass
            saved_id = self._milestone_id
        else:
            saved_id = self._db.add_milestone(
                subject_id=self._subject_id, name=name, target_date=target_date, lead_weeks=lead_weeks, comment=comment,
            )

        self.post_message(DataChanged())
        self.post_message(ContentSaved("milestone_form", {"subject_id": self._subject_id, "milestone_id": saved_id}))

    def action_cancel(self) -> None:
        self.post_message(ContentCancelled())
