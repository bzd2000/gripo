"""Dataclasses mapping SQLite rows to Python objects."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Subject:
    id: str
    name: str
    pinned: bool
    archived: bool
    color: Optional[str]
    created_at: str
    deleted_at: Optional[str]

    # Optional aggregate fields populated by list_subjects()
    open_tasks: int = 0
    open_points_count: int = 0
    follow_ups_count: int = 0
    latest_note: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Subject":
        keys = row.keys()
        return cls(
            id=row["id"],
            name=row["name"],
            pinned=bool(row["pinned"]),
            archived=bool(row["archived"]),
            color=row["color"],
            created_at=row["created_at"],
            deleted_at=row["deleted_at"],
            open_tasks=row["open_tasks"] if "open_tasks" in keys else 0,
            open_points_count=row["open_points_count"] if "open_points_count" in keys else 0,
            follow_ups_count=row["follow_ups_count"] if "follow_ups_count" in keys else 0,
            latest_note=row["latest_note"] if "latest_note" in keys else None,
        )


@dataclass
class Task:
    id: str
    subject_id: str
    text: str
    priority: str
    status: str
    category: Optional[str]
    day: Optional[str]
    today: bool
    due_date: Optional[str]
    comment: Optional[str]
    created_at: str
    completed_at: Optional[str]
    deleted_at: Optional[str]

    # Optional field for cross-cutting queries
    subject_name: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Task":
        keys = row.keys()
        return cls(
            id=row["id"],
            subject_id=row["subject_id"],
            text=row["text"],
            priority=row["priority"],
            status=row["status"],
            category=row["category"],
            day=row["day"],
            today=bool(row["today"]),
            due_date=row["due_date"] if "due_date" in keys else None,
            comment=row["comment"] if "comment" in keys else None,
            created_at=row["created_at"],
            completed_at=row["completed_at"],
            deleted_at=row["deleted_at"],
            subject_name=row["subject_name"] if "subject_name" in keys else None,
        )


@dataclass
class OpenPoint:
    id: str
    subject_id: str
    text: str
    context: Optional[str]
    status: str
    resolved_note: Optional[str]
    comment: Optional[str]
    raised_at: str
    resolved_at: Optional[str]
    deleted_at: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "OpenPoint":
        keys = row.keys()
        return cls(
            id=row["id"],
            subject_id=row["subject_id"],
            text=row["text"],
            context=row["context"],
            status=row["status"],
            resolved_note=row["resolved_note"],
            comment=row["comment"] if "comment" in keys else None,
            raised_at=row["raised_at"],
            resolved_at=row["resolved_at"],
            deleted_at=row["deleted_at"],
        )


@dataclass
class FollowUp:
    id: str
    subject_id: str
    text: str
    owner: str
    asked_on: str
    due_by: Optional[str]
    status: str
    notes: Optional[str]
    comment: Optional[str]
    deleted_at: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "FollowUp":
        keys = row.keys()
        return cls(
            id=row["id"],
            subject_id=row["subject_id"],
            text=row["text"],
            owner=row["owner"],
            asked_on=row["asked_on"],
            due_by=row["due_by"],
            status=row["status"],
            notes=row["notes"],
            comment=row["comment"] if "comment" in keys else None,
            deleted_at=row["deleted_at"],
        )


@dataclass
class Note:
    id: str
    subject_id: str
    content: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str]

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Note":
        return cls(
            id=row["id"],
            subject_id=row["subject_id"],
            content=row["content"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            deleted_at=row["deleted_at"],
        )
