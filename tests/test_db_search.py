"""Tests for Database.search() method."""

from __future__ import annotations

import pytest

from tracker.db import Database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _subject(db: Database, name: str = "My Project") -> str:
    return db.add_subject(name=name)


# ---------------------------------------------------------------------------
# Finds subjects
# ---------------------------------------------------------------------------

def test_search_finds_subject_by_name(db: Database) -> None:
    sid = _subject(db, "Alpha Project")
    results = db.search("Alpha")
    assert any(r["type"] == "subject" and r["id"] == sid for r in results)


def test_search_subject_result_has_correct_keys(db: Database) -> None:
    sid = _subject(db, "Beta")
    results = db.search("Beta")
    result = next(r for r in results if r["type"] == "subject")
    assert "type" in result
    assert "id" in result
    assert "match_text" in result
    assert "subject_id" in result
    assert result["id"] == result["subject_id"]


# ---------------------------------------------------------------------------
# Finds tasks
# ---------------------------------------------------------------------------

def test_search_finds_task_by_text(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Implement search feature")
    results = db.search("search feature")
    assert any(r["type"] == "task" and r["id"] == tid for r in results)


def test_search_task_result_has_subject_id(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Unique task text xyz")
    results = db.search("Unique task text xyz")
    result = next(r for r in results if r["type"] == "task")
    assert result["subject_id"] == sid


# ---------------------------------------------------------------------------
# Finds notes
# ---------------------------------------------------------------------------

def test_search_finds_note_by_content(db: Database) -> None:
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Meeting notes from yesterday")
    results = db.search("Meeting notes")
    assert any(r["type"] == "note" and r["id"] == nid for r in results)


# ---------------------------------------------------------------------------
# Finds open points
# ---------------------------------------------------------------------------

def test_search_finds_open_point_by_text(db: Database) -> None:
    sid = _subject(db)
    pid = db.add_open_point(subject_id=sid, text="Why is the budget over limit?")
    results = db.search("budget over")
    assert any(r["type"] == "open_point" and r["id"] == pid for r in results)


# ---------------------------------------------------------------------------
# Finds follow-ups
# ---------------------------------------------------------------------------

def test_search_finds_follow_up_by_text(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Review contract renewal", owner="Alice")
    results = db.search("contract renewal")
    assert any(r["type"] == "follow_up" and r["id"] == fid for r in results)


def test_search_finds_follow_up_by_owner(db: Database) -> None:
    sid = _subject(db)
    fid = db.add_follow_up(subject_id=sid, text="Pending decision", owner="BobSmith")
    results = db.search("BobSmith")
    assert any(r["type"] == "follow_up" and r["id"] == fid for r in results)


# ---------------------------------------------------------------------------
# Excludes soft-deleted
# ---------------------------------------------------------------------------

def test_search_excludes_soft_deleted_task(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Deleted unique task zzz")
    db.soft_delete_task(tid)
    results = db.search("Deleted unique task zzz")
    assert not any(r["type"] == "task" and r["id"] == tid for r in results)


def test_search_excludes_soft_deleted_note(db: Database) -> None:
    sid = _subject(db)
    nid = db.add_note(subject_id=sid, content="Deleted note content zzz")
    db.soft_delete_note(nid)
    results = db.search("Deleted note content zzz")
    assert not any(r["type"] == "note" and r["id"] == nid for r in results)


def test_search_excludes_soft_deleted_subject(db: Database) -> None:
    sid = _subject(db, "SoftDeletedProject")
    db.soft_delete_subject(sid)
    results = db.search("SoftDeletedProject")
    assert not any(r["type"] == "subject" and r["id"] == sid for r in results)


# ---------------------------------------------------------------------------
# Case-insensitive
# ---------------------------------------------------------------------------

def test_search_is_case_insensitive_subject(db: Database) -> None:
    sid = _subject(db, "CaseSensitiveTest")
    results = db.search("casesensitivetest")
    assert any(r["type"] == "subject" and r["id"] == sid for r in results)


def test_search_is_case_insensitive_task(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="UpperCaseTask")
    results = db.search("uppercasetask")
    assert any(r["type"] == "task" and r["id"] == tid for r in results)


# ---------------------------------------------------------------------------
# Max results
# ---------------------------------------------------------------------------

def test_search_returns_max_20_results(db: Database) -> None:
    sid = _subject(db)
    for i in range(25):
        db.add_task(subject_id=sid, text=f"Searchable task number {i}")
    results = db.search("Searchable task number")
    assert len(results) <= 20


# ---------------------------------------------------------------------------
# No results
# ---------------------------------------------------------------------------

def test_search_returns_empty_list_when_no_match(db: Database) -> None:
    _subject(db, "Nothing matches")
    results = db.search("xyzzy_no_match_here")
    assert results == []
