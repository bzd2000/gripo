"""Tests for task CRUD methods in Database."""

from __future__ import annotations

import pytest

from tracker.db import Database
from tracker.models import Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _subject(db: Database, name: str = "Sub") -> str:
    return db.add_subject(name=name)


# ---------------------------------------------------------------------------
# add_task
# ---------------------------------------------------------------------------

def test_add_task_returns_id(db: Database) -> None:
    sid = _subject(db)
    task_id = db.add_task(subject_id=sid, text="Do something")
    assert isinstance(task_id, str)
    assert len(task_id) == 32  # uuid4().hex


def test_add_task_with_priority(db: Database) -> None:
    sid = _subject(db)
    task_id = db.add_task(subject_id=sid, text="Critical", priority="must")
    task = db.get_task(task_id)
    assert task is not None
    assert task.priority == "must"


def test_add_task_with_category(db: Database) -> None:
    sid = _subject(db)
    task_id = db.add_task(subject_id=sid, text="Deliver", category="delivery")
    task = db.get_task(task_id)
    assert task is not None
    assert task.category == "delivery"


def test_add_task_default_priority_is_should(db: Database) -> None:
    sid = _subject(db)
    task_id = db.add_task(subject_id=sid, text="Default prio")
    task = db.get_task(task_id)
    assert task.priority == "should"


def test_add_task_default_status_is_todo(db: Database) -> None:
    sid = _subject(db)
    task_id = db.add_task(subject_id=sid, text="New task")
    task = db.get_task(task_id)
    assert task.status == "todo"


# ---------------------------------------------------------------------------
# get_task
# ---------------------------------------------------------------------------

def test_get_task_returns_none_for_unknown(db: Database) -> None:
    assert db.get_task("nonexistent") is None


def test_get_task_returns_task(db: Database) -> None:
    sid = _subject(db)
    task_id = db.add_task(subject_id=sid, text="Fetch me")
    task = db.get_task(task_id)
    assert task is not None
    assert task.id == task_id
    assert task.text == "Fetch me"
    assert task.subject_id == sid


# ---------------------------------------------------------------------------
# list_tasks
# ---------------------------------------------------------------------------

def test_list_tasks_excludes_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    db.add_task(subject_id=sid, text="Visible")
    tid = db.add_task(subject_id=sid, text="Deleted")
    db.soft_delete_task(tid)

    tasks = db.list_tasks(subject_id=sid)
    texts = [t.text for t in tasks]
    assert "Visible" in texts
    assert "Deleted" not in texts


def test_list_tasks_ordered_by_status_then_priority(db: Database) -> None:
    """Tasks should be ordered: todo > in-progress > blocked > done, then must > should > if-time."""
    sid = _subject(db)
    db.add_task(subject_id=sid, text="Done task", status="done", priority="must")
    db.add_task(subject_id=sid, text="Todo should", status="todo", priority="should")
    db.add_task(subject_id=sid, text="Todo must", status="todo", priority="must")
    db.add_task(subject_id=sid, text="In-progress", status="in-progress", priority="should")
    db.add_task(subject_id=sid, text="Blocked", status="blocked", priority="should")

    tasks = db.list_tasks(subject_id=sid)
    # First two should be todo items, done last
    assert tasks[-1].text == "Done task"
    # Among todo, must before should
    todo_tasks = [t for t in tasks if t.status == "todo"]
    assert todo_tasks[0].text == "Todo must"
    assert todo_tasks[1].text == "Todo should"


def test_list_tasks_only_returns_tasks_for_subject(db: Database) -> None:
    sid1 = _subject(db, "Sub1")
    sid2 = _subject(db, "Sub2")
    db.add_task(subject_id=sid1, text="Task A")
    db.add_task(subject_id=sid2, text="Task B")

    tasks = db.list_tasks(subject_id=sid1)
    assert len(tasks) == 1
    assert tasks[0].text == "Task A"


# ---------------------------------------------------------------------------
# update_task_status
# ---------------------------------------------------------------------------

def test_update_task_status_sets_completed_at_when_done(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Finish me")
    db.update_task_status(tid, "done")
    task = db.get_task(tid)
    assert task.status == "done"
    assert task.completed_at is not None


def test_update_task_status_clears_completed_at_when_un_done(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Toggle me")
    db.update_task_status(tid, "done")
    db.update_task_status(tid, "todo")
    task = db.get_task(tid)
    assert task.status == "todo"
    assert task.completed_at is None


def test_update_task_status_in_progress_does_not_set_completed_at(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="In flight")
    db.update_task_status(tid, "in-progress")
    task = db.get_task(tid)
    assert task.status == "in-progress"
    assert task.completed_at is None


def test_update_task_status_blocked(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Blocked task")
    db.update_task_status(tid, "blocked")
    task = db.get_task(tid)
    assert task.status == "blocked"
    assert task.completed_at is None


# ---------------------------------------------------------------------------
# update_task_priority
# ---------------------------------------------------------------------------

def test_update_task_priority(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Bump me", priority="should")
    db.update_task_priority(tid, "must")
    task = db.get_task(tid)
    assert task.priority == "must"


# ---------------------------------------------------------------------------
# toggle_today
# ---------------------------------------------------------------------------

def test_toggle_today_sets_today_flag(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Today task")
    task = db.get_task(tid)
    assert task.today is False
    db.toggle_today(tid)
    task = db.get_task(tid)
    assert task.today is True


def test_toggle_today_clears_today_flag(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Was today")
    db.toggle_today(tid)
    db.toggle_today(tid)
    task = db.get_task(tid)
    assert task.today is False


# ---------------------------------------------------------------------------
# update_task_day
# ---------------------------------------------------------------------------

def test_update_task_day_sets_day(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Monday task")
    db.update_task_day(tid, "mon")
    task = db.get_task(tid)
    assert task.day == "mon"


def test_update_task_day_sets_to_none(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Clear day")
    db.update_task_day(tid, "fri")
    db.update_task_day(tid, None)
    task = db.get_task(tid)
    assert task.day is None


def test_update_task_day_anytime(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Anytime task")
    db.update_task_day(tid, "anytime")
    task = db.get_task(tid)
    assert task.day == "anytime"


# ---------------------------------------------------------------------------
# update_task (text, priority, category)
# ---------------------------------------------------------------------------

def test_update_task_text(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Old text")
    db.update_task(tid, text="New text")
    task = db.get_task(tid)
    assert task.text == "New text"


def test_update_task_priority(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Reprioritize", priority="should")
    db.update_task(tid, priority="if-time")
    task = db.get_task(tid)
    assert task.priority == "if-time"


def test_update_task_category(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Recategorize", category="admin")
    db.update_task(tid, category="people")
    task = db.get_task(tid)
    assert task.category == "people"


def test_update_task_multiple_fields(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Multi update", priority="must", category="admin")
    db.update_task(tid, text="Updated text", priority="if-time", category="meeting")
    task = db.get_task(tid)
    assert task.text == "Updated text"
    assert task.priority == "if-time"
    assert task.category == "meeting"


# ---------------------------------------------------------------------------
# soft_delete_task
# ---------------------------------------------------------------------------

def test_soft_delete_task_sets_deleted_at(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Delete me")
    db.soft_delete_task(tid)
    # Must fetch directly since list_tasks excludes deleted
    row = db.conn.execute("SELECT deleted_at FROM tasks WHERE id = ?", (tid,)).fetchone()
    assert row["deleted_at"] is not None


def test_soft_delete_task_excludes_from_list(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Gone")
    db.soft_delete_task(tid)
    tasks = db.list_tasks(subject_id=sid)
    assert all(t.id != tid for t in tasks)
