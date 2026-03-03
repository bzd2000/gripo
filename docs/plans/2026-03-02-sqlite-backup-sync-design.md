# SQLite Backup Sync (Electron)

## Problem

Gripo stores all data in browser IndexedDB via Dexie. If the browser clears storage, all data is lost. Users need a durable local backup that persists independently of the browser.

## Decision

Mirror every Dexie mutation to a local SQLite file via Electron IPC. SQLite is a write-through backup — not a primary database. IndexedDB remains the working copy; SQLite is the safety net.

## Architecture

```
Renderer Process (Vue app)
  Dexie hooks (creating / updating / deleting)
    -> ipcRenderer.send('db:sync', { table, op, id?, data })

Main Process (Electron)
  ipcMain.on('db:sync', handler)
    -> better-sqlite3 write to user-chosen .db file
```

- **Dexie/IndexedDB**: primary database, all reads come from here
- **SQLite** (`better-sqlite3`): durable backup in main process, write-only during normal operation
- **Sync trigger**: every individual mutation (not full-table dumps)
- **IPC**: fire-and-forget from renderer (async, non-blocking)

## Sync Behavior

### Per-record sync (not full table)

Each Dexie hook fires with the specific record:

- **`creating` hook** -> `INSERT INTO {table} (...) VALUES (...)`
- **`updating` hook** -> `UPDATE {table} SET ... WHERE id = ?`
- **`deleting` hook** -> `DELETE FROM {table} WHERE id = ?` (hard delete — app uses soft deletes via `update` for tasks/agenda/minutes; the `deleting` hook only fires on true row removals)

IPC payload shape:

```ts
{ table: 'tasks', op: 'create', data: { id: 5, subjectId: 1, title: '...', ... } }
{ table: 'tasks', op: 'update', id: 5, data: { status: 'done', updatedAt: '...' } }
{ table: 'tasks', op: 'update', id: 5, data: { deleted: 1, updatedAt: '...' } }
```

### No automatic restore

SQLite is a backup only. The user explicitly triggers "Restore from backup" when needed (e.g. after browser storage is cleared). No merge logic — restore replaces all IndexedDB data.

## SQLite Schema

Mirrors Dexie exactly. Dates as ISO 8601 strings, booleans as integers (0/1).

```sql
CREATE TABLE IF NOT EXISTS subjects (
  id INTEGER PRIMARY KEY,
  name TEXT, type TEXT, color TEXT,
  pinned INTEGER, archived INTEGER,
  startDate TEXT, endDate TEXT,
  createdAt TEXT, updatedAt TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY,
  subjectId INTEGER, title TEXT, description TEXT,
  status TEXT, priority TEXT, dueDate TEXT,
  deleted INTEGER, createdAt TEXT, updatedAt TEXT
);

CREATE TABLE IF NOT EXISTS agendaPoints (
  id INTEGER PRIMARY KEY,
  subjectId INTEGER, title TEXT, content TEXT,
  resolved INTEGER, deleted INTEGER,
  createdAt TEXT, updatedAt TEXT
);

CREATE TABLE IF NOT EXISTS meetingMinutes (
  id INTEGER PRIMARY KEY,
  subjectId INTEGER, title TEXT, content TEXT,
  date TEXT, deleted INTEGER,
  createdAt TEXT, updatedAt TEXT
);
```

## File Path

- User picks the `.db` file location on first launch via `dialog.showSaveDialogSync`
- Path stored in a config file at `app.getPath('userData')/config.json`
- Settings UI lets user change path or trigger restore

## File Changes

### Electron main process (`src-electron/electron-main.ts`)
- Initialize `better-sqlite3` connection to user-chosen path
- Create tables if they don't exist
- Handle `db:sync` IPC channel
- Handle `db:restore` IPC channel (read all tables, return to renderer)
- Handle `db:get-path` / `db:set-path` IPC channels

### Electron preload (`src-electron/electron-preload.ts`)
- Expose `window.electronAPI.dbSync(payload)` via `contextBridge`
- Expose `window.electronAPI.dbRestore()` — returns all SQLite data
- Expose `window.electronAPI.dbGetPath()` / `dbSetPath(path)`

### Database (`src/db/database.ts`)
- Register Dexie hooks on all 4 tables after construction
- Each hook calls `window.electronAPI.dbSync(...)` if available (feature-detect)
- ~30 lines of generic hook registration code

### Settings UI (new component or page)
- Show current backup file path
- "Change backup location" button
- "Restore from backup" button with confirmation dialog

### Dependencies
- `better-sqlite3` — native SQLite binding for Node.js (Electron main process)

## Maintainability

- **New table**: register one hook + add `CREATE TABLE` to schema init
- **New column**: no sync code changes (hooks send full records); add column to SQLite schema
- **No store or component changes**: sync lives entirely in database.ts + Electron files
- **Risk**: fire-and-forget IPC means a main process crash could lose one mutation in SQLite (acceptable for backup use case)

## Not in scope

- Cloud sync
- Multi-device sync
- Conflict resolution
- Automatic restore on startup
- Browser (non-Electron) support for SQLite sync
