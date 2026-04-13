"""NavTree widget — navigation tree for the tracker TUI."""

from __future__ import annotations

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from tracker.db import Database
from tracker.messages import DataChanged, ShowContent

_TASK_STATUS_ICON = {
    "todo": "○",
    "in-progress": "●",
    "done": "✓",
    "blocked": "✗",
}

_OP_STATUS_ICON = {
    "open": "?",
    "resolved": "✓",
    "parked": "—",
}

_FU_STATUS_ICON = {
    "waiting": "⏳",
    "received": "✓",
    "overdue": "‼",
    "cancelled": "✗",
}


def _truncate(text: str, max_len: int = 50) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


class NavTree(Tree):
    """Navigation tree showing subjects and their children."""

    BINDINGS = [
        Binding("p", "toggle_pin", "Toggle pin"),
        Binding("e", "edit_subject", "Edit"),
        Binding("x", "archive_subject", "Archive"),
        Binding("a", "add", "Add"),
        Binding("A", "toggle_archived", "Toggle archived"),
    ]

    def __init__(self, db: Database) -> None:
        super().__init__("Overview")
        self._db = db
        self._show_archived = False
        # Track expanded state: set of label strings for expanded nodes
        self._expanded_paths: set[str] = set()
        self.show_root = True
        self.auto_expand = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_mount(self) -> None:
        self.rebuild()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rebuild(self) -> None:
        """Clear tree and add all root nodes."""
        self.clear()
        root = self.root
        root.expand()
        root.allow_expand = False

        # Root is the overview node
        today_count = self._count_today_non_done()
        week_tasks = self._db.list_week_tasks()
        week_fus = self._db.list_week_follow_ups()
        week_count = len(week_tasks) + len(week_fus)
        root.set_label(f"Overview ({today_count} today, {week_count} week)")
        root.data = {"type": "overview", "id": "overview", "subject_id": None}

        # Subjects grouped by type
        subjects = self._db.list_subjects(include_archived=self._show_archived)
        type_labels = {
            "person": "People",
            "team": "Teams",
            "project": "Projects",
            "board": "Boards",
            None: "Other",
        }
        type_order = ["person", "team", "project", "board", None]

        # Group subjects by type
        by_type: dict[str | None, list] = {t: [] for t in type_order}
        for subject in subjects:
            key = subject.subject_type if subject.subject_type in type_labels else None
            by_type[key].append(subject)

        for stype in type_order:
            group = by_type[stype]
            if not group:
                continue
            group_label = type_labels[stype]
            group_node = root.add(
                group_label,
                data={"type": "type_group", "id": f"type_{stype}", "subject_id": None},
            )
            group_node.expand()
            for subject in group:
                pin_indicator = " 📌" if subject.pinned else ""
                archived_indicator = " [archived]" if subject.archived else ""
                subject_node = group_node.add(
                    f"{subject.name}{pin_indicator}{archived_indicator}",
                    data={
                        "type": "subject",
                        "id": subject.id,
                        "subject_id": subject.id,
                    },
                )
                self._add_subject_children(subject_node, subject.id)

    def refresh_tree(self) -> None:
        """Rebuild while preserving expanded state and current selection."""
        # Collect expanded node labels
        self._expanded_paths = self._collect_expanded_paths(self.root)
        # Remember current cursor
        current_node = self.cursor_node
        current_data = current_node.data if current_node else None

        self.rebuild()
        # Restore expansion
        self._restore_expanded_paths(self.root, self._expanded_paths)
        # Try to restore cursor by matching data
        if current_data:
            self._restore_cursor(self.root, current_data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _count_today_non_done(self) -> int:
        tasks = self._db.list_today_tasks()
        follow_ups = self._db.list_today_follow_ups()
        return len([t for t in tasks if t.status != "done"]) + len(follow_ups)

    def _add_subject_children(self, subject_node: TreeNode, subject_id: str) -> None:
        """Add section children (Tasks, Open Points, Follow-Ups, Notes) under a subject."""
        tasks = self._db.list_tasks(subject_id)
        task_count = len([t for t in tasks if t.status != "done"])
        task_section = subject_node.add(
            f"Tasks ({task_count})",
            data={
                "type": "task_section",
                "id": f"tasks_{subject_id}",
                "subject_id": subject_id,
            },
        )
        for task in tasks:
            icon = _TASK_STATUS_ICON.get(task.status, "?")
            task_section.add_leaf(
                f"{icon} {_truncate(task.text)}",
                data={
                    "type": "task",
                    "id": task.id,
                    "subject_id": subject_id,
                },
            )

        open_points = self._db.list_open_points(subject_id)
        op_open_count = len([p for p in open_points if p.status == "open"])
        op_section = subject_node.add(
            f"Open Points ({op_open_count})",
            data={
                "type": "open_points_section",
                "id": f"open_points_{subject_id}",
                "subject_id": subject_id,
            },
        )
        for point in open_points:
            icon = _OP_STATUS_ICON.get(point.status, "?")
            op_section.add_leaf(
                f"{icon} {_truncate(point.text)}",
                data={
                    "type": "open_point",
                    "id": point.id,
                    "subject_id": subject_id,
                },
            )

        follow_ups = self._db.list_follow_ups(subject_id)
        fu_waiting_count = len([f for f in follow_ups if f.status in ("waiting", "overdue")])
        fu_section = subject_node.add(
            f"Follow-Ups ({fu_waiting_count})",
            data={
                "type": "follow_ups_section",
                "id": f"follow_ups_{subject_id}",
                "subject_id": subject_id,
            },
        )
        for fu in follow_ups:
            icon = _FU_STATUS_ICON.get(fu.status, "?")
            fu_section.add_leaf(
                f"{icon} {_truncate(fu.text)}",
                data={
                    "type": "follow_up",
                    "id": fu.id,
                    "subject_id": subject_id,
                },
            )

        milestones = self._db.list_milestones(subject_id)
        ms_active_count = len([m for m in milestones if m.status == "active"])
        ms_section = subject_node.add(
            f"Milestones ({ms_active_count})",
            data={
                "type": "milestones_section",
                "id": f"milestones_{subject_id}",
                "subject_id": subject_id,
            },
        )
        for ms in milestones:
            icon = "◎" if ms.status == "active" else ("✓" if ms.status == "completed" else "✗")
            ms_section.add_leaf(
                f"{icon} {_truncate(ms.name)}",
                data={
                    "type": "milestone",
                    "id": ms.id,
                    "subject_id": subject_id,
                },
            )

        notes = self._db.list_notes(subject_id)
        notes_section = subject_node.add(
            f"Notes ({len(notes)})",
            data={
                "type": "notes_section",
                "id": f"notes_{subject_id}",
                "subject_id": subject_id,
            },
        )
        for note in notes:
            date_str = note.created_at[:10]
            preview = _truncate(note.content.replace("\n", " "), 40)
            notes_section.add_leaf(
                f"{date_str} {preview}",
                data={
                    "type": "note",
                    "id": note.id,
                    "subject_id": subject_id,
                },
            )

    def _collect_expanded_paths(self, node: TreeNode, prefix: str = "") -> set[str]:
        """Collect string labels of all expanded nodes."""
        expanded = set()
        path = f"{prefix}/{node.label}"
        if node.is_expanded:
            expanded.add(path)
        for child in node.children:
            expanded |= self._collect_expanded_paths(child, path)
        return expanded

    def _restore_expanded_paths(self, node: TreeNode, expanded: set[str], prefix: str = "") -> None:
        """Re-expand nodes that were expanded before rebuild."""
        path = f"{prefix}/{node.label}"
        if path in expanded:
            node.expand()
        for child in node.children:
            self._restore_expanded_paths(child, expanded, path)

    def _restore_cursor(self, node: TreeNode, target_data: dict) -> bool:
        """Move cursor to a node matching target_data. Returns True if found."""
        if node.data and node.data.get("id") == target_data.get("id"):
            self.move_cursor(node)
            return True
        for child in node.children:
            if self._restore_cursor(child, target_data):
                return True
        return False

    def reveal_content(self, content_type: str, data: dict) -> None:
        """Expand tree and select the relevant node for a content request."""
        subject_id = data.get("subject_id")
        if not subject_id:
            return

        item_id = (
            data.get("task_id") or data.get("point_id")
            or data.get("follow_up_id") or data.get("note_id")
            or data.get("milestone_id")
        )

        # Search through type group nodes → subject nodes
        for group in self.root.children:
            for child in group.children:
                if child.data and child.data.get("type") == "subject" and child.data.get("id") == subject_id:
                    group.expand()
                    child.expand()
                    if item_id:
                        for section in child.children:
                            section.expand()
                        self.set_timer(0.1, lambda: self._deferred_select(item_id))
                    else:
                        self.move_cursor(child)
                    return

    def reveal_section(self, content_type: str, data: dict) -> None:
        """Select the section node matching a list content type."""
        subject_id = data.get("subject_id")
        if not subject_id:
            return

        section_type_map = {
            "task_list": "task_section",
            "open_points_list": "open_points_section",
            "follow_ups_list": "follow_ups_section",
            "notes_list": "notes_section",
            "milestone_list": "milestones_section",
        }
        target_type = section_type_map.get(content_type)
        if not target_type:
            return

        for group in self.root.children:
            for child in group.children:
                if child.data and child.data.get("type") == "subject" and child.data.get("id") == subject_id:
                    group.expand()
                    child.expand()
                    for section in child.children:
                        if section.data and section.data.get("type") == target_type:
                            self.move_cursor(section)
                            return
                    return

    def _deferred_select(self, item_id: str) -> None:
        """Select a node by item id after tree has laid out."""
        self._find_and_select(self.root, item_id)

    def _find_and_select(self, node: TreeNode, item_id: str) -> bool:
        if node.data and node.data.get("id") == item_id:
            self.move_cursor(node)
            self.scroll_to_node(node)
            return True
        for child in node.children:
            if self._find_and_select(child, item_id):
                return True
        return False

    def _current_subject_id(self) -> Optional[str]:
        """Return subject_id from the currently selected node, if applicable."""
        node = self.cursor_node
        if node and node.data:
            return node.data.get("subject_id")
        return None

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Post ShowContent based on selected node type."""
        node = event.node
        if not node.data:
            return
        data = node.data
        node_type = data.get("type")

        if node_type == "overview":
            self.post_message(ShowContent("overview", {}))
        elif node_type == "subject":
            self.post_message(
                ShowContent("subject_overview", {"subject_id": data["subject_id"]})
            )
        elif node_type == "task_section":
            self.post_message(
                ShowContent("task_list", {"subject_id": data["subject_id"]})
            )
        elif node_type == "open_points_section":
            self.post_message(
                ShowContent("open_points_list", {"subject_id": data["subject_id"]})
            )
        elif node_type == "follow_ups_section":
            self.post_message(
                ShowContent("follow_ups_list", {"subject_id": data["subject_id"]})
            )
        elif node_type == "notes_section":
            self.post_message(
                ShowContent("notes_list", {"subject_id": data["subject_id"]})
            )
        elif node_type == "task":
            self.post_message(
                ShowContent(
                    "task_form",
                    {"subject_id": data["subject_id"], "task_id": data["id"]},
                )
            )
        elif node_type == "open_point":
            self.post_message(
                ShowContent(
                    "open_point_form",
                    {"subject_id": data["subject_id"], "point_id": data["id"]},
                )
            )
        elif node_type == "follow_up":
            self.post_message(
                ShowContent(
                    "follow_up_form",
                    {"subject_id": data["subject_id"], "follow_up_id": data["id"]},
                )
            )
        elif node_type == "note":
            self.post_message(
                ShowContent(
                    "note_editor",
                    {"subject_id": data["subject_id"], "note_id": data["id"]},
                )
            )
        elif node_type == "milestones_section":
            self.post_message(
                ShowContent("milestone_list", {"subject_id": data["subject_id"]})
            )
        elif node_type == "milestone":
            self.post_message(
                ShowContent(
                    "milestone_view",
                    {"subject_id": data["subject_id"], "milestone_id": data["id"]},
                )
            )

    # ------------------------------------------------------------------
    # Actions (key bindings)
    # ------------------------------------------------------------------

    def action_toggle_pin(self) -> None:
        subject_id = self._current_subject_id()
        if not subject_id:
            return
        node = self.cursor_node
        if node and node.data and node.data.get("type") == "subject":
            self._db.toggle_pin(subject_id)
            self.post_message(DataChanged())
            self.refresh_tree()

    def action_edit_subject(self) -> None:
        subject_id = self._current_subject_id()
        if subject_id:
            self.post_message(ShowContent("subject_form", {"subject_id": subject_id}))

    def action_archive_subject(self) -> None:
        subject_id = self._current_subject_id()
        if not subject_id:
            return
        node = self.cursor_node
        if node and node.data and node.data.get("type") == "subject":
            from tracker.screens.confirm import ConfirmScreen

            def _on_confirm(confirmed: bool) -> None:
                if confirmed:
                    self._db.archive_subject(subject_id)
                    self.post_message(DataChanged())
                    self.refresh_tree()

            self.app.push_screen(ConfirmScreen("Archive this subject?"), _on_confirm)

    def action_add(self) -> None:
        """Context-aware add: adds the right type based on current tree position."""
        node = self.cursor_node
        if not node or not node.data:
            self.post_message(ShowContent("subject_form", {}))
            return

        node_type = node.data.get("type")
        subject_id = node.data.get("subject_id")

        # On a section node → add that type
        if node_type == "task_section":
            self.post_message(ShowContent("task_form", {"subject_id": subject_id}))
        elif node_type == "open_points_section":
            self.post_message(ShowContent("open_point_form", {"subject_id": subject_id}))
        elif node_type == "follow_ups_section":
            self.post_message(ShowContent("follow_up_form", {"subject_id": subject_id}))
        elif node_type == "notes_section":
            self.post_message(ShowContent("note_editor", {"subject_id": subject_id}))
        elif node_type == "milestones_section":
            self.post_message(ShowContent("milestone_form", {"subject_id": subject_id}))
        # On a leaf item → add same type as sibling
        elif node_type == "task":
            self.post_message(ShowContent("task_form", {"subject_id": subject_id}))
        elif node_type == "open_point":
            self.post_message(ShowContent("open_point_form", {"subject_id": subject_id}))
        elif node_type == "follow_up":
            self.post_message(ShowContent("follow_up_form", {"subject_id": subject_id}))
        elif node_type == "note":
            self.post_message(ShowContent("note_editor", {"subject_id": subject_id}))
        elif node_type == "milestone":
            self.post_message(ShowContent("milestone_form", {"subject_id": subject_id}))
        # On a subject node → add subject
        elif node_type == "subject":
            self.post_message(ShowContent("subject_form", {}))
        # Root level → add subject
        else:
            self.post_message(ShowContent("subject_form", {}))

    def action_toggle_archived(self) -> None:
        self._show_archived = not self._show_archived
        self.refresh_tree()
