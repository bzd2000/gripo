"""Tests for Database schema and subject CRUD methods."""

import pytest

from tracker.db import Database
from tracker.models import Subject


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def test_schema_creates_all_tables(db: Database) -> None:
    """All 6 tables should exist after schema init."""
    tables = {
        row[0]
        for row in db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert {"subjects", "tasks", "open_points", "follow_ups", "notes", "meta"} <= tables


# ---------------------------------------------------------------------------
# add_subject / get_subject
# ---------------------------------------------------------------------------

def test_add_subject_returns_id(db: Database) -> None:
    subject_id = db.add_subject(name="Alpha")
    assert isinstance(subject_id, str)
    assert len(subject_id) == 32  # uuid4().hex


def test_get_subject_returns_subject(db: Database) -> None:
    subject_id = db.add_subject(name="Beta", color="#ff0000")
    subject = db.get_subject(subject_id)
    assert subject is not None
    assert subject.id == subject_id
    assert subject.name == "Beta"
    assert subject.color == "#ff0000"
    assert subject.pinned is False
    assert subject.archived is False
    assert subject.deleted_at is None


def test_get_subject_unknown_returns_none(db: Database) -> None:
    assert db.get_subject("nonexistent") is None


# ---------------------------------------------------------------------------
# list_subjects
# ---------------------------------------------------------------------------

def test_list_subjects_excludes_archived_by_default(db: Database) -> None:
    db.add_subject(name="Active")
    archived_id = db.add_subject(name="Archived")
    db.toggle_archive(archived_id)

    subjects = db.list_subjects()
    names = [s.name for s in subjects]
    assert "Active" in names
    assert "Archived" not in names


def test_list_subjects_includes_archived_when_requested(db: Database) -> None:
    db.add_subject(name="Active")
    archived_id = db.add_subject(name="Archived")
    db.toggle_archive(archived_id)

    subjects = db.list_subjects(include_archived=True)
    names = [s.name for s in subjects]
    assert "Active" in names
    assert "Archived" in names


def test_list_subjects_excludes_soft_deleted(db: Database) -> None:
    db.add_subject(name="Visible")
    deleted_id = db.add_subject(name="Deleted")
    db.soft_delete_subject(deleted_id)

    subjects = db.list_subjects()
    names = [s.name for s in subjects]
    assert "Visible" in names
    assert "Deleted" not in names


def test_list_subjects_aggregate_fields(db: Database) -> None:
    """list_subjects should return aggregate counts."""
    subject_id = db.add_subject(name="WithData")
    db.add_task(subject_id=subject_id, text="Task one")
    db.add_task(subject_id=subject_id, text="Task two")
    db.add_note(subject_id=subject_id, content="A note")

    subjects = db.list_subjects()
    s = next(s for s in subjects if s.name == "WithData")
    assert s.open_tasks == 2
    assert s.latest_note is not None


# ---------------------------------------------------------------------------
# toggle_pin
# ---------------------------------------------------------------------------

def test_toggle_pin_pins_unpinned_subject(db: Database) -> None:
    subject_id = db.add_subject(name="Pinnable")
    db.toggle_pin(subject_id)
    subject = db.get_subject(subject_id)
    assert subject.pinned is True


def test_toggle_pin_unpins_pinned_subject(db: Database) -> None:
    subject_id = db.add_subject(name="WasPinned")
    db.toggle_pin(subject_id)
    db.toggle_pin(subject_id)
    subject = db.get_subject(subject_id)
    assert subject.pinned is False


def test_pinned_subjects_sort_first(db: Database) -> None:
    db.add_subject(name="Unpinned A")
    pinned_id = db.add_subject(name="Pinned B")
    db.toggle_pin(pinned_id)
    db.add_subject(name="Unpinned C")

    subjects = db.list_subjects()
    assert subjects[0].name == "Pinned B"


# ---------------------------------------------------------------------------
# archive_subject
# ---------------------------------------------------------------------------

def test_archive_subject_sets_archived_flag(db: Database) -> None:
    subject_id = db.add_subject(name="ToArchive")
    db.toggle_archive(subject_id)
    subject = db.get_subject(subject_id)
    assert subject.archived is True


def test_archived_subject_excluded_from_default_list(db: Database) -> None:
    subject_id = db.add_subject(name="ToArchive2")
    db.toggle_archive(subject_id)
    names = [s.name for s in db.list_subjects()]
    assert "ToArchive2" not in names


# ---------------------------------------------------------------------------
# soft_delete_subject (with cascade)
# ---------------------------------------------------------------------------

def test_soft_delete_subject_hides_from_get(db: Database) -> None:
    subject_id = db.add_subject(name="ToDelete")
    db.soft_delete_subject(subject_id)
    subject = db.get_subject(subject_id)
    assert subject is None


def test_soft_delete_cascades_to_tasks(db: Database) -> None:
    subject_id = db.add_subject(name="Parent")
    db.add_task(subject_id=subject_id, text="Child task")
    db.soft_delete_subject(subject_id)

    tasks = db.list_tasks(subject_id=subject_id)
    assert all(t.deleted_at is not None for t in tasks)


def test_soft_delete_cascades_to_notes(db: Database) -> None:
    subject_id = db.add_subject(name="ParentNotes")
    db.add_note(subject_id=subject_id, content="Child note")
    db.soft_delete_subject(subject_id)

    notes = db.list_notes(subject_id=subject_id)
    assert all(n.deleted_at is not None for n in notes)
