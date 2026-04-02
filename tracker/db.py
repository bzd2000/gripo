"""Database class — schema init and all SQL queries."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Union

from tracker.models import FollowUp, Note, OpenPoint, Subject, Task

_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS subjects (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    pinned        INTEGER NOT NULL DEFAULT 0,
    archived      INTEGER NOT NULL DEFAULT 0,
    color         TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    text          TEXT NOT NULL,
    priority      TEXT NOT NULL DEFAULT 'should' CHECK (priority IN ('must', 'should', 'if-time')),
    status        TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo', 'in-progress', 'done', 'blocked')),
    category      TEXT CHECK (category IN ('delivery', 'admin', 'people', 'strategy', 'meeting', 'other')),
    day           TEXT CHECK (day IN ('mon', 'tue', 'wed', 'thu', 'fri', 'anytime')),
    today         INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at  TEXT,
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS open_points (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    text          TEXT NOT NULL,
    context       TEXT,
    status        TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'resolved', 'parked')),
    resolved_note TEXT,
    raised_at     TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at   TEXT,
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS follow_ups (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    text          TEXT NOT NULL,
    owner         TEXT NOT NULL,
    asked_on      TEXT NOT NULL DEFAULT (date('now')),
    due_by        TEXT,
    status        TEXT NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'received', 'overdue', 'cancelled')),
    notes         TEXT,
    deleted_at    TEXT
);

CREATE TABLE IF NOT EXISTS notes (
    id            TEXT PRIMARY KEY,
    subject_id    TEXT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    content       TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now')),
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
        self.conn.commit()

    # ------------------------------------------------------------------
    # Subject CRUD
    # ------------------------------------------------------------------

    def add_subject(
        self,
        name: str,
        color: Optional[str] = None,
        pinned: bool = False,
    ) -> str:
        subject_id = _new_id()
        self.conn.execute(
            "INSERT INTO subjects (id, name, color, pinned) VALUES (?, ?, ?, ?)",
            (subject_id, name, color, int(pinned)),
        )
        self.conn.commit()
        return subject_id

    def get_subject(self, subject_id: str) -> Optional[Subject]:
        row = self.conn.execute(
            "SELECT * FROM subjects WHERE id = ?", (subject_id,)
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
            ORDER BY s.pinned DESC, s.name ASC
        """
        rows = self.conn.execute(sql).fetchall()
        return [Subject.from_row(row) for row in rows]

    def toggle_pin(self, subject_id: str) -> None:
        self.conn.execute(
            "UPDATE subjects SET pinned = CASE WHEN pinned = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (subject_id,),
        )
        self.conn.commit()

    def archive_subject(self, subject_id: str) -> None:
        self.conn.execute(
            "UPDATE subjects SET archived = 1 WHERE id = ?", (subject_id,)
        )
        self.conn.commit()

    def soft_delete_subject(self, subject_id: str) -> None:
        """Soft-delete a subject and all its child records in a single transaction."""
        now = datetime.now(timezone.utc).isoformat()
        with self.conn:
            self.conn.execute(
                "UPDATE subjects SET deleted_at = ? WHERE id = ?", (now, subject_id)
            )
            for table in ("tasks", "open_points", "follow_ups", "notes"):
                self.conn.execute(
                    f"UPDATE {table} SET deleted_at = ? WHERE subject_id = ? AND deleted_at IS NULL",
                    (now, subject_id),
                )

    # ------------------------------------------------------------------
    # Task stubs (needed for cascade tests and future tasks)
    # ------------------------------------------------------------------

    def add_task(
        self,
        subject_id: str,
        text: str,
        priority: str = "should",
        status: str = "todo",
        category: Optional[str] = None,
        day: Optional[str] = None,
        today: bool = False,
    ) -> str:
        task_id = _new_id()
        self.conn.execute(
            """INSERT INTO tasks (id, subject_id, text, priority, status, category, day, today)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, subject_id, text, priority, status, category, day, int(today)),
        )
        self.conn.commit()
        return task_id

    def list_tasks(self, subject_id: str) -> List[Task]:
        rows = self.conn.execute(
            "SELECT * FROM tasks WHERE subject_id = ?", (subject_id,)
        ).fetchall()
        return [Task.from_row(row) for row in rows]

    # ------------------------------------------------------------------
    # Note stubs (needed for cascade tests and future tasks)
    # ------------------------------------------------------------------

    def add_note(self, subject_id: str, content: str) -> str:
        note_id = _new_id()
        self.conn.execute(
            "INSERT INTO notes (id, subject_id, content) VALUES (?, ?, ?)",
            (note_id, subject_id, content),
        )
        self.conn.commit()
        return note_id

    def list_notes(self, subject_id: str) -> List[Note]:
        rows = self.conn.execute(
            "SELECT * FROM notes WHERE subject_id = ?", (subject_id,)
        ).fetchall()
        return [Note.from_row(row) for row in rows]
