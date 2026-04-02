"""Tests for note CRUD methods in Database."""

from __future__ import annotations

import time

import pytest

from tracker.db import Database
from tracker.models import Note


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _subject(db: Database, name: str = "Sub") -> str:
    return db.add_subject(name=name)


# ---------------------------------------------------------------------------
# add_note
# ---------------------------------------------------------------------------

def test_add_note_returns_id(db: Database) -> None:
    sid = _subject(db)
    note_id = db.add_note(subject_id=sid, content="# Hello\nWorld")
    assert isinstance(note_id, str)
    assert len(note_id) == 32  # uuid4().hex


def test_add_note_stores_markdown_content(db: Database) -> None:
    sid = _subject(db)
    content = "# My Note\n\n- item 1\n- item 2\n\n**bold text**"
    note_id = db.add_note(subject_id=sid, content=content)
    note = db.get_note(note_id)
    assert note is not None
    assert note.content == content


def test_add_note_links_to_subject(db: Database) -> None:
    sid = _subject(db)
    note_id = db.add_note(subject_id=sid, content="Some note")
    note = db.get_note(note_id)
    assert note is not None
    assert note.subject_id == sid


def test_add_note_sets_created_at(db: Database) -> None:
    sid = _subject(db)
    note_id = db.add_note(subject_id=sid, content="Timestamped note")
    note = db.get_note(note_id)
    assert note is not None
    assert note.created_at is not None
    assert len(note.created_at) > 0


def test_add_note_sets_updated_at(db: Database) -> None:
    sid = _subject(db)
    note_id = db.add_note(subject_id=sid, content="Updated at note")
    note = db.get_note(note_id)
    assert note is not None
    assert note.updated_at is not None


def test_add_note_deleted_at_is_none(db: Database) -> None:
    sid = _subject(db)
    note_id = db.add_note(subject_id=sid, content="Active note")
    note = db.get_note(note_id)
    assert note is not None
    assert note.deleted_at is None


# ---------------------------------------------------------------------------
# get_note
# ---------------------------------------------------------------------------

def test_get_note_returns_none_for_unknown(db: Database) -> None:
    assert db.get_note("nonexistent") is None


def test_get_note_returns_correct_note(db: Database) -> None:
    sid = _subject(db)
    note_id = db.add_note(subject_id=sid, content="Fetch me")
    note = db.get_note(note_id)
    assert note is not None
    assert note.id == note_id
    assert note.content == "Fetch me"


# ---------------------------------------------------------------------------
# list_notes
# ---------------------------------------------------------------------------

def test_list_notes_returns_empty_for_no_notes(db: Database) -> None:
    sid = _subject(db)
    notes = db.list_notes(subject_id=sid)
    assert notes == []


def test_list_notes_excludes_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    db.add_note(subject_id=sid, content="Visible note")
    nid = db.add_note(subject_id=sid, content="Deleted note")
    db.soft_delete_note(nid)

    notes = db.list_notes(subject_id=sid)
    contents = [n.content for n in notes]
    assert "Visible note" in contents
    assert "Deleted note" not in contents


def test_list_notes_newest_first(db: Database) -> None:
    sid = _subject(db)
    nid1 = db.add_note(subject_id=sid, content="First note")
    nid2 = db.add_note(subject_id=sid, content="Second note")

    # Force different timestamps by updating created_at directly
    db.conn.execute(
        "UPDATE notes SET created_at = '2024-01-01 10:00:00' WHERE id = ?", (nid1,)
    )
    db.conn.execute(
        "UPDATE notes SET created_at = '2024-01-02 10:00:00' WHERE id = ?", (nid2,)
    )
    db.conn.commit()

    notes = db.list_notes(subject_id=sid)
    assert notes[0].content == "Second note"
    assert notes[1].content == "First note"


def test_list_notes_only_returns_notes_for_subject(db: Database) -> None:
    sid1 = _subject(db, "Sub1")
    sid2 = _subject(db, "Sub2")
    db.add_note(subject_id=sid1, content="Note A")
    db.add_note(subject_id=sid2, content="Note B")

    notes = db.list_notes(subject_id=sid1)
    assert len(notes) == 1
    assert notes[0].content == "Note A"


# ---------------------------------------------------------------------------
# update_note
# ---------------------------------------------------------------------------

def test_update_note_changes_content(db: Database) -> None:
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Old content")
    db.update_note(nid, content="New content")
    note = db.get_note(nid)
    assert note is not None
    assert note.content == "New content"


def test_update_note_updates_updated_at(db: Database) -> None:
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Original")

    # Set a known old updated_at
    db.conn.execute(
        "UPDATE notes SET updated_at = '2024-01-01 10:00:00' WHERE id = ?", (nid,)
    )
    db.conn.commit()

    old_note = db.get_note(nid)
    db.update_note(nid, content="Modified content")
    new_note = db.get_note(nid)

    assert new_note is not None
    assert new_note.updated_at != "2024-01-01 10:00:00"


def test_update_note_preserves_created_at(db: Database) -> None:
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Stable timestamps")
    note_before = db.get_note(nid)
    db.update_note(nid, content="Changed content")
    note_after = db.get_note(nid)
    assert note_after is not None
    assert note_after.created_at == note_before.created_at


# ---------------------------------------------------------------------------
# soft_delete_note
# ---------------------------------------------------------------------------

def test_soft_delete_note_sets_deleted_at(db: Database) -> None:
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Delete me")
    db.soft_delete_note(nid)
    row = db.conn.execute(
        "SELECT deleted_at FROM notes WHERE id = ?", (nid,)
    ).fetchone()
    assert row["deleted_at"] is not None


def test_soft_delete_note_excludes_from_list(db: Database) -> None:
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Gone")
    db.soft_delete_note(nid)
    notes = db.list_notes(subject_id=sid)
    assert all(n.id != nid for n in notes)


def test_soft_delete_note_note_still_fetchable_directly(db: Database) -> None:
    """get_note should still return the note after soft delete (no hard delete)."""
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Soft deleted note")
    db.soft_delete_note(nid)
    note = db.get_note(nid)
    assert note is not None
    assert note.deleted_at is not None
