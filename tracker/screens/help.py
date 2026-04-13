"""HelpScreen — keyboard shortcut reference."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

_HELP_TEXT = """\
╔══════════════════════════════════════════╗
║         TRACKER — KEYBOARD SHORTCUTS     ║
╚══════════════════════════════════════════╝

GLOBAL
  q            Quit
  /            Search (all content)
  ?            Show this help screen

SUBJECTS LIST
  a            Add subject
  p            Pin / unpin subject
  x            Archive subject
  Enter        Open subject detail

SUBJECT DETAIL
  Esc          Back to subjects list
  1            Jump to Tasks section
  2            Jump to Open Points section
  3            Jump to Follow-Ups section
  4            Jump to Notes section

  TASKS
    a          Add task
    e          Edit task (text / priority / category)
    d          Toggle done
    b          Toggle blocked
    s          Cycle status (todo → in-progress → done → blocked)
    p          Cycle priority (must → should → if-time)
    t          Toggle today flag
    w          Cycle day (mon → tue → … → anytime)
    x          Delete task

  OPEN POINTS
    a / o      Add open point
    e          Edit text
    c          Edit context
    r          Resolve with note
    s          Cycle status (open → parked → resolved)
    x          Delete open point

  FOLLOW-UPS
    a          Add follow-up
    e          Edit follow-up
    s          Cycle status (waiting → received → overdue → cancelled)
    n          Edit notes
    x          Delete follow-up

  NOTES
    a / n      Add note
    e          Edit note
    x          Delete note

TODAY
  d            Toggle done
  s            Cycle status
  p            Cycle priority
  Enter        Open subject for highlighted task

THIS WEEK
  d            Toggle done
  s            Cycle status
  p            Cycle priority
  w            Cycle day assignment
  Enter        Open subject for highlighted task

Press Esc or ? to close this screen.
"""


class HelpScreen(ModalScreen):
    """Keyboard shortcut reference screen."""

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("question_mark", "close", "Close", key_display="?"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            with ScrollableContainer(id="help-container"):
                yield Static(_HELP_TEXT, id="help-content")

    def action_close(self) -> None:
        self.dismiss()
