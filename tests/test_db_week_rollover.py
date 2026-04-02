"""Tests for Database.perform_week_rollover() method."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from tracker.db import Database


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _subject(db: Database, name: str = "Sub") -> str:
    return db.add_subject(name=name)


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _set_week_of(db: Database, week_of: str) -> None:
    db.conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES ('week_of', ?)", (week_of,)
    )
    db.conn.commit()


def _get_week_of(db: Database) -> str | None:
    row = db.conn.execute("SELECT value FROM meta WHERE key = 'week_of'").fetchone()
    return row["value"] if row else None


# ---------------------------------------------------------------------------
# Clears today flags
# ---------------------------------------------------------------------------

def test_rollover_clears_today_flags(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Today task", today=True)
    db.perform_week_rollover(force=True)
    task = db.get_task(tid)
    assert task.today is False


def test_rollover_clears_today_flag_on_all_tasks(db: Database) -> None:
    sid = _subject(db)
    ids = [db.add_task(subject_id=sid, text=f"Task {i}", today=True) for i in range(5)]
    db.perform_week_rollover(force=True)
    for tid in ids:
        assert db.get_task(tid).today is False


# ---------------------------------------------------------------------------
# Clears day assignments on non-done tasks
# ---------------------------------------------------------------------------

def test_rollover_clears_day_on_non_done_tasks(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Monday task", day="mon")
    db.perform_week_rollover(force=True)
    task = db.get_task(tid)
    assert task.day is None


def test_rollover_clears_day_on_in_progress_tasks(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="In-progress task", day="wed", status="in-progress")
    db.perform_week_rollover(force=True)
    task = db.get_task(tid)
    assert task.day is None


# ---------------------------------------------------------------------------
# Preserves done task day assignments
# ---------------------------------------------------------------------------

def test_rollover_preserves_done_task_day(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Done task", day="fri", status="done")
    db.perform_week_rollover(force=True)
    task = db.get_task(tid)
    assert task.day == "fri"


# ---------------------------------------------------------------------------
# Soft-deletes done tasks older than 14 days
# ---------------------------------------------------------------------------

def test_rollover_soft_deletes_old_done_tasks(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Old done task", status="done")
    old_date = (date.today() - timedelta(days=15)).isoformat() + "T00:00:00+00:00"
    db.conn.execute("UPDATE tasks SET completed_at = ? WHERE id = ?", (old_date, tid))
    db.conn.commit()
    db.perform_week_rollover(force=True)
    row = db.conn.execute("SELECT deleted_at FROM tasks WHERE id = ?", (tid,)).fetchone()
    assert row["deleted_at"] is not None


def test_rollover_keeps_recent_done_tasks(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Recent done task", status="done")
    recent_date = (date.today() - timedelta(days=3)).isoformat() + "T00:00:00+00:00"
    db.conn.execute("UPDATE tasks SET completed_at = ? WHERE id = ?", (recent_date, tid))
    db.conn.commit()
    db.perform_week_rollover(force=True)
    row = db.conn.execute("SELECT deleted_at FROM tasks WHERE id = ?", (tid,)).fetchone()
    assert row["deleted_at"] is None


def test_rollover_keeps_done_task_without_completed_at(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Done no completed_at", status="done")
    # completed_at is NULL — should not be deleted
    db.perform_week_rollover(force=True)
    row = db.conn.execute("SELECT deleted_at FROM tasks WHERE id = ?", (tid,)).fetchone()
    assert row["deleted_at"] is None


# ---------------------------------------------------------------------------
# Updates meta.week_of to current Monday
# ---------------------------------------------------------------------------

def test_rollover_sets_week_of_to_current_monday(db: Database) -> None:
    db.perform_week_rollover(force=True)
    week_of = _get_week_of(db)
    expected = _monday_of(date.today()).isoformat()
    assert week_of == expected


# ---------------------------------------------------------------------------
# Skips if same week (no force)
# ---------------------------------------------------------------------------

def test_rollover_skips_if_same_week(db: Database) -> None:
    current_monday = _monday_of(date.today()).isoformat()
    _set_week_of(db, current_monday)
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Monday task keep", day="mon", today=True)
    result = db.perform_week_rollover(force=False)
    assert result is False
    task = db.get_task(tid)
    # day and today should be unchanged
    assert task.day == "mon"
    assert task.today is True


def test_rollover_runs_if_different_week(db: Database) -> None:
    old_monday = (_monday_of(date.today()) - timedelta(weeks=1)).isoformat()
    _set_week_of(db, old_monday)
    result = db.perform_week_rollover(force=False)
    assert result is True


def test_rollover_runs_if_no_week_of_in_meta(db: Database) -> None:
    # Fresh DB has no meta entry
    result = db.perform_week_rollover(force=False)
    assert result is True


def test_rollover_with_force_runs_even_same_week(db: Database) -> None:
    current_monday = _monday_of(date.today()).isoformat()
    _set_week_of(db, current_monday)
    result = db.perform_week_rollover(force=True)
    assert result is True


# ---------------------------------------------------------------------------
# Return value
# ---------------------------------------------------------------------------

def test_rollover_returns_true_when_executed(db: Database) -> None:
    result = db.perform_week_rollover(force=True)
    assert result is True
