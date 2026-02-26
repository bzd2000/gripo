# Gripo — Design Document

**Date**: 2026-02-26
**Purpose**: Personal task/project/planning app to get grip on your work.

## Overview

Gripo is a local-first, offline-capable personal productivity app. It helps users organize work around **Subjects** — flexible containers that can represent a project, person, team, or board. Each subject holds Tasks, Agenda Points, and Meeting Minutes.

The primary interaction model is a **command palette** (`Cmd+K` / `Ctrl+K`) for keyboard-driven quick capture and navigation. The visual style is warm and friendly.

## Tech Stack

- **Framework**: Vue 3 + Quasar Framework (v2)
- **Language**: TypeScript (strict mode)
- **State Management**: Pinia
- **Rich Text**: Tiptap (MIT, open source)
- **Local Storage**: Dexie.js (IndexedDB)
- **Build**: Vite via @quasar/app-vite
- **Targets**: Electron (desktop), PWA (browser)
- **Testing**: Vitest, Vue Test Utils, Cypress or Playwright

## Data Model

### Subject

| Field       | Type     | Description                                      |
|-------------|----------|--------------------------------------------------|
| id          | string   | Auto-generated                                   |
| name        | string   | Display name (e.g., "Project Alpha", "John")     |
| type        | enum     | `project` \| `person` \| `team` \| `board` \| `other` |
| color       | string   | Color for visual identification                  |
| pinned      | boolean  | Keep visible on dashboard regardless of dates    |
| archived    | boolean  | Soft-archive instead of delete                   |
| startDate   | date?    | Optional start date for time-bound subjects      |
| endDate     | date?    | Optional end date for time-bound subjects        |
| createdAt   | date     | Creation timestamp                               |
| updatedAt   | date     | Last update timestamp                            |

### Task

| Field       | Type     | Description                                      |
|-------------|----------|--------------------------------------------------|
| id          | string   | Auto-generated                                   |
| subjectId   | string   | Belongs to a subject                             |
| title       | string   | Rich text (HTML via Tiptap)                      |
| description | string   | Rich text (HTML via Tiptap)                      |
| status      | enum     | `todo` \| `in-progress` \| `done`                |
| priority    | enum     | `low` \| `medium` \| `high`                      |
| dueDate     | date?    | Optional due date                                |
| createdAt   | date     | Creation timestamp                               |
| updatedAt   | date     | Last update timestamp                            |

### AgendaPoint

| Field       | Type     | Description                                      |
|-------------|----------|--------------------------------------------------|
| id          | string   | Auto-generated                                   |
| subjectId   | string   | Belongs to a subject                             |
| title       | string   | Rich text (HTML via Tiptap)                      |
| content     | string   | Rich text (HTML via Tiptap)                      |
| resolved    | boolean  | Whether it has been discussed                    |
| createdAt   | date     | Creation timestamp                               |
| updatedAt   | date     | Last update timestamp                            |

### MeetingMinutes

| Field       | Type     | Description                                      |
|-------------|----------|--------------------------------------------------|
| id          | string   | Auto-generated                                   |
| subjectId   | string   | Belongs to a subject                             |
| title       | string   | Rich text (HTML via Tiptap)                      |
| content     | string   | Rich text (HTML via Tiptap)                      |
| date        | date     | Meeting date                                     |
| createdAt   | date     | Creation timestamp                               |
| updatedAt   | date     | Last update timestamp                            |

## Navigation & Views

### Dashboard (Home)

Time-bucketed overview of work across all subjects:

- **Today** — tasks due today
- **This week** — tasks due this week
- **Next week** — tasks due next week
- **Ongoing subjects** — subjects with active time spans (startDate/endDate)
- **Pinned subjects** — subjects flagged to stay on your radar

Each item shows its parent subject name and color for context. Clicking navigates to the item within its subject.

### Subject List (Sidebar)

- Persistent left sidebar showing all subjects
- Each subject shows: name, color dot, count badge (open tasks + unresolved agenda points)
- Subjects can be reordered via drag-and-drop
- Archived subjects hidden by default, toggle to show

### Subject Detail View

Main area when a subject is selected. Three tabs:

- **Tasks** — list of tasks, filterable by status/priority
- **Agenda** — list of agenda points, unresolved on top
- **Minutes** — list of meeting minutes, sorted by date (newest first)

Clicking any item expands it in-place or opens a side panel for editing rich text content.

## Command Palette & Keyboard Interaction

### Global Shortcut: `Cmd+K` / `Ctrl+K`

Opens the palette overlay from anywhere in the app.

### Search & Navigate (default mode)

- Start typing to fuzzy search across subjects, tasks, agenda points, minutes
- Results grouped by type, showing parent subject
- `Enter` to navigate to selected result
- Arrow keys or `j`/`k` to move through results

### Quick Create (prefix mode)

- `t: Buy new laptop @ProjectAlpha` — creates a task
- `a: Discuss budget @John` — creates an agenda point
- `m: Weekly standup @DesignTeam` — creates meeting minutes
- `s: New Client Project` — creates a new subject
- Subject name auto-completes after `@`
- If `@Subject` is omitted, prompts a subject picker
- `Enter` to confirm, `Escape` to cancel

### Command mode (`/` prefix)

- `/archive` — archive current subject
- `/done` — mark selected task as done
- `/pin` — pin/unpin current subject
- `/filter priority:high` — filter current view

### Navigation shortcuts (no palette)

- `Cmd+1` — go to Dashboard
- `Cmd+2` — focus Subject list sidebar
- `j` / `k` or Arrow Up / Arrow Down — move up/down in lists
- `Enter` — open/expand selected item
- `Escape` — close panel / go back
- `Tab` — cycle between Tasks / Agenda / Minutes tabs in subject view

## Rich Text Editor

- **Tiptap** (open source, MIT licensed) — built on ProseMirror
- Features: bold, italic, strikethrough, bullet list, numbered list, headings, links, code blocks
- Floating toolbar appears on text selection
- Markdown shortcuts supported: `**bold**`, `- list item`, `# heading`
- Consistent editor used everywhere: task descriptions, agenda content, meeting minutes

## UI & Visual Style

**Warm & friendly** aesthetic:

- Rounded corners (`border-radius: 12px`)
- Soft color palette: warm grays, muted accent colors per subject
- Quasar Material components as base, customized with SCSS overrides
- Smooth transitions on expand/collapse
- Comfortable spacing, readable typography

### Key Components

- **Subject Card** — color dot, name, badge, pin icon, date range
- **Task Item** — checkbox, rich title, priority dot, due date pill (color-coded: overdue=red, today=orange, upcoming=neutral)
- **Agenda Point Item** — resolved toggle, rich title, expandable content
- **Meeting Minutes Item** — date + title card, click to open full editor

## Error Handling & Edge Cases

### Data Integrity

- All writes to Dexie/IndexedDB are transactional (rollback on failure)
- Auto-save on rich text fields with ~500ms debounce — no "save" button
- Timestamps on all records for future sync/conflict detection

### Deletion

- No hard deletes — subjects get archived, items get soft-deleted
- Undo toast shown for a few seconds after any delete action
- Archived subjects recoverable from settings/archive view

### Empty States

- Dashboard with no subjects: onboarding prompt — "Create your first subject"
- Subject with no items: contextual hint per tab — "Press Cmd+K then t: to add a task"
- Search with no results: "Nothing found" with suggestion to create

### Command Palette Edge Cases

- Unknown prefix: show help text — "Try t: for task, a: for agenda, m: for minutes, s: for subject"
- Missing `@Subject`: prompt subject picker inline
- Typo in subject name: fuzzy match with "Did you mean @ProjectAlpha?"

### Storage

- Monitor IndexedDB quota, warn if approaching limits (rare for text data)
- 100% offline — no loading spinners waiting on network

## Testing Strategy

### Unit Tests

- Data layer: Dexie CRUD operations for all entity types
- Pinia stores: state management logic, computed properties, dashboard filters/sorting
- Command palette parser: prefix parsing, subject extraction, fuzzy matching

### Component Tests

- Key components: subject list, task item, agenda item, minutes editor
- Command palette: keyboard navigation, create flows, search results
- Tiptap editor: renders, basic formatting works

### E2E Tests

- Core workflows: create subject → add task → mark done
- Command palette: `Cmd+K` → `t: Something @Subject` → verify created
- Dashboard: verify time-bucketed views show correct items
