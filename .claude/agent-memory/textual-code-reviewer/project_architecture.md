---
name: Tracker TUI Architecture Patterns
description: Key architecture patterns, widget conventions, and code style used in the Tracker TUI codebase
type: project
---

Architecture and code patterns observed in the Tracker TUI:

**Widget data attachment pattern**: ListItem widgets store data via monkey-patched private attributes (e.g., `li._task_id = task.id` with `# type: ignore[attr-defined]`). This is used consistently across all list views.

**Form pattern**: All forms (TaskForm, OpenPointForm, FollowUpForm, MilestoneForm) use `.item-form` CSS class, grid layout with fields on left and CommentEditor on right. They post DataChanged + ContentSaved on save, ContentCancelled on escape.

**List pattern**: All list widgets (TaskList, OpenPointsList, FollowUpsList, NotesList, MilestoneList) extend ListView directly, have `_refresh_list()`, `_highlighted_*()` helpers, and inline key bindings for CRUD.

**_ItemList subclass**: Used in OverviewView and MilestoneView for focus/blur highlight management (sets index=0 on focus, index=None on blur).

**ContentArea widget factory**: Uses lazy imports inside `_create_widget()` with ImportError fallbacks to Label for some widgets.

**Navigation**: ContentArea._navigate_to_parent() handles back-navigation with a mapping dict. Tree cursor sync happens via reveal_content/reveal_section.

**DB**: Single connection, no connection pooling. Each mutation calls conn.commit() individually. _SENTINEL pattern for optional update fields.

**Why:** Understanding these patterns is critical for consistent code reviews.
**How to apply:** Flag deviations from these patterns in reviews; suggest following them for new code.
