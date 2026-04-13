"""Tests for the DateInput widget."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from tracker.widgets.date_input import _DateField


# ---------------------------------------------------------------------------
# Helper — test logic without running a Textual app
# ---------------------------------------------------------------------------

class _DateFieldStub(_DateField):
    """Subclass that replaces Textual's __init__ and value reactive with simple attrs."""

    def __init__(self, value: str | None = None) -> None:
        initial = value if value is not None else date.today().isoformat()
        self._stub_value: str = initial

    @property  # type: ignore[override]
    def value(self) -> str:
        return self._stub_value

    @value.setter
    def value(self, v: str) -> None:
        self._stub_value = v

    @property
    def date_value(self):
        return self._parse_date(self.value)


def _w(value: str | None = None) -> _DateFieldStub:
    return _DateFieldStub(value)


# ---------------------------------------------------------------------------
# _parse_date (static helper)
# ---------------------------------------------------------------------------

def test_parse_date_valid() -> None:
    assert _DateField._parse_date("2026-04-01") == "2026-04-01"


def test_parse_date_strips_whitespace() -> None:
    assert _DateField._parse_date("  2026-04-01  ") == "2026-04-01"


def test_parse_date_invalid() -> None:
    assert _DateField._parse_date("not-a-date") is None


def test_parse_date_empty() -> None:
    assert _DateField._parse_date("") is None


# ---------------------------------------------------------------------------
# _shift_months (static helper)
# ---------------------------------------------------------------------------

def test_shift_months_normal() -> None:
    d = date(2026, 4, 15)
    assert _DateField._shift_months(d, 1) == date(2026, 5, 15)
    assert _DateField._shift_months(d, -1) == date(2026, 3, 15)


def test_shift_months_year_wrap_forward() -> None:
    assert _DateField._shift_months(date(2026, 12, 15), 1) == date(2027, 1, 15)


def test_shift_months_year_wrap_backward() -> None:
    assert _DateField._shift_months(date(2026, 1, 15), -1) == date(2025, 12, 15)


def test_shift_months_day_clamped_feb_non_leap() -> None:
    assert _DateField._shift_months(date(2026, 3, 31), -1) == date(2026, 2, 28)


def test_shift_months_day_clamped_feb_leap() -> None:
    assert _DateField._shift_months(date(2024, 3, 31), -1) == date(2024, 2, 29)


def test_shift_months_jan_31_forward_to_feb() -> None:
    assert _DateField._shift_months(date(2026, 1, 31), 1) == date(2026, 2, 28)


# ---------------------------------------------------------------------------
# Default pre-fill
# ---------------------------------------------------------------------------

def test_default_prefill_is_today() -> None:
    widget = _w()
    assert widget.value == date.today().isoformat()


def test_explicit_value_is_used() -> None:
    widget = _w("2025-12-31")
    assert widget.value == "2025-12-31"


# ---------------------------------------------------------------------------
# date_value property
# ---------------------------------------------------------------------------

def test_date_value_returns_iso_when_valid() -> None:
    widget = _w("2026-06-15")
    assert widget.date_value == "2026-06-15"


def test_date_value_returns_none_when_invalid() -> None:
    widget = _w("hello")
    assert widget.date_value is None


def test_date_value_returns_none_when_empty() -> None:
    widget = _w("")
    assert widget.date_value is None


# ---------------------------------------------------------------------------
# Arrow key navigation — day shift
# ---------------------------------------------------------------------------

def _key_event(key: str) -> MagicMock:
    event = MagicMock()
    event.key = key
    return event


def test_left_arrow_decreases_by_one_day() -> None:
    widget = _w("2026-04-15")
    event = _key_event("left")
    widget._on_key(event)
    assert widget.value == "2026-04-14"
    event.prevent_default.assert_called_once()
    event.stop.assert_called_once()


def test_right_arrow_increases_by_one_day() -> None:
    widget = _w("2026-04-15")
    event = _key_event("right")
    widget._on_key(event)
    assert widget.value == "2026-04-16"
    event.prevent_default.assert_called_once()
    event.stop.assert_called_once()


def test_left_arrow_wraps_month_boundary() -> None:
    widget = _w("2026-04-01")
    widget._on_key(_key_event("left"))
    assert widget.value == "2026-03-31"


def test_right_arrow_wraps_month_boundary() -> None:
    widget = _w("2026-03-31")
    widget._on_key(_key_event("right"))
    assert widget.value == "2026-04-01"


# ---------------------------------------------------------------------------
# Arrow key navigation — month shift
# ---------------------------------------------------------------------------

def test_up_arrow_increases_by_one_month() -> None:
    widget = _w("2026-04-15")
    event = _key_event("up")
    widget._on_key(event)
    assert widget.value == "2026-05-15"
    event.prevent_default.assert_called_once()
    event.stop.assert_called_once()


def test_down_arrow_decreases_by_one_month() -> None:
    widget = _w("2026-04-15")
    event = _key_event("down")
    widget._on_key(event)
    assert widget.value == "2026-03-15"
    event.prevent_default.assert_called_once()
    event.stop.assert_called_once()


def test_up_arrow_wraps_year_boundary() -> None:
    widget = _w("2026-12-15")
    widget._on_key(_key_event("up"))
    assert widget.value == "2027-01-15"


def test_down_arrow_wraps_year_boundary() -> None:
    widget = _w("2026-01-15")
    widget._on_key(_key_event("down"))
    assert widget.value == "2025-12-15"


# ---------------------------------------------------------------------------
# Month boundary clamping
# ---------------------------------------------------------------------------

def test_down_arrow_march_31_clamps_to_feb_28() -> None:
    widget = _w("2026-03-31")
    widget._on_key(_key_event("down"))
    assert widget.value == "2026-02-28"


def test_down_arrow_march_31_clamps_to_feb_29_leap_year() -> None:
    widget = _w("2024-03-31")
    widget._on_key(_key_event("down"))
    assert widget.value == "2024-02-29"


def test_up_arrow_jan_31_clamps_to_feb_28() -> None:
    widget = _w("2026-01-31")
    widget._on_key(_key_event("up"))
    assert widget.value == "2026-02-28"


def test_up_arrow_jan_31_clamps_to_feb_29_leap_year() -> None:
    widget = _w("2024-01-31")
    widget._on_key(_key_event("up"))
    assert widget.value == "2024-02-29"


# ---------------------------------------------------------------------------
# Arrow keys do nothing when value is invalid/empty
# ---------------------------------------------------------------------------

def test_arrow_keys_ignored_when_invalid_date() -> None:
    widget = _w("not-a-date")
    original_value = widget.value
    for key in ("left", "right", "up", "down"):
        event = _key_event(key)
        widget._on_key(event)
        assert widget.value == original_value
        event.prevent_default.assert_not_called()


def test_arrow_keys_ignored_when_empty() -> None:
    widget = _w("")
    for key in ("left", "right", "up", "down"):
        event = _key_event(key)
        widget._on_key(event)
        assert widget.value == ""
        event.prevent_default.assert_not_called()


# ---------------------------------------------------------------------------
# Non-arrow keys are not intercepted
# ---------------------------------------------------------------------------

def test_other_keys_not_intercepted() -> None:
    widget = _w("2026-04-15")
    original_value = widget.value
    event = _key_event("backspace")
    widget._on_key(event)
    assert widget.value == original_value
    event.prevent_default.assert_not_called()
    event.stop.assert_not_called()
