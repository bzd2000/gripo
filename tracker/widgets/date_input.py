"""DateInput widget — a text Input pre-filled with today and navigable with arrow keys."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Input, Label


class _DateField(Input):
    """Inner Input that handles arrow-key date navigation."""

    @staticmethod
    def _parse_date(text: str) -> Optional[str]:
        try:
            date.fromisoformat(text.strip())
            return text.strip()
        except ValueError:
            return None

    @staticmethod
    def _shift_months(d: date, delta: int) -> date:
        month = d.month + delta
        year = d.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        max_day = calendar.monthrange(year, month)[1]
        day = min(d.day, max_day)
        return date(year, month, day)

    def _current_date(self) -> Optional[date]:
        raw = self._parse_date(self.value)
        if raw is None:
            return None
        return date.fromisoformat(raw)

    def _set_date(self, d: date) -> None:
        self.value = d.isoformat()

    def _on_key(self, event) -> None:  # type: ignore[override]
        current = self._current_date()
        if current is None:
            return

        key = event.key
        if key == "left":
            self._set_date(current - timedelta(days=1))
            event.prevent_default()
            event.stop()
        elif key == "right":
            self._set_date(current + timedelta(days=1))
            event.prevent_default()
            event.stop()
        elif key == "up":
            self._set_date(self._shift_months(current, 1))
            event.prevent_default()
            event.stop()
        elif key == "down":
            self._set_date(self._shift_months(current, -1))
            event.prevent_default()
            event.stop()


def _day_prefix(value: str) -> str:
    """Return short day name for a date string, or empty."""
    try:
        d = date.fromisoformat(value.strip())
        return d.strftime("%a")
    except ValueError:
        return "   "


class DateInput(Widget):
    """Date input with a read-only day-of-week prefix that updates reactively.

    Displays as: `Mon 2026-04-13` with the day prefix auto-updating.
    """

    def __init__(
        self,
        value: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        # Extract Widget-compatible kwargs
        widget_kwargs = {}
        for k in ("id", "classes", "name", "disabled"):
            if k in kwargs:
                widget_kwargs[k] = kwargs.pop(k)
        super().__init__(**widget_kwargs)
        self._initial = value if value is not None else date.today().isoformat()
        self._placeholder = kwargs.pop("placeholder", "YYYY-MM-DD")

    def compose(self) -> ComposeResult:
        prefix = _day_prefix(self._initial)
        yield Label(prefix, id="date-prefix")
        yield _DateField(
            value=self._initial,
            placeholder=self._placeholder,
            id="date-field",
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        """Update day prefix when the date value changes."""
        prefix = _day_prefix(event.value)
        try:
            self.query_one("#date-prefix", Label).update(prefix)
        except Exception:
            pass

    @property
    def date_value(self) -> Optional[str]:
        """Return current text if it is a valid ISO date, else None."""
        try:
            field = self.query_one("#date-field", _DateField)
            return field._parse_date(field.value)
        except Exception:
            return None

    @property
    def value(self) -> str:
        try:
            return self.query_one("#date-field", _DateField).value
        except Exception:
            return self._initial

    @value.setter
    def value(self, val: str) -> None:
        try:
            self.query_one("#date-field", _DateField).value = val
        except Exception:
            pass
