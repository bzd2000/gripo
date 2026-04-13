"""Shared constants for status/priority icons and cycles."""

TASK_STATUS_ICON = {
    "todo": "○",
    "in-progress": "●",
    "done": "✓",
    "blocked": "✗",
}

FU_STATUS_ICON = {
    "waiting": "⏳",
    "received": "✓",
    "overdue": "‼",
    "cancelled": "✗",
}

OP_STATUS_ICON = {
    "open": "?",
    "resolved": "✓",
    "parked": "—",
}

MS_STATUS_ICON = {
    "active": "◎",
    "completed": "✓",
    "cancelled": "✗",
}

STATUS_CYCLE = ["todo", "in-progress", "done", "blocked"]
PRIORITY_CYCLE = ["must", "should", "if-time"]
DAYS = ["mon", "tue", "wed", "thu", "fri"]
DAY_LABELS = {"mon": "MON", "tue": "TUE", "wed": "WED", "thu": "THU", "fri": "FRI"}
