# Tree Layout Redesign — Design Spec

Replace the current `TabbedContent` + `ModalScreen` architecture with a tree sidebar + content pane layout.

## Layout

Horizontal split: `Tree` widget on the left (~25% width), `ContentArea` container on the right (~75%). The tree is always visible.

## Focus Model

- Arrow keys navigate the tree when it has focus
- `Enter` on a tree node: expands/collapses children AND updates the right pane
- `ctrl+w` from anywhere in the right pane: moves focus back to the tree
- When the right pane shows a form, `Enter` saves and returns to the parent list view, `Escape` cancels

## Tree Structure (3 levels)

```
▸ Today (3)
▸ This Week
▼ Project Alpha
  ▼ Tasks (4)
    ○ Review PR
    ● Write tests
    ✓ Set up CI
  ▸ Open Points (2)
  ▸ Follow-Ups (1)
  ▸ Notes (3)
▸ Q2 Planning
▸ Client: Acme
```

**Level 1:** Today, This Week, Subjects (each subject is a node)
**Level 2:** Section nodes under each subject — Tasks, Open Points, Follow-Ups, Notes (with counts)
**Level 3:** Individual items under each section — task rows, note rows, etc.

Pinned subjects float to top. Archived subjects hidden by default (toggle with `shift+a`).

## Right Pane Content Per Tree Node

| Tree node | Right pane |
|-----------|-----------|
| Today | Cross-cutting today task list (max 5, priority ordered) |
| This Week | Week view grouped by day |
| Subject | Overview dashboard |
| Tasks (section) | Full task list with CRUD bindings |
| A specific task | Task detail/edit form |
| Open Points (section) | Full open points list with bindings |
| A specific open point | Open point detail/edit form |
| Follow-Ups (section) | Full follow-ups list with bindings |
| A specific follow-up | Follow-up detail/edit form |
| Notes (section) | Full notes list |
| A specific note | Markdown editor (TextArea) |

## Subject Overview Dashboard

When a subject node is selected, the right pane shows a highlights dashboard:
- Important/due tasks (must priority or has due_date approaching)
- Open points with status "open"
- Follow-ups with status "waiting" or "overdue"
- Most recent notes (last 3)

Each section is a compact summary, not the full list.

## Adding Items

Press `a` while on a section node (e.g. Tasks) → right pane switches to an empty add form. `Enter` saves the item, refreshes the tree (new leaf appears), and returns to the list view. `Escape` cancels and returns to the list view.

## Editing Items

Select an item leaf in the tree (or press `e` on a section list) → right pane shows detail/edit form pre-filled with current values. `Enter` saves, `Escape` cancels. Both return to the list view.

## Deleting Items

Press `x` on a section list or item → `ConfirmScreen` modal dialog (kept as-is). Soft delete on confirm.

## Item Status/Priority Shortcuts

When viewing a section list (e.g. Tasks list on the right pane), the existing keyboard shortcuts still work:
- Tasks: `d` done, `b` blocked, `s` cycle status, `p` cycle priority, `t` toggle today, `w` cycle day
- Open Points: `s` cycle status, `r` resolve
- Follow-Ups: `s` cycle status

These operate on the highlighted item in the right pane list, same as before.

## Modals (kept)

- `ConfirmScreen` — delete confirmations
- `SearchScreen` — `/` search overlay with live results
- `HelpScreen` — `?` keyboard shortcut reference

## Global Bindings

- `q` — quit
- `/` — search (modal)
- `?` — help (modal)
- `ctrl+w` — focus tree
- `a` — add subject (when tree is focused on root level), add item (when on a section node)
- `p` — toggle pin (when on a subject node)
- `x` — archive subject (when on subject node)

## Tree Refresh

After any mutation (add, edit, delete, status change), the tree must refresh to reflect:
- Updated counts on section nodes: "Tasks (4)", "Open Points (2)"
- Updated item labels (status icons, text changes)
- New/removed leaf nodes
- Updated Today/This Week counts

The tree should preserve the current selection and expansion state across refreshes.

## What Gets Removed

- `TabbedContent` / `TabPane` usage in `TrackerApp`
- `SubjectDetailScreen` (replaced by tree navigation + content pane)
- `AddTaskScreen`, `EditTaskScreen` (replaced by inline form widgets in right pane)
- `AddNoteScreen`, `EditNoteScreen` (replaced by inline form/editor in right pane)
- `AddOpenPointScreen`, `ResolveScreen` (replaced by inline forms)
- `AddFollowUpScreen` (replaced by inline form)
- `AddSubjectScreen` (replaced by inline form)
- `SubjectsList` widget (replaced by tree)

## What Gets Kept

- `Database` class and all CRUD methods — unchanged
- All models — unchanged
- `DataChanged` message — unchanged
- `ConfirmScreen` — unchanged
- `SearchScreen` — unchanged
- `HelpScreen` — unchanged
- `tracker.tcss` — updated for new layout, existing status/priority classes kept
- All tests — unchanged (they test the DB layer)

## Markdown Comments

Tasks, follow-ups, and open points each get a `comment` TEXT field (nullable, markdown). This is a new DB column on each table (with migration).

**Display:** When viewing an item's detail in the right pane, the comment is rendered as markdown (using Textual's `Markdown` widget) at the bottom of the pane.

**Editing:** When editing an item, the comment field shows as a raw markdown `TextArea` (same as notes editing).

**Notes:** Notes content is also rendered as markdown when viewing the notes list (preview), and as raw `TextArea` when editing.

**Rule:** All markdown content is rendered via Textual's `Markdown` widget everywhere except in edit mode, where it shows as a raw `TextArea`.

## DateInput Widget

A reusable `DateInput` widget for all date fields (task due date, follow-up due date, follow-up asked_on).

**Behavior:**
- Pre-filled with today's date (YYYY-MM-DD)
- Left/Right arrow: decrease/increase by 1 day
- Up/Down arrow: decrease/increase by 1 month
- Still editable as text (type a date directly)
- `Delete` or `Backspace` on empty clears to None (for optional dates)

Used in: task form, follow-up form.

## New Files

- `tracker/widgets/date_input.py` — `DateInput` widget
- `tracker/widgets/nav_tree.py` — `NavTree(Tree)` widget
- `tracker/widgets/content_area.py` — `ContentArea` container that swaps child widgets
- `tracker/widgets/subject_overview.py` — Subject dashboard widget
- `tracker/widgets/task_form.py` — Task add/edit form (inline, not modal)
- `tracker/widgets/open_point_form.py` — Open point add/edit form
- `tracker/widgets/follow_up_form.py` — Follow-up add/edit form
- `tracker/widgets/note_editor.py` — Note add/edit with TextArea
- `tracker/widgets/subject_form.py` — Subject add form

## Modified Files

- `tracker/app.py` — replace TabbedContent with Tree + ContentArea split
- `tracker/tracker.tcss` — add tree/pane layout styles
- `tracker/widgets/task_list.py` — remove modal pushes, emit messages for tree to handle
- `tracker/widgets/notes_list.py` — same
- `tracker/widgets/open_points_list.py` — same
- `tracker/widgets/follow_ups_list.py` — same
- `tracker/widgets/today_view.py` — adapt to work in content pane
- `tracker/widgets/week_view.py` — adapt to work in content pane

## Files to Delete

- `tracker/screens/subject_detail.py`
- `tracker/screens/add_subject.py`
- `tracker/screens/add_task.py`
- `tracker/screens/edit_task.py`
- `tracker/screens/add_note.py`
- `tracker/screens/edit_note.py`
- `tracker/screens/add_open_point.py`
- `tracker/screens/add_follow_up.py`
- `tracker/screens/resolve_point.py`
- `tracker/widgets/subjects_list.py`
