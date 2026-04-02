"""Tests for follow-up CRUD methods in Database."""

from __future__ import annotations

import pytest

from tracker.db import Database
from tracker.models import FollowUp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _subject(db: Database, name: str = "Sub") -> str:
    return db.add_subject(name=name)


# ---------------------------------------------------------------------------
# add_follow_up
# ---------------------------------------------------------------------------

def test_add_follow_up_returns_id(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Waiting on reply", owner="Alice")
    assert isinstance(fid, str)
    assert len(fid) == 32  # uuid4().hex


def test_add_follow_up_default_status_is_waiting(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Default status", owner="Bob")
    fu = db.get_follow_up(fid)
    assert fu is not None
    assert fu.status == "waiting"


def test_add_follow_up_with_due_by(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Has due date", owner="Carol", due_by="2026-04-15")
    fu = db.get_follow_up(fid)
    assert fu is not None
    assert fu.due_by == "2026-04-15"


def test_add_follow_up_without_due_by(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="No due date", owner="Dave")
    fu = db.get_follow_up(fid)
    assert fu is not None
    assert fu.due_by is None


def test_add_follow_up_stores_correct_fields(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Check fields", owner="Eve")
    fu = db.get_follow_up(fid)
    assert fu is not None
    assert fu.id == fid
    assert fu.subject_id == sid
    assert fu.text == "Check fields"
    assert fu.owner == "Eve"
    assert fu.notes is None
    assert fu.deleted_at is None
    assert fu.asked_on is not None


# ---------------------------------------------------------------------------
# get_follow_up
# ---------------------------------------------------------------------------

def test_get_follow_up_returns_none_for_unknown(db: Database) -> None:
    assert db.get_follow_up("nonexistent") is None


def test_get_follow_up_returns_none_for_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Will be deleted", owner="Frank")
    db.soft_delete_follow_up(fid)
    assert db.get_follow_up(fid) is None


def test_get_follow_up_returns_follow_up(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Fetch me", owner="Grace")
    fu = db.get_follow_up(fid)
    assert fu is not None
    assert fu.id == fid
    assert fu.text == "Fetch me"
    assert fu.owner == "Grace"


# ---------------------------------------------------------------------------
# list_follow_ups
# ---------------------------------------------------------------------------

def test_list_follow_ups_excludes_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    db.add_follow_up(subject_id=sid, text="Visible", owner="A")
    fid = db.add_follow_up(subject_id=sid, text="Deleted", owner="B")
    db.soft_delete_follow_up(fid)

    follow_ups = db.list_follow_ups(subject_id=sid)
    texts = [f.text for f in follow_ups]
    assert "Visible" in texts
    assert "Deleted" not in texts


def test_list_follow_ups_only_returns_for_subject(db: Database) -> None:
    sid1 = _subject(db, "Sub1")
    sid2 = _subject(db, "Sub2")
    db.add_follow_up(subject_id=sid1, text="FU A", owner="A")
    db.add_follow_up(subject_id=sid2, text="FU B", owner="B")

    follow_ups = db.list_follow_ups(subject_id=sid1)
    assert len(follow_ups) == 1
    assert follow_ups[0].text == "FU A"


def test_list_follow_ups_ordered_waiting_overdue_rest(db: Database) -> None:
    """waiting first, overdue second, then others."""
    sid = _subject(db)
    fid_received = db.add_follow_up(subject_id=sid, text="Received FU", owner="A")
    fid_overdue = db.add_follow_up(subject_id=sid, text="Overdue FU", owner="B")
    fid_waiting = db.add_follow_up(subject_id=sid, text="Waiting FU", owner="C")
    fid_cancelled = db.add_follow_up(subject_id=sid, text="Cancelled FU", owner="D")

    db.update_follow_up_status(fid_received, "received")
    db.update_follow_up_status(fid_overdue, "overdue")
    db.update_follow_up_status(fid_cancelled, "cancelled")

    follow_ups = db.list_follow_ups(subject_id=sid)
    statuses = [f.status for f in follow_ups]
    assert statuses[0] == "waiting"
    assert statuses[1] == "overdue"
    # remaining (received, cancelled) come after overdue


def test_list_follow_ups_returns_empty_for_no_follow_ups(db: Database) -> None:
    sid = _subject(db)
    assert db.list_follow_ups(subject_id=sid) == []


def test_list_follow_ups_ordered_by_due_by_asc_nulls_last(db: Database) -> None:
    """Among same status, order by due_by ASC NULLS LAST."""
    sid = _subject(db)
    fid_later = db.add_follow_up(subject_id=sid, text="Later", owner="A", due_by="2026-05-01")
    fid_sooner = db.add_follow_up(subject_id=sid, text="Sooner", owner="B", due_by="2026-04-01")
    fid_no_due = db.add_follow_up(subject_id=sid, text="No due", owner="C")

    follow_ups = db.list_follow_ups(subject_id=sid)
    texts = [f.text for f in follow_ups]
    assert texts.index("Sooner") < texts.index("Later")
    assert texts.index("Later") < texts.index("No due")


# ---------------------------------------------------------------------------
# update_follow_up_status
# ---------------------------------------------------------------------------

def test_update_follow_up_status_to_overdue(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Now overdue", owner="A")
    db.update_follow_up_status(fid, "overdue")
    fu = db.get_follow_up(fid)
    assert fu.status == "overdue"


def test_update_follow_up_status_to_received(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Got reply", owner="A")
    db.update_follow_up_status(fid, "received")
    fu = db.get_follow_up(fid)
    assert fu.status == "received"


def test_update_follow_up_status_to_cancelled(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Cancelled", owner="A")
    db.update_follow_up_status(fid, "cancelled")
    fu = db.get_follow_up(fid)
    assert fu.status == "cancelled"


# ---------------------------------------------------------------------------
# update_follow_up_notes
# ---------------------------------------------------------------------------

def test_update_follow_up_notes_sets_notes(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Add notes", owner="A")
    db.update_follow_up_notes(fid, "Some notes here")
    fu = db.get_follow_up(fid)
    assert fu.notes == "Some notes here"


def test_update_follow_up_notes_clears_notes(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Clear notes", owner="A")
    db.update_follow_up_notes(fid, "Initial notes")
    db.update_follow_up_notes(fid, None)
    fu = db.get_follow_up(fid)
    assert fu.notes is None


# ---------------------------------------------------------------------------
# update_follow_up
# ---------------------------------------------------------------------------

def test_update_follow_up_updates_text(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Old text", owner="Alice")
    db.update_follow_up(fid, text="New text", owner="Alice", due_by=None)
    fu = db.get_follow_up(fid)
    assert fu.text == "New text"


def test_update_follow_up_updates_owner(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Some task", owner="Old Owner")
    db.update_follow_up(fid, text="Some task", owner="New Owner", due_by=None)
    fu = db.get_follow_up(fid)
    assert fu.owner == "New Owner"


def test_update_follow_up_updates_due_by(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Task", owner="Alice", due_by="2026-04-01")
    db.update_follow_up(fid, text="Task", owner="Alice", due_by="2026-05-01")
    fu = db.get_follow_up(fid)
    assert fu.due_by == "2026-05-01"


def test_update_follow_up_clears_due_by(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Task", owner="Alice", due_by="2026-04-01")
    db.update_follow_up(fid, text="Task", owner="Alice", due_by=None)
    fu = db.get_follow_up(fid)
    assert fu.due_by is None


def test_update_follow_up_all_fields(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Old", owner="Alice", due_by="2026-04-01")
    db.update_follow_up(fid, text="New text", owner="Bob", due_by="2026-06-01")
    fu = db.get_follow_up(fid)
    assert fu.text == "New text"
    assert fu.owner == "Bob"
    assert fu.due_by == "2026-06-01"


# ---------------------------------------------------------------------------
# soft_delete_follow_up
# ---------------------------------------------------------------------------

def test_soft_delete_follow_up_sets_deleted_at(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Delete me", owner="A")
    db.soft_delete_follow_up(fid)
    row = db.conn.execute(
        "SELECT deleted_at FROM follow_ups WHERE id = ?", (fid,)
    ).fetchone()
    assert row["deleted_at"] is not None


def test_soft_delete_follow_up_excludes_from_list(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Gone", owner="A")
    db.soft_delete_follow_up(fid)
    follow_ups = db.list_follow_ups(subject_id=sid)
    assert all(f.id != fid for f in follow_ups)


# ---------------------------------------------------------------------------
# comment round-trip
# ---------------------------------------------------------------------------

def test_add_follow_up_with_comment(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="With comment", owner="Alice", comment="Note about this")
    fu = db.get_follow_up(fid)
    assert fu is not None
    assert fu.comment == "Note about this"


def test_add_follow_up_without_comment_defaults_to_none(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="No comment", owner="Bob")
    fu = db.get_follow_up(fid)
    assert fu is not None
    assert fu.comment is None


def test_update_follow_up_comment(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Will get comment", owner="Carol")
    db.update_follow_up_comment(fid, "Added later")
    fu = db.get_follow_up(fid)
    assert fu.comment == "Added later"


def test_update_follow_up_comment_to_none(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Remove comment", owner="Dave", comment="Remove me")
    db.update_follow_up_comment(fid, None)
    fu = db.get_follow_up(fid)
    assert fu.comment is None
