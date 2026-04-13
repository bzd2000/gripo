"""Database class — schema init and all SQL queries."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Union

from tracker.models import FollowUp, Milestone, Note, OpenPoint, Subject, Task

SENTINEL = object()

_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS subjects (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    subject_type  TEXT CHECK (subject_type IN ('person', 'team', 'board', 'project')),
    pinned        INTEGER NOT NULL DEFAULT 0,
    archived      INTEGER NOT NULL DEFAULT 0,
    color         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    text          TEXT NOT NULL,
    priority      TEXT NOT NULL DEFAULT 'should' CHECK (priority IN ('must', 'should', 'if-time')),
    status        TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in-progress', 'done', 'blocked')),
    category      TEXT CHECK (category IN ('delivery', 'admin', 'people', 'strategy', 'meeting', 'other')),
    day           TEXT CHECK (day IN ('mon', 'tue', 'wed', 'thu', 'fri', 'anytime')),
    today         INTEGER NOT NULL DEFAULT 0,
    due_date      TEXT,
    comment       TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at  TEXT,
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS open_points (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    text          TEXT NOT NULL,
    context       TEXT,
    status        TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'parked')),
    resolved_note TEXT,
    comment       TEXT,
    raised_at     TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at   TEXT,
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS follow_ups (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    text          TEXT NOT NULL,
    owner         TEXT NOT NULL,
    asked_on      TEXT NOT NULL DEFAULT (date('now')),
    due_by        TEXT,
    status        TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'received', 'overdue', 'cancelled')),
    notes         TEXT,
    comment       TEXT,
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    title         TEXT NOT NULL DEFAULT '',
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS milestones (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
    name          TEXT NOT NULL,
    target_date   TEXT,
    lead_weeks    INTEGER,
    status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    comment       TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at  TEXT,
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS meta (
    key           TEXT PRIMARY KEY,
    value         TEXT NOT NULL
);
"""


def _new_id() -> str:
    return uuid.uuid4().hex


class Database:
    """Wrapper around sqlite3 providing all app CRUD operations."""

    def __init__(self, path: Union[Path, str] = ":memory:") -> None:
        if path != ":memory:":
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            db_path = str(p)
        else:
            db_path = ":memory:"

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        # Apply pragmas and schema
        self.conn.executescript(_SCHEMA)
        self._migrate()
        self.conn.commit()

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()

    def _migrate(self) -> None:
        """Run forward-only migrations for schema changes."""
        # Add due_date column to tasks if missing
        cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "due_date" not in cols:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
        if "comment" not in cols:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN comment TEXT")

        # Add comment column to open_points if missing
        op_cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(open_points)").fetchall()]
        if "comment" not in op_cols:
            self.conn.execute("ALTER TABLE open_points ADD COLUMN comment TEXT")

        # Add comment column to follow_ups if missing
        fu_cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(follow_ups)").fetchall()]
        if "comment" not in fu_cols:
            self.conn.execute("ALTER TABLE follow_ups ADD COLUMN comment TEXT")

        # Add milestone_id to tasks and follow_ups if missing
        if "milestone_id" not in cols:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN milestone_id TEXT REFERENCES milestones(id) ON DELETE SET NULL")
        if "milestone_id" not in fu_cols:
            self.conn.execute("ALTER TABLE follow_ups ADD COLUMN milestone_id TEXT REFERENCES milestones(id) ON DELETE SET NULL")

        # Add lead_weeks to milestones if missing
        ms_cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(milestones)").fetchall()]
        if ms_cols and "lead_weeks" not in ms_cols:
            self.conn.execute("ALTER TABLE milestones ADD COLUMN lead_weeks INTEGER")

        # Add subject_type to subjects if missing
        subj_cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(subjects)").fetchall()]
        if "subject_type" not in subj_cols:
            self.conn.execute("ALTER TABLE subjects ADD COLUMN subject_type TEXT CHECK (subject_type IN ('person', 'team', 'board', 'project'))")

        # Add title to notes if missing
        note_cols = [r["name"] for r in self.conn.execute("PRAGMA table_info(notes)").fetchall()]
        if note_cols and "title" not in note_cols:
            self.conn.execute("ALTER TABLE notes ADD COLUMN title TEXT NOT NULL DEFAULT ''")

    # ------------------------------------------------------------------
    # Subject CRUD
    # ------------------------------------------------------------------

    def add_subject(
        self,
        name: str,
        subject_type: Optional[str] = None,
        color: Optional[str] = None,
        pinned: bool = False,
    ) -> str:
        subject_id = _new_id()
        self.conn.execute(
            "INSERT INTO subjects (id, name, subject_type, color, pinned) VALUES (?, ?, ?, ?, ?)",
            (subject_id, name, subject_type, color, int(pinned)),
        )
        self.conn.commit()
        return subject_id

    def get_subject(self, subject_id: str) -> Optional[Subject]:
        row = self.conn.execute(
            "SELECT * FROM subjects WHERE id = ? AND deleted_at IS NULL", (subject_id,)
        ).fetchone()
        return Subject.from_row(row) if row else None

    def list_subjects(self, include_archived: bool = False) -> List[Subject]:
        """Return subjects with aggregate counts.

        By default excludes archived and soft-deleted subjects.
        Pinned subjects sort first, then by name.
        """
        archived_clause = "" if include_archived else "AND s.archived = 0"
        sql = f"""
            SELECT
                s.id,
                s.name,
                s.subject_type,
                s.pinned,
                s.archived,
                s.color,
                s.created_at,
                s.deleted_at,
                COUNT(DISTINCT CASE
                    WHEN t.deleted_at IS NULL AND t.status NOT IN ('done')
                    THEN t.id END) AS open_tasks,
                COUNT(DISTINCT CASE
                    WHEN op.deleted_at IS NULL AND op.status = 'open'
                    THEN op.id END) AS open_points_count,
                COUNT(DISTINCT CASE
                    WHEN fu.deleted_at IS NULL AND fu.status = 'waiting'
                    THEN fu.id END) AS follow_ups_count,
                MAX(CASE WHEN n.deleted_at IS NULL THEN n.created_at END) AS latest_note
            FROM subjects s
            LEFT JOIN tasks t ON t.subject_id = s.id
            LEFT JOIN open_points op ON op.subject_id = s.id
            LEFT JOIN follow_ups fu ON fu.subject_id = s.id
            LEFT JOIN notes n ON n.subject_id = s.id
            WHERE s.deleted_at IS NULL
            {archived_clause}
            GROUP BY s.id
            ORDER BY CASE s.subject_type WHEN 'person' THEN 0 WHEN 'team' THEN 1
                     WHEN 'project' THEN 2 WHEN 'board' THEN 3 ELSE 4 END,
                     s.pinned DESC, s.name ASC
        """
        rows = self.conn.execute(sql).fetchall()
        return [Subject.from_row(row) for row in rows]

    def update_subject(self, subject_id: str, name: str, subject_type: Optional[str] = None) -> None:
        self.conn.execute(
            "UPDATE subjects SET name = ?, subject_type = ? WHERE id = ?",
            (name, subject_type, subject_id),
        )
        self.conn.commit()

    def toggle_pin(self, subject_id: str) -> None:
        self.conn.execute(
            "UPDATE subjects SET pinned = CASE WHEN pinned = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (subject_id,),
        )
        self.conn.commit()

    def toggle_archive(self, subject_id: str) -> None:
        self.conn.execute(
            "UPDATE subjects SET archived = CASE WHEN archived = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (subject_id,),
        )
        self.conn.commit()

    def soft_delete_subject(self, subject_id: str) -> None:
        """Soft-delete a subject and all its child records in a single transaction."""
        now = datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.execute(
                "UPDATE subjects SET deleted_at = ? WHERE id = ?", (now, subject_id)
            )
            for table in ("tasks", "open_points", "follow_ups", "notes", "milestones"):
                self.conn.execute(
                    f"UPDATE {table} SET deleted_at = ? WHERE subject_id = ? AND deleted_at IS NULL",
                    (now, subject_id),
                )

    # ------------------------------------------------------------------
    # Task CRUD
    # ------------------------------------------------------------------

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def add_task(
        self,
        subject_id: str,
        text: str,
        priority: str = "should",
        status: str = "todo",
        category: Optional[str] = None,
        day: Optional[str] = None,
        today: bool = False,
        due_date: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> str:
        task_id = _new_id()
        self.conn.execute(
            """INSERT INTO tasks (id, subject_id, text, priority, status, category, day, today, due_date, comment)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, subject_id, text, priority, status, category, day, int(today), due_date, comment),
        )
        self.conn.commit()
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL", (task_id,)
        ).fetchone()
        return Task.from_row(row) if row else None

    def list_tasks(self, subject_id: str) -> List[Task]:
        """Return tasks for a subject, excluding soft-deleted.

        Ordered by status (todo first, done last) then priority (must first).
        """
        _STATUS_ORDER = "CASE status WHEN 'todo' THEN 0 WHEN 'in-progress' THEN 1 WHEN 'blocked' THEN 2 WHEN 'done' THEN 3 ELSE 4 END"
        _PRIORITY_ORDER = "CASE priority WHEN 'must' THEN 0 WHEN 'should' THEN 1 WHEN 'if-time' THEN 2 ELSE 3 END"
        sql = f"""
            SELECT * FROM tasks
            WHERE subject_id = ? AND deleted_at IS NULL
            ORDER BY {_STATUS_ORDER}, {_PRIORITY_ORDER}
        """
        rows = self.conn.execute(sql, (subject_id,)).fetchall()
        return [Task.from_row(row) for row in rows]

    def update_task_status(self, task_id: str, status: str) -> None:
        """Update task status, setting completed_at when done, clearing it otherwise."""
        completed_at = self._now() if status == "done" else None
        self.conn.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            (status, completed_at, task_id),
        )
        self.conn.commit()

    def update_task_priority(self, task_id: str, priority: str) -> None:
        self.conn.execute(
            "UPDATE tasks SET priority = ? WHERE id = ?",
            (priority, task_id),
        )
        self.conn.commit()

    def toggle_today(self, task_id: str) -> None:
        self.conn.execute(
            "UPDATE tasks SET today = CASE WHEN today = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (task_id,),
        )
        self.conn.commit()

    def update_task_day(self, task_id: str, day: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE tasks SET day = ? WHERE id = ?",
            (day, task_id),
        )
        self.conn.commit()

    def update_task_due_date(self, task_id: str, due_date: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE tasks SET due_date = ? WHERE id = ?",
            (due_date, task_id),
        )
        self.conn.commit()

    def update_task_comment(self, task_id: str, comment: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE tasks SET comment = ? WHERE id = ?",
            (comment, task_id),
        )
        self.conn.commit()

    def update_task(
        self,
        task_id: str,
        text: Optional[str] = None,
        priority: Optional[str] = None,
        category: object = SENTINEL,
        due_date: object = SENTINEL,
        comment: object = SENTINEL,
    ) -> None:
        """Update text, priority, category, due_date, and/or comment fields on a task."""
        fields: list[str] = []
        values: list = []
        if text is not None:
            fields.append("text = ?")
            values.append(text)
        if priority is not None:
            fields.append("priority = ?")
            values.append(priority)
        if category is not SENTINEL:
            fields.append("category = ?")
            values.append(category)
        if due_date is not SENTINEL:
            fields.append("due_date = ?")
            values.append(due_date)
        if comment is not SENTINEL:
            fields.append("comment = ?")
            values.append(comment)
        if not fields:
            return
        values.append(task_id)
        self.conn.execute(
            f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        self.conn.commit()

    def soft_delete_task(self, task_id: str) -> None:
        self.conn.execute(
            "UPDATE tasks SET deleted_at = ? WHERE id = ?",
            (self._now(), task_id),
        )
        self.conn.commit()

    def search(self, query: str) -> List[dict]:
        """Search across subjects, tasks, notes, open_points, follow_ups.

        Returns list of dicts with keys: type, id, match_text, subject_id.
        Case-insensitive LIKE match. Excludes soft-deleted records. Max 20 results.
        """
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        like = f"%{escaped}%"
        sql = """
            SELECT 'subject' AS type, id, name AS match_text, id AS subject_id
            FROM subjects
            WHERE name LIKE ? ESCAPE '\\' AND deleted_at IS NULL
            UNION ALL
            SELECT 'task' AS type, id, text AS match_text, subject_id
            FROM tasks
            WHERE text LIKE ? ESCAPE '\\' AND deleted_at IS NULL
            UNION ALL
            SELECT 'note' AS type, id, content AS match_text, subject_id
            FROM notes
            WHERE content LIKE ? ESCAPE '\\' AND deleted_at IS NULL
            UNION ALL
            SELECT 'open_point' AS type, id, text AS match_text, subject_id
            FROM open_points
            WHERE text LIKE ? ESCAPE '\\' AND deleted_at IS NULL
            UNION ALL
            SELECT 'follow_up' AS type, id, text AS match_text, subject_id
            FROM follow_ups
            WHERE (text LIKE ? ESCAPE '\\' OR owner LIKE ? ESCAPE '\\') AND deleted_at IS NULL
            UNION ALL
            SELECT 'milestone' AS type, id, name AS match_text, subject_id
            FROM milestones
            WHERE name LIKE ? ESCAPE '\\' AND deleted_at IS NULL
            LIMIT 20
        """
        rows = self.conn.execute(sql, (like, like, like, like, like, like, like)).fetchall()
        return [dict(row) for row in rows]

    def list_week_tasks(self) -> List[Task]:
        """Return week-relevant non-done tasks across all subjects."""
        today = date.today()
        monday = (today - timedelta(days=today.weekday())).isoformat()
        sunday = (today - timedelta(days=today.weekday()) + timedelta(days=6)).isoformat()
        sql = """
            SELECT t.*, s.name AS subject_name
            FROM tasks t JOIN subjects s ON t.subject_id = s.id
            WHERE (t.day IS NOT NULL
                   OR (t.due_date >= ? AND t.due_date <= ?))
            AND t.status != 'done'
            AND t.deleted_at IS NULL AND s.deleted_at IS NULL AND s.archived = 0
            ORDER BY COALESCE(t.due_date, '9999-12-31'),
                     CASE t.day WHEN 'mon' THEN 1 WHEN 'tue' THEN 2 WHEN 'wed' THEN 3
                                 WHEN 'thu' THEN 4 WHEN 'fri' THEN 5 ELSE 6 END,
                     CASE t.priority WHEN 'must' THEN 1 WHEN 'should' THEN 2 ELSE 3 END
        """
        rows = self.conn.execute(sql, (monday, sunday)).fetchall()
        return [Task.from_row(row) for row in rows]

    def list_today_tasks(self) -> List[Task]:
        """Return today-relevant non-done tasks across all subjects, ordered by priority."""
        today_str = date.today().isoformat()
        sql = """
            SELECT t.*, s.name AS subject_name
            FROM tasks t JOIN subjects s ON t.subject_id = s.id
            WHERE (t.today = 1 OR t.due_date <= ?)
            AND t.status != 'done'
            AND t.deleted_at IS NULL AND s.deleted_at IS NULL AND s.archived = 0
            ORDER BY CASE t.priority WHEN 'must' THEN 1 WHEN 'should' THEN 2 ELSE 3 END
        """
        rows = self.conn.execute(sql, (today_str,)).fetchall()
        return [Task.from_row(row) for row in rows]

    def today_counts(self) -> tuple[int, int, int]:
        """Return (total, done, blocked) counts for today-relevant tasks."""
        today_str = date.today().isoformat()
        sql = """
            SELECT COUNT(*) AS total,
              SUM(CASE WHEN t.status = 'done' THEN 1 ELSE 0 END) AS done,
              SUM(CASE WHEN t.status = 'blocked' THEN 1 ELSE 0 END) AS blocked
            FROM tasks t JOIN subjects s ON t.subject_id = s.id
            WHERE (t.today = 1 OR t.due_date <= ?)
            AND t.deleted_at IS NULL AND s.deleted_at IS NULL AND s.archived = 0
        """
        row = self.conn.execute(sql, (today_str,)).fetchone()
        total = row["total"] or 0
        done = row["done"] or 0
        blocked = row["blocked"] or 0
        return (total, done, blocked)

    # ------------------------------------------------------------------
    # Today / Week follow-up queries
    # ------------------------------------------------------------------

    def list_today_follow_ups(self) -> List["FollowUp"]:
        """Return follow-ups due today or overdue, with waiting/overdue status."""
        today_str = date.today().isoformat()
        sql = """
            SELECT f.*, s.name AS subject_name
            FROM follow_ups f JOIN subjects s ON f.subject_id = s.id
            WHERE f.due_by <= ?
            AND f.status IN ('waiting', 'overdue')
            AND f.deleted_at IS NULL AND s.deleted_at IS NULL AND s.archived = 0
            ORDER BY f.due_by ASC
        """
        rows = self.conn.execute(sql, (today_str,)).fetchall()
        return [FollowUp.from_row(row) for row in rows]

    def list_week_follow_ups(self) -> List["FollowUp"]:
        """Return follow-ups due this week (Mon-Sun), with waiting/overdue status."""
        today = date.today()
        monday = (today - timedelta(days=today.weekday())).isoformat()
        sunday = (today - timedelta(days=today.weekday()) + timedelta(days=6)).isoformat()
        sql = """
            SELECT f.*, s.name AS subject_name
            FROM follow_ups f JOIN subjects s ON f.subject_id = s.id
            WHERE f.due_by >= ? AND f.due_by <= ?
            AND f.status IN ('waiting', 'overdue')
            AND f.deleted_at IS NULL AND s.deleted_at IS NULL AND s.archived = 0
            ORDER BY f.due_by ASC
        """
        rows = self.conn.execute(sql, (monday, sunday)).fetchall()
        return [FollowUp.from_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Note CRUD
    # ------------------------------------------------------------------

    def add_note(self, subject_id: str, content: str, title: str = "") -> str:
        note_id = _new_id()
        self.conn.execute(
            "INSERT INTO notes (id, subject_id, title, content) VALUES (?, ?, ?, ?)",
            (note_id, subject_id, title, content),
        )
        self.conn.commit()
        return note_id

    def get_note(self, note_id: str) -> Optional[Note]:
        row = self.conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return Note.from_row(row) if row else None

    def list_notes(self, subject_id: str) -> List[Note]:
        """Return notes for a subject, excluding soft-deleted, newest first."""
        rows = self.conn.execute(
            "SELECT * FROM notes WHERE subject_id = ? AND deleted_at IS NULL ORDER BY created_at DESC",
            (subject_id,),
        ).fetchall()
        return [Note.from_row(row) for row in rows]

    def update_note(self, note_id: str, content: str, title: str = "") -> None:
        """Update note title, content and set updated_at to now."""
        self.conn.execute(
            "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
            (title, content, self._now(), note_id),
        )
        self.conn.commit()

    def soft_delete_note(self, note_id: str) -> None:
        self.conn.execute(
            "UPDATE notes SET deleted_at = ? WHERE id = ?",
            (self._now(), note_id),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Milestone CRUD
    # ------------------------------------------------------------------

    def add_milestone(
        self,
        subject_id: str,
        name: str,
        target_date: Optional[str] = None,
        lead_weeks: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> str:
        milestone_id = _new_id()
        self.conn.execute(
            "INSERT INTO milestones (id, subject_id, name, target_date, lead_weeks, comment) VALUES (?, ?, ?, ?, ?, ?)",
            (milestone_id, subject_id, name, target_date, lead_weeks, comment),
        )
        self.conn.commit()
        return milestone_id

    def get_milestone(self, milestone_id: str) -> Optional[Milestone]:
        row = self.conn.execute(
            "SELECT * FROM milestones WHERE id = ? AND deleted_at IS NULL", (milestone_id,)
        ).fetchone()
        return Milestone.from_row(row) if row else None

    def list_milestones(self, subject_id: str) -> List[Milestone]:
        rows = self.conn.execute(
            """SELECT * FROM milestones WHERE subject_id = ? AND deleted_at IS NULL
               ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'completed' THEN 1 ELSE 2 END,
                        target_date ASC NULLS LAST""",
            (subject_id,),
        ).fetchall()
        return [Milestone.from_row(row) for row in rows]

    def update_milestone(
        self,
        milestone_id: str,
        name: str = SENTINEL,
        target_date: str = SENTINEL,
        lead_weeks: int = SENTINEL,
        comment: str = SENTINEL,
    ) -> None:
        updates = []
        params = []
        if name is not SENTINEL:
            updates.append("name = ?")
            params.append(name)
        if target_date is not SENTINEL:
            updates.append("target_date = ?")
            params.append(target_date)
        if lead_weeks is not SENTINEL:
            updates.append("lead_weeks = ?")
            params.append(lead_weeks)
        if comment is not SENTINEL:
            updates.append("comment = ?")
            params.append(comment)
        if updates:
            params.append(milestone_id)
            self.conn.execute(
                f"UPDATE milestones SET {', '.join(updates)} WHERE id = ?", params
            )
            self.conn.commit()

    def update_milestone_status(self, milestone_id: str, status: str) -> None:
        completed_at = self._now() if status == "completed" else None
        self.conn.execute(
            "UPDATE milestones SET status = ?, completed_at = ? WHERE id = ?",
            (status, completed_at, milestone_id),
        )
        self.conn.commit()

    def soft_delete_milestone(self, milestone_id: str) -> None:
        now = self._now()
        with self.conn:
            self.conn.execute(
                "UPDATE milestones SET deleted_at = ? WHERE id = ?", (now, milestone_id)
            )
            self.conn.execute(
                "UPDATE tasks SET milestone_id = NULL WHERE milestone_id = ?", (milestone_id,)
            )
            self.conn.execute(
                "UPDATE follow_ups SET milestone_id = NULL WHERE milestone_id = ?", (milestone_id,)
            )

    def link_task_to_milestone(self, task_id: str, milestone_id: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE tasks SET milestone_id = ? WHERE id = ?", (milestone_id, task_id)
        )
        self.conn.commit()

    def link_follow_up_to_milestone(self, follow_up_id: str, milestone_id: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE follow_ups SET milestone_id = ? WHERE id = ?", (milestone_id, follow_up_id)
        )
        self.conn.commit()

    def list_milestone_tasks(self, milestone_id: str) -> List[Task]:
        rows = self.conn.execute(
            """SELECT * FROM tasks WHERE milestone_id = ? AND deleted_at IS NULL
               ORDER BY CASE status WHEN 'todo' THEN 0 WHEN 'in-progress' THEN 1
                        WHEN 'blocked' THEN 2 ELSE 3 END,
                        CASE priority WHEN 'must' THEN 0 WHEN 'should' THEN 1 ELSE 2 END""",
            (milestone_id,),
        ).fetchall()
        return [Task.from_row(row) for row in rows]

    def list_milestone_follow_ups(self, milestone_id: str) -> List[FollowUp]:
        rows = self.conn.execute(
            """SELECT * FROM follow_ups WHERE milestone_id = ? AND deleted_at IS NULL
               ORDER BY CASE status WHEN 'waiting' THEN 0 WHEN 'overdue' THEN 1 ELSE 2 END,
                        due_by ASC NULLS LAST""",
            (milestone_id,),
        ).fetchall()
        return [FollowUp.from_row(row) for row in rows]

    def list_all_active_milestones(self) -> List[Milestone]:
        """Return all active milestones with target_date across all subjects."""
        rows = self.conn.execute(
            """SELECT m.*, s.name AS subject_name
               FROM milestones m JOIN subjects s ON m.subject_id = s.id
               WHERE m.status = 'active' AND m.target_date IS NOT NULL
               AND m.deleted_at IS NULL AND s.deleted_at IS NULL AND s.archived = 0
               ORDER BY m.target_date ASC""",
        ).fetchall()
        return [Milestone.from_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Open Point CRUD
    # ------------------------------------------------------------------

    def add_open_point(
        self,
        subject_id: str,
        text: str,
        context: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> str:
        point_id = _new_id()
        self.conn.execute(
            "INSERT INTO open_points (id, subject_id, text, context, comment) VALUES (?, ?, ?, ?, ?)",
            (point_id, subject_id, text, context, comment),
        )
        self.conn.commit()
        return point_id

    def get_open_point(self, point_id: str) -> Optional[OpenPoint]:
        row = self.conn.execute(
            "SELECT * FROM open_points WHERE id = ? AND deleted_at IS NULL",
            (point_id,),
        ).fetchone()
        return OpenPoint.from_row(row) if row else None

    def list_open_points(self, subject_id: str) -> List[OpenPoint]:
        """Return open points for a subject, excluding soft-deleted.

        Ordered by status (open first, parked second, resolved last) then raised_at.
        """
        _STATUS_ORDER = (
            "CASE status WHEN 'open' THEN 0 WHEN 'parked' THEN 1 WHEN 'resolved' THEN 2 ELSE 3 END"
        )
        sql = f"""
            SELECT * FROM open_points
            WHERE subject_id = ? AND deleted_at IS NULL
            ORDER BY {_STATUS_ORDER}, raised_at ASC
        """
        rows = self.conn.execute(sql, (subject_id,)).fetchall()
        return [OpenPoint.from_row(row) for row in rows]

    def update_open_point_status(self, point_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE open_points SET status = ? WHERE id = ?",
            (status, point_id),
        )
        self.conn.commit()

    def resolve_open_point(self, point_id: str, note: str) -> None:
        """Set status to resolved, record resolved_note and resolved_at."""
        self.conn.execute(
            "UPDATE open_points SET status = 'resolved', resolved_note = ?, resolved_at = ? WHERE id = ?",
            (note, self._now(), point_id),
        )
        self.conn.commit()

    def update_open_point_text(self, point_id: str, text: str) -> None:
        self.conn.execute(
            "UPDATE open_points SET text = ? WHERE id = ?",
            (text, point_id),
        )
        self.conn.commit()

    def update_open_point_context(self, point_id: str, context: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE open_points SET context = ? WHERE id = ?",
            (context, point_id),
        )
        self.conn.commit()

    def update_open_point_comment(self, point_id: str, comment: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE open_points SET comment = ? WHERE id = ?",
            (comment, point_id),
        )
        self.conn.commit()

    def update_open_point(
        self, point_id: str, text: str, context: Optional[str] = None,
        comment: Optional[str] = None, resolved_note: object = SENTINEL,
    ) -> None:
        """Update all fields on an open point in a single transaction."""
        with self.conn:
            self.conn.execute(
                "UPDATE open_points SET text = ?, context = ?, comment = ? WHERE id = ?",
                (text, context, comment, point_id),
            )
            if resolved_note is not SENTINEL:
                self.conn.execute(
                    "UPDATE open_points SET resolved_note = ? WHERE id = ?",
                    (resolved_note, point_id),
                )

    def soft_delete_open_point(self, point_id: str) -> None:
        self.conn.execute(
            "UPDATE open_points SET deleted_at = ? WHERE id = ?",
            (self._now(), point_id),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Follow-Up CRUD
    # ------------------------------------------------------------------

    def add_follow_up(
        self,
        subject_id: str,
        text: str,
        owner: str,
        due_by: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> str:
        follow_up_id = _new_id()
        self.conn.execute(
            "INSERT INTO follow_ups (id, subject_id, text, owner, due_by, comment) VALUES (?, ?, ?, ?, ?, ?)",
            (follow_up_id, subject_id, text, owner, due_by, comment),
        )
        self.conn.commit()
        return follow_up_id

    def get_follow_up(self, follow_up_id: str) -> Optional[FollowUp]:
        row = self.conn.execute(
            "SELECT * FROM follow_ups WHERE id = ? AND deleted_at IS NULL",
            (follow_up_id,),
        ).fetchone()
        return FollowUp.from_row(row) if row else None

    def list_follow_ups(self, subject_id: str) -> List[FollowUp]:
        """Return follow-ups for a subject, excluding soft-deleted.

        Ordered by status (waiting first, overdue second, rest after) then due_by ASC NULLS LAST.
        """
        _STATUS_ORDER = (
            "CASE status WHEN 'waiting' THEN 0 WHEN 'overdue' THEN 1 ELSE 2 END"
        )
        sql = f"""
            SELECT * FROM follow_ups
            WHERE subject_id = ? AND deleted_at IS NULL
            ORDER BY {_STATUS_ORDER}, due_by ASC NULLS LAST
        """
        rows = self.conn.execute(sql, (subject_id,)).fetchall()
        return [FollowUp.from_row(row) for row in rows]

    def update_follow_up_status(self, follow_up_id: str, status: str) -> None:
        self.conn.execute(
            "UPDATE follow_ups SET status = ? WHERE id = ?",
            (status, follow_up_id),
        )
        self.conn.commit()

    def update_follow_up_notes(self, follow_up_id: str, notes: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE follow_ups SET notes = ? WHERE id = ?",
            (notes, follow_up_id),
        )
        self.conn.commit()

    def update_follow_up_comment(self, follow_up_id: str, comment: Optional[str]) -> None:
        self.conn.execute(
            "UPDATE follow_ups SET comment = ? WHERE id = ?",
            (comment, follow_up_id),
        )
        self.conn.commit()

    def update_follow_up(
        self,
        follow_up_id: str,
        text: str,
        owner: str,
        due_by: Optional[str],
        asked_on: Optional[str] = None,
    ) -> None:
        """Update text, owner, due_by, and optionally asked_on fields on a follow-up."""
        if asked_on:
            self.conn.execute(
                "UPDATE follow_ups SET text = ?, owner = ?, due_by = ?, asked_on = ? WHERE id = ?",
                (text, owner, due_by, asked_on, follow_up_id),
            )
        else:
            self.conn.execute(
                "UPDATE follow_ups SET text = ?, owner = ?, due_by = ? WHERE id = ?",
                (text, owner, due_by, follow_up_id),
            )
        self.conn.commit()

    def soft_delete_follow_up(self, follow_up_id: str) -> None:
        self.conn.execute(
            "UPDATE follow_ups SET deleted_at = ? WHERE id = ?",
            (self._now(), follow_up_id),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Week rollover
    # ------------------------------------------------------------------

    def perform_week_rollover(self, force: bool = False) -> bool:
        """Perform week rollover housekeeping.

        1. Calculate current Monday from date.today().
        2. Read week_of from meta table.
        3. If not force and same week, return False.
        4. In a transaction:
           - Clear today flags on all tasks.
           - Reset day on non-done tasks.
           - Soft-delete done tasks completed more than 14 days ago.
           - Update meta.week_of to current Monday.
        5. Return True.
        """
        today = date.today()
        current_monday = today - timedelta(days=today.weekday())
        current_monday_str = current_monday.isoformat()

        row = self.conn.execute(
            "SELECT value FROM meta WHERE key = 'week_of'"
        ).fetchone()
        stored_week = row["value"] if row else None

        if not force and stored_week == current_monday_str:
            return False

        # First launch: just set week_of without wiping assignments
        if stored_week is None and not force:
            self.conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('week_of', ?)",
                (current_monday_str,),
            )
            self.conn.commit()
            return False

        cutoff = (today - timedelta(days=14)).isoformat()
        now = self._now()

        with self.conn:
            # Clear today flags on all tasks
            self.conn.execute("UPDATE tasks SET today = 0 WHERE deleted_at IS NULL")
            # Reset day on non-done tasks
            self.conn.execute(
                "UPDATE tasks SET day = NULL WHERE status != 'done' AND deleted_at IS NULL"
            )
            # Soft-delete done tasks completed more than 14 days ago
            self.conn.execute(
                """UPDATE tasks SET deleted_at = ?
                   WHERE status = 'done'
                   AND completed_at IS NOT NULL
                   AND DATE(completed_at) <= ?
                   AND deleted_at IS NULL""",
                (now, cutoff),
            )
            # Update meta.week_of
            self.conn.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('week_of', ?)",
                (current_monday_str,),
            )

        return True
