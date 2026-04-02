"""Tests for open point CRUD methods in Database."""

from __future__ import annotations

import pytest

from tracker.db import Database
from tracker.models import OpenPoint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _subject(db: Database, name: str = "Sub") -> str:
    return db.add_subject(name=name)


# ---------------------------------------------------------------------------
# add_open_point
# ---------------------------------------------------------------------------

def test_add_open_point_returns_id(db: Database) -> None:
    sid = _subject(db)
    point_id = db.add_open_point(subject_id=sid, text="Something unclear")
    assert isinstance(point_id, str)
    assert len(point_id) == 32  # uuid4().hex


def test_add_open_point_default_status_is_open(db: Database) -> None:
    sid = _subject(db)
    point_id = db.add_open_point(subject_id=sid, text="Open by default")
    point = db.get_open_point(point_id)
    assert point is not None
    assert point.status == "open"


def test_add_open_point_with_context(db: Database) -> None:
    sid = _subject(db)
    point_id = db.add_open_point(subject_id=sid, text="With context", context="Discussed in retro")
    point = db.get_open_point(point_id)
    assert point is not None
    assert point.context == "Discussed in retro"


def test_add_open_point_without_context(db: Database) -> None:
    sid = _subject(db)
    point_id = db.add_open_point(subject_id=sid, text="No context")
    point = db.get_open_point(point_id)
    assert point is not None
    assert point.context is None


def test_add_open_point_stores_correct_fields(db: Database) -> None:
    sid = _subject(db)
    point_id = db.add_open_point(subject_id=sid, text="Check fields")
    point = db.get_open_point(point_id)
    assert point is not None
    assert point.id == point_id
    assert point.subject_id == sid
    assert point.text == "Check fields"
    assert point.resolved_note is None
    assert point.resolved_at is None
    assert point.deleted_at is None
    assert point.raised_at is not None


# ---------------------------------------------------------------------------
# get_open_point
# ---------------------------------------------------------------------------

def test_get_open_point_returns_none_for_unknown(db: Database) -> None:
    assert db.get_open_point("nonexistent") is None


def test_get_open_point_returns_none_for_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    point_id = db.add_open_point(subject_id=sid, text="Will be deleted")
    db.soft_delete_open_point(point_id)
    assert db.get_open_point(point_id) is None


def test_get_open_point_returns_open_point(db: Database) -> None:
    sid = _subject(db)
    point_id = db.add_open_point(subject_id=sid, text="Fetch me")
    point = db.get_open_point(point_id)
    assert point is not None
    assert point.id == point_id
    assert point.text == "Fetch me"


# ---------------------------------------------------------------------------
# list_open_points
# ---------------------------------------------------------------------------

def test_list_open_points_excludes_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    db.add_open_point(subject_id=sid, text="Visible")
    pid = db.add_open_point(subject_id=sid, text="Deleted")
    db.soft_delete_open_point(pid)

    points = db.list_open_points(subject_id=sid)
    texts = [p.text for p in points]
    assert "Visible" in texts
    assert "Deleted" not in texts


def test_list_open_points_only_returns_for_subject(db: Database) -> None:
    sid1 = _subject(db, "Sub1")
    sid2 = _subject(db, "Sub2")
    db.add_open_point(subject_id=sid1, text="Point A")
    db.add_open_point(subject_id=sid2, text="Point B")

    points = db.list_open_points(subject_id=sid1)
    assert len(points) == 1
    assert points[0].text == "Point A"


def test_list_open_points_ordered_open_parked_resolved(db: Database) -> None:
    """open first, then parked, then resolved."""
    sid = _subject(db)
    pid_resolved = db.add_open_point(subject_id=sid, text="Resolved point")
    pid_parked = db.add_open_point(subject_id=sid, text="Parked point")
    pid_open = db.add_open_point(subject_id=sid, text="Open point")

    db.update_open_point_status(pid_resolved, "resolved")
    db.update_open_point_status(pid_parked, "parked")

    points = db.list_open_points(subject_id=sid)
    statuses = [p.status for p in points]
    assert statuses[0] == "open"
    assert statuses[1] == "parked"
    assert statuses[2] == "resolved"


def test_list_open_points_returns_empty_for_no_points(db: Database) -> None:
    sid = _subject(db)
    assert db.list_open_points(subject_id=sid) == []


# ---------------------------------------------------------------------------
# update_open_point_status
# ---------------------------------------------------------------------------

def test_update_open_point_status_to_parked(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Park me")
    db.update_open_point_status(pid, "parked")
    point = db.get_open_point(pid)
    assert point.status == "parked"


def test_update_open_point_status_to_resolved(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Resolve via status")
    db.update_open_point_status(pid, "resolved")
    point = db.get_open_point(pid)
    assert point.status == "resolved"


# ---------------------------------------------------------------------------
# resolve_open_point
# ---------------------------------------------------------------------------

def test_resolve_open_point_sets_status_and_note(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Needs resolution")
    db.resolve_open_point(pid, note="Fixed in sprint 3")
    point = db.get_open_point(pid)
    assert point.status == "resolved"
    assert point.resolved_note == "Fixed in sprint 3"


def test_resolve_open_point_sets_resolved_at(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Resolve me")
    db.resolve_open_point(pid, note="Done")
    point = db.get_open_point(pid)
    assert point.resolved_at is not None


def test_resolve_open_point_resolved_at_was_none_before(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Not yet resolved")
    point = db.get_open_point(pid)
    assert point.resolved_at is None


# ---------------------------------------------------------------------------
# update_open_point_text
# ---------------------------------------------------------------------------

def test_update_open_point_text(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Original text")
    db.update_open_point_text(pid, "Updated text")
    point = db.get_open_point(pid)
    assert point.text == "Updated text"


# ---------------------------------------------------------------------------
# update_open_point_context
# ---------------------------------------------------------------------------

def test_update_open_point_context_sets_context(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Some point")
    db.update_open_point_context(pid, "New context info")
    point = db.get_open_point(pid)
    assert point.context == "New context info"


def test_update_open_point_context_clears_context(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Has context", context="Original context")
    db.update_open_point_context(pid, None)
    point = db.get_open_point(pid)
    assert point.context is None


# ---------------------------------------------------------------------------
# soft_delete_open_point
# ---------------------------------------------------------------------------

def test_soft_delete_open_point_sets_deleted_at(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Delete me")
    db.soft_delete_open_point(pid)
    row = db.conn.execute(
        "SELECT deleted_at FROM open_points WHERE id = ?", (pid,)
    ).fetchone()
    assert row["deleted_at"] is not None


def test_soft_delete_open_point_excludes_from_list(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Gone")
    db.soft_delete_open_point(pid)
    points = db.list_open_points(subject_id=sid)
    assert all(p.id != pid for p in points)
