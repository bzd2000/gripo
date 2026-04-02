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


def test_update_task_changes_priority(db: Database) -> None:
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


# ---------------------------------------------------------------------------
# list_today_tasks
# ---------------------------------------------------------------------------

def test_list_today_tasks_returns_today_flagged_tasks(db: Database) -> None:
    sid = _subject(db)
    tid = db.add_task(subject_id=sid, text="Today task", today=True)
    db.add_task(subject_id=sid, text="Not today task", today=False)

    tasks = db.list_today_tasks()
    assert len(tasks) == 1
    assert tasks[0].id == tid
    assert tasks[0].text == "Today task"


def test_list_today_tasks_excludes_done(db: Database) -> None:
    sid = _subject(db)
    db.add_task(subject_id=sid, text="Done today", today=True, status="done")
    tid = db.add_task(subject_id=sid, text="Active today", today=True)

    tasks = db.list_today_tasks()
    ids = [t.id for t in tasks]
    assert tid in ids
    assert not any(t.text == "Done today" for t in tasks)


def test_list_today_tasks_excludes_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    tid_active = db.add_task(subject_id=sid, text="Active", today=True)
    tid_deleted = db.add_task(subject_id=sid, text="Deleted", today=True)
    db.soft_delete_task(tid_deleted)

    tasks = db.list_today_tasks()
    ids = [t.id for t in tasks]
    assert tid_active in ids
    assert tid_deleted not in ids


def test_list_today_tasks_excludes_soft_deleted_subject(db: Database) -> None:
    sid_active = _subject(db, "Active Subject")
    sid_deleted = _subject(db, "Deleted Subject")
    db.add_task(subject_id=sid_active, text="Active subject task", today=True)
    db.add_task(subject_id=sid_deleted, text="Deleted subject task", today=True)
    db.soft_delete_subject(sid_deleted)

    tasks = db.list_today_tasks()
    assert len(tasks) == 1
    assert tasks[0].text == "Active subject task"


def test_list_today_tasks_ordered_by_priority(db: Database) -> None:
    sid = _subject(db)
    db.add_task(subject_id=sid, text="If-time task", today=True, priority="if-time")
    db.add_task(subject_id=sid, text="Should task", today=True, priority="should")
    db.add_task(subject_id=sid, text="Must task", today=True, priority="must")

    tasks = db.list_today_tasks()
    assert tasks[0].text == "Must task"
    assert tasks[1].text == "Should task"
    assert tasks[2].text == "If-time task"


def test_list_today_tasks_includes_subject_name(db: Database) -> None:
    sid = _subject(db, "My Project")
    db.add_task(subject_id=sid, text="A task", today=True)

    tasks = db.list_today_tasks()
    assert len(tasks) == 1
    assert tasks[0].subject_name == "My Project"


def test_list_today_tasks_crosses_subjects(db: Database) -> None:
    sid1 = _subject(db, "Subject 1")
    sid2 = _subject(db, "Subject 2")
    db.add_task(subject_id=sid1, text="Task from S1", today=True)
    db.add_task(subject_id=sid2, text="Task from S2", today=True)

    tasks = db.list_today_tasks()
    texts = [t.text for t in tasks]
    assert "Task from S1" in texts
    assert "Task from S2" in texts


# ---------------------------------------------------------------------------
# today_counts
# ---------------------------------------------------------------------------

def test_today_counts_returns_zero_when_no_today_tasks(db: Database) -> None:
    sid = _subject(db)
    db.add_task(subject_id=sid, text="Not today")

    total, done, blocked = db.today_counts()
    assert total == 0
    assert done == 0
    assert blocked == 0


def test_today_counts_total_includes_done(db: Database) -> None:
    sid = _subject(db)
    db.add_task(subject_id=sid, text="Active", today=True)
    db.add_task(subject_id=sid, text="Done task", today=True, status="done")

    total, done, blocked = db.today_counts()
    assert total == 2
    assert done == 1
    assert blocked == 0


def test_today_counts_blocked(db: Database) -> None:
    sid = _subject(db)
    db.add_task(subject_id=sid, text="Blocked task", today=True, status="blocked")
    db.add_task(subject_id=sid, text="Active task", today=True)

    total, done, blocked = db.today_counts()
    assert total == 2
    assert done == 0
    assert blocked == 1


def test_today_counts_excludes_soft_deleted(db: Database) -> None:
    sid = _subject(db)
    db.add_task(subject_id=sid, text="Active", today=True)
    tid = db.add_task(subject_id=sid, text="Deleted", today=True)
    db.soft_delete_task(tid)

    total, done, blocked = db.today_counts()
    assert total == 1
