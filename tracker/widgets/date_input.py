"""DateInput widget — a text Input pre-filled with today and navigable with arrow keys."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Optional

from textual.widgets import Input


class DateInput(Input):
    """A text Input pre-filled with today's date.

    When the current value is a valid ISO date (YYYY-MM-DD):
    - Left arrow : decrease by 1 day
    - Right arrow: increase by 1 day
    - Up arrow   : increase by 1 month (day clamped to month boundary)
    - Down arrow : decrease by 1 month (day clamped to month boundary)

    Backspace/Delete work normally.  The field is still editable as free text.
    """

    def __init__(
        self,
        value: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        initial = value if value is not None else date.today().isoformat()
        super().__init__(value=initial, *args, **kwargs)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def date_value(self) -> Optional[str]:
        """Return current text if it is a valid ISO date, else None."""
        return self._parse_date(self.value)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date(text: str) -> Optional[str]:
        """Return the ISO string if valid, else None."""
        try:
            date.fromisoformat(text.strip())
            return text.strip()
        except ValueError:
            return None

    @staticmethod
    def _shift_months(d: date, delta: int) -> date:
        """Add *delta* months to *d*, clamping the day to the target month."""
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

    # ------------------------------------------------------------------
    # Key handling
    # ------------------------------------------------------------------

    def _on_key(self, event) -> None:  # type: ignore[override]
        """Intercept arrow keys to navigate dates when value is a valid date."""
        current = self._current_date()
        if current is None:
            return  # let Input handle everything normally

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
