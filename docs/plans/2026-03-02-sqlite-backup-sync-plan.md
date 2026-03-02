# SQLite Backup Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Mirror every Dexie mutation to a local SQLite file via Electron IPC, so users have a durable backup that survives browser storage clearing.

**Architecture:** Dexie hooks in the renderer fire IPC messages to the Electron main process on every create/update/delete. The main process writes to a `better-sqlite3` database at a user-chosen file path. Restore is user-initiated only.

**Tech Stack:** Dexie 4 hooks, Electron IPC (`contextBridge`), `better-sqlite3`, Quasar/Vue 3

---

### Task 1: Install better-sqlite3

**Files:**
- Modify: `package.json`
- Modify: `quasar.config.ts` (electron section)

**Step 1: Install the dependency**

Run: `npm install better-sqlite3`
Run: `npm install -D @types/better-sqlite3`

better-sqlite3 must be in `dependencies` (not devDependencies) so Electron can access it at runtime.

**Step 2: Mark as external in quasar config**

In `quasar.config.ts`, uncomment and configure the electron main esbuild config to externalize native modules:

```ts
// Inside the electron config object:
electron: {
  extendElectronMainConf(esbuildConf) {
    esbuildConf.external = esbuildConf.external || [];
    esbuildConf.external.push('better-sqlite3');
  },

  // ... rest of existing config
}
```

**Step 3: Rebuild native modules for Electron**

Run: `npx electron-rebuild`

If `electron-rebuild` is not installed:
Run: `npm install -D @electron/rebuild`
Run: `npx electron-rebuild`

**Step 4: Verify**

Run: `npx vue-tsc --noEmit`
Expected: No type errors

**Step 5: Commit**

```
git add package.json package-lock.json quasar.config.ts
git commit -m "chore: install better-sqlite3 for Electron SQLite backup"
```

---

### Task 2: Create SQLite service in Electron main process

**Files:**
- Create: `src-electron/sqlite-service.ts`

**Step 1: Write the SQLite service**

This module initializes the SQLite database, creates tables, and exposes sync/restore/config functions.

```ts
import Database from 'better-sqlite3';
import { app } from 'electron';
import fs from 'fs';
import path from 'path';

let db: Database.Database | null = null;

const configPath = path.join(app.getPath('userData'), 'config.json');

// --- Config ---

function readConfig(): { dbPath?: string } {
  try {
    return JSON.parse(fs.readFileSync(configPath, 'utf-8')) as { dbPath?: string };
  } catch {
    return {};
  }
}

function writeConfig(config: { dbPath?: string }) {
  fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
}

export function getDbPath(): string | undefined {
  return readConfig().dbPath;
}

export function setDbPath(dbPath: string) {
  close();
  writeConfig({ ...readConfig(), dbPath });
  init(dbPath);
}

// --- Init ---

export function init(dbPath: string) {
  db = new Database(dbPath);
  db.pragma('journal_mode = WAL');

  db.exec(`
    CREATE TABLE IF NOT EXISTS subjects (
      id INTEGER PRIMARY KEY,
      name TEXT, type TEXT, color TEXT,
      pinned INTEGER DEFAULT 0, archived INTEGER DEFAULT 0,
      startDate TEXT, endDate TEXT,
      createdAt TEXT, updatedAt TEXT
    );
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY,
      subjectId INTEGER, title TEXT, description TEXT,
      status TEXT, priority TEXT, dueDate TEXT,
      deleted INTEGER DEFAULT 0,
      createdAt TEXT, updatedAt TEXT
    );
    CREATE TABLE IF NOT EXISTS agendaPoints (
      id INTEGER PRIMARY KEY,
      subjectId INTEGER, title TEXT, content TEXT,
      resolved INTEGER DEFAULT 0, deleted INTEGER DEFAULT 0,
      createdAt TEXT, updatedAt TEXT
    );
    CREATE TABLE IF NOT EXISTS meetingMinutes (
      id INTEGER PRIMARY KEY,
      subjectId INTEGER, title TEXT, content TEXT,
      date TEXT, deleted INTEGER DEFAULT 0,
      createdAt TEXT, updatedAt TEXT
    );
  `);
}

export function close() {
  db?.close();
  db = null;
}

// --- Sync ---

interface SyncPayload {
  table: string;
  op: 'create' | 'update' | 'delete';
  id?: number;
  data?: Record<string, unknown>;
}

const VALID_TABLES = ['subjects', 'tasks', 'agendaPoints', 'meetingMinutes'];

function serializeValue(val: unknown): unknown {
  if (val instanceof Date) return val.toISOString();
  if (typeof val === 'boolean') return val ? 1 : 0;
  return val;
}

function serializeRecord(data: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(data)) {
    out[k] = serializeValue(v);
  }
  return out;
}

export function sync(payload: SyncPayload) {
  if (!db) return;
  if (!VALID_TABLES.includes(payload.table)) return;

  const table = payload.table;

  if (payload.op === 'create' && payload.data) {
    const data = serializeRecord(payload.data);
    const keys = Object.keys(data);
    const placeholders = keys.map(() => '?').join(', ');
    const stmt = db.prepare(
      `INSERT OR REPLACE INTO ${table} (${keys.join(', ')}) VALUES (${placeholders})`
    );
    stmt.run(...keys.map((k) => data[k]));
  }

  if (payload.op === 'update' && payload.id != null && payload.data) {
    const data = serializeRecord(payload.data);
    const sets = Object.keys(data).map((k) => `${k} = ?`).join(', ');
    const values = Object.values(data);
    const stmt = db.prepare(`UPDATE ${table} SET ${sets} WHERE id = ?`);
    stmt.run(...values, payload.id);
  }

  if (payload.op === 'delete' && payload.id != null) {
    const stmt = db.prepare(`DELETE FROM ${table} WHERE id = ?`);
    stmt.run(payload.id);
  }
}

// --- Restore ---

export function restore(): Record<string, unknown[]> {
  if (!db) return {};
  const result: Record<string, unknown[]> = {};
  for (const table of VALID_TABLES) {
    result[table] = db.prepare(`SELECT * FROM ${table}`).all();
  }
  return result;
}
```

**Step 2: Commit**

```
git add src-electron/sqlite-service.ts
git commit -m "feat: add SQLite service for Electron main process"
```

---

### Task 3: Wire up IPC handlers in Electron main process

**Files:**
- Modify: `src-electron/electron-main.ts`

**Step 1: Import and initialize the SQLite service**

Add the following to `electron-main.ts`. Import the service and dialog, initialize on app ready, register IPC handlers, prompt for DB path on first launch.

```ts
// Add to existing imports:
import { app, BrowserWindow, ipcMain, dialog } from 'electron';

// Add new import after existing imports:
import * as sqliteService from './sqlite-service.js';

// Inside the createWindow function, AFTER creating the BrowserWindow, add:

// --- SQLite backup init ---
let dbPath = sqliteService.getDbPath();
if (!dbPath) {
  const result = dialog.showSaveDialogSync(mainWindow, {
    title: 'Choose backup database location',
    defaultPath: path.join(app.getPath('documents'), 'gripo-backup.db'),
    filters: [{ name: 'SQLite Database', extensions: ['db'] }],
  });
  if (result) {
    dbPath = result;
    sqliteService.setDbPath(dbPath);
  }
}
if (dbPath) {
  sqliteService.init(dbPath);
}
```

Register IPC handlers outside `createWindow`, after `app.whenReady()`:

```ts
// --- IPC handlers ---

ipcMain.on('db:sync', (_event, payload) => {
  sqliteService.sync(payload);
});

ipcMain.handle('db:restore', () => {
  return sqliteService.restore();
});

ipcMain.handle('db:get-path', () => {
  return sqliteService.getDbPath();
});

ipcMain.handle('db:set-path', (_event, newPath: string) => {
  sqliteService.setDbPath(newPath);
});

ipcMain.handle('db:pick-path', async () => {
  const result = await dialog.showSaveDialog({
    title: 'Choose backup database location',
    defaultPath: path.join(app.getPath('documents'), 'gripo-backup.db'),
    filters: [{ name: 'SQLite Database', extensions: ['db'] }],
  });
  if (!result.canceled && result.filePath) {
    sqliteService.setDbPath(result.filePath);
    return result.filePath;
  }
  return null;
});
```

Add cleanup:
```ts
app.on('before-quit', () => {
  sqliteService.close();
});
```

**Step 2: Verify type-check**

Run: `npx vue-tsc --noEmit`
Expected: No type errors

**Step 3: Commit**

```
git add src-electron/electron-main.ts
git commit -m "feat: wire up SQLite IPC handlers in Electron main"
```

---

### Task 4: Set up preload script with contextBridge

**Files:**
- Modify: `src-electron/electron-preload.ts`
- Create: `src/electron-api.d.ts` (type declarations for window.electronAPI)

**Step 1: Implement the preload script**

Replace the template comments in `src-electron/electron-preload.ts` with:

```ts
import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  dbSync: (payload: { table: string; op: string; id?: number; data?: Record<string, unknown> }) => {
    ipcRenderer.send('db:sync', payload);
  },
  dbRestore: (): Promise<Record<string, unknown[]>> => {
    return ipcRenderer.invoke('db:restore');
  },
  dbGetPath: (): Promise<string | undefined> => {
    return ipcRenderer.invoke('db:get-path');
  },
  dbSetPath: (newPath: string): Promise<void> => {
    return ipcRenderer.invoke('db:set-path', newPath);
  },
  dbPickPath: (): Promise<string | null> => {
    return ipcRenderer.invoke('db:pick-path');
  },
});
```

**Step 2: Add type declarations**

Create `src/electron-api.d.ts`:

```ts
export interface ElectronAPI {
  dbSync: (payload: { table: string; op: string; id?: number; data?: Record<string, unknown> }) => void;
  dbRestore: () => Promise<Record<string, unknown[]>>;
  dbGetPath: () => Promise<string | undefined>;
  dbSetPath: (newPath: string) => Promise<void>;
  dbPickPath: () => Promise<string | null>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
```

**Step 3: Verify type-check**

Run: `npx vue-tsc --noEmit`
Expected: No type errors

**Step 4: Commit**

```
git add src-electron/electron-preload.ts src/electron-api.d.ts
git commit -m "feat: expose SQLite backup API via Electron preload"
```

---

### Task 5: Register Dexie hooks for sync

**Files:**
- Modify: `src/db/database.ts`

**Step 1: Add hook registration**

After the `GripoDB` class and `db` export, add a function that registers hooks on all tables. The hooks fire `window.electronAPI.dbSync(...)` if running in Electron.

```ts
// Add after: export const db = new GripoDB();

function registerSyncHooks() {
  if (!window.electronAPI) return;

  const tables = [
    { name: 'subjects', table: db.subjects },
    { name: 'tasks', table: db.tasks },
    { name: 'agendaPoints', table: db.agendaPoints },
    { name: 'meetingMinutes', table: db.meetingMinutes },
  ] as const;

  for (const { name, table } of tables) {
    table.hook('creating', function (_primKey, obj) {
      // obj.id may not be set yet for auto-increment; use onsuccess to get it
      this.onsuccess = (id: number) => {
        window.electronAPI!.dbSync({
          table: name,
          op: 'create',
          data: { ...obj, id },
        });
      };
    });

    table.hook('updating', (modifications, primKey) => {
      window.electronAPI!.dbSync({
        table: name,
        op: 'update',
        id: primKey as number,
        data: modifications,
      });
    });

    table.hook('deleting', (primKey) => {
      window.electronAPI!.dbSync({
        table: name,
        op: 'delete',
        id: primKey as number,
      });
    });
  }
}

registerSyncHooks();
```

Key details:
- `creating` hook uses `this.onsuccess` to get the auto-generated ID after insert
- `updating` hook receives `modifications` (only changed fields) and `primKey`
- `deleting` hook receives `primKey` (hard delete from IndexedDB; stores use soft delete via update, so this mostly catches edge cases)
- The `window.electronAPI` check means this is a no-op in browser mode

**Step 2: Verify type-check and lint**

Run: `npx vue-tsc --noEmit`
Run: `npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"`
Expected: No errors

**Step 3: Run existing tests**

Run: `npx vitest run`
Expected: All 34 tests pass (hooks are a no-op in test env since window.electronAPI is undefined)

**Step 4: Commit**

```
git add src/db/database.ts
git commit -m "feat: register Dexie hooks to sync mutations to SQLite"
```

---

### Task 6: Add settings page with backup path and restore

**Files:**
- Create: `src/pages/SettingsPage.vue`
- Modify: `src/router/routes.ts`
- Modify: `src/layouts/MainLayout.vue` (add settings link to sidebar)
- Modify: `src/css/app.scss` (add setting-row styles)

**Step 1: Check the router and layout files**

Read `src/router/routes.ts` and `src/layouts/MainLayout.vue` to understand the existing route and sidebar structure.

**Step 2: Create the settings page**

Create `src/pages/SettingsPage.vue`:

```vue
<template>
  <q-page class="q-pa-md">
    <div class="stagger-in">
      <div class="page-title">Settings</div>
      <div class="page-subtitle">Backup &amp; data</div>

      <div style="margin-top: 24px;">
        <div class="section-title">Backup database</div>

        <div class="setting-row">
          <div class="setting-label">Backup location</div>
          <div class="setting-value">
            <template v-if="dbPath">
              <code>{{ dbPath }}</code>
            </template>
            <template v-else>
              <span style="color: var(--g-text-muted);">Not configured</span>
            </template>
          </div>
          <q-btn
            v-if="hasElectron"
            flat dense size="sm" label="Change"
            @click="pickPath"
          />
        </div>

        <div class="setting-row" v-if="hasElectron" style="margin-top: 16px;">
          <div class="setting-label">Restore from backup</div>
          <div class="setting-value">
            <span style="color: var(--g-text-dim); font-size: 0.75rem;">
              Replaces all current data with the backup contents.
            </span>
          </div>
          <q-btn
            flat dense size="sm" label="Restore" color="red-4"
            @click="confirmRestore"
          />
        </div>
      </div>
    </div>

    <q-dialog v-model="showRestoreDialog">
      <q-card class="command-palette" style="width: 400px;">
        <q-card-section>
          <div style="color: var(--g-text-bright); font-size: 0.9rem; font-weight: 700;">
            Restore from backup?
          </div>
        </q-card-section>
        <q-card-section style="color: var(--g-text-secondary); font-size: 0.82rem;">
          This will replace all current data with the contents of your backup file.
          This action cannot be undone.
        </q-card-section>
        <q-card-actions align="right">
          <q-btn flat label="Cancel" color="grey-7" v-close-popup />
          <q-btn flat label="Restore" color="red-4" @click="doRestore" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { db } from 'src/db/database';

const hasElectron = ref(!!window.electronAPI);
const dbPath = ref<string | undefined>();
const showRestoreDialog = ref(false);

onMounted(async () => {
  if (window.electronAPI) {
    dbPath.value = await window.electronAPI.dbGetPath();
  }
});

async function pickPath() {
  if (!window.electronAPI) return;
  const newPath = await window.electronAPI.dbPickPath();
  if (newPath) {
    dbPath.value = newPath;
  }
}

function confirmRestore() {
  showRestoreDialog.value = true;
}

async function doRestore() {
  if (!window.electronAPI) return;
  showRestoreDialog.value = false;

  const data = await window.electronAPI.dbRestore();

  await db.transaction('rw', [db.subjects, db.tasks, db.agendaPoints, db.meetingMinutes], async () => {
    await db.subjects.clear();
    await db.tasks.clear();
    await db.agendaPoints.clear();
    await db.meetingMinutes.clear();

    if (data.subjects?.length) await db.subjects.bulkAdd(data.subjects as never[]);
    if (data.tasks?.length) await db.tasks.bulkAdd(data.tasks as never[]);
    if (data.agendaPoints?.length) await db.agendaPoints.bulkAdd(data.agendaPoints as never[]);
    if (data.meetingMinutes?.length) await db.meetingMinutes.bulkAdd(data.meetingMinutes as never[]);
  });

  window.location.reload();
}
</script>
```

**Step 3: Add route**

In `src/router/routes.ts`, add inside the layout children array:

```ts
{
  path: '/settings',
  name: 'settings',
  component: () => import('pages/SettingsPage.vue'),
}
```

**Step 4: Add sidebar link**

In `src/layouts/MainLayout.vue`, add a settings nav item at the bottom of the sidebar.

**Step 5: Add styles for settings rows**

In `src/css/app.scss`, add:

```scss
// --- Settings ---
.setting-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--g-border);

  .setting-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--g-text);
    min-width: 140px;
  }

  .setting-value {
    flex: 1;
    font-size: 0.78rem;
    color: var(--g-text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
  }
}
```

**Step 6: Verify type-check and lint**

Run: `npx vue-tsc --noEmit`
Run: `npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"`
Expected: No errors

**Step 7: Run tests**

Run: `npx vitest run`
Expected: All tests pass

**Step 8: Commit**

```
git add src/pages/SettingsPage.vue src/router/routes.ts src/layouts/MainLayout.vue src/css/app.scss
git commit -m "feat: add settings page with backup path and restore UI"
```

---

### Task 7: End-to-end verification in Electron

**Step 1: Start the Electron dev server**

Run: `npx quasar dev -m electron`

**Step 2: Verify first-launch dialog**

On first launch, a file picker dialog should appear asking where to save the backup database. Choose a location.

**Step 3: Verify sync**

1. Create a subject, then a task under it
2. Check the SQLite file exists at the chosen path
3. Verify data is in SQLite (open with any SQLite viewer)

**Step 4: Verify restore**

1. Open Settings page from sidebar
2. Verify the backup path is displayed
3. Clear IndexedDB via DevTools (Application > IndexedDB > GripoDB > Delete database)
4. Click "Restore" in Settings, confirm dialog
5. Verify all data reappears after page reload

**Step 5: Verify path change**

1. In Settings, click "Change" next to backup location
2. Pick a new path
3. Create a new item
4. Verify the new SQLite file has the data

**Step 6: Verify web mode still works**

Run: `npx quasar dev`
Expected: App runs normally, no errors (hooks are no-op without electronAPI)

**Step 7: Final commit if any fixes needed**

```
git add -A
git commit -m "fix: adjustments from e2e testing of SQLite backup"
```

---

## Verification Checklist

1. `npx vue-tsc --noEmit` — no type errors
2. `npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"` — no lint errors
3. `npx vitest run` — all tests pass
4. `npx quasar dev -m electron` — app launches, first-run dialog appears
5. Creating/updating/deleting items writes to SQLite in real time
6. Restore from backup replaces IndexedDB data correctly
7. Changing backup path works
8. Web mode (`npx quasar dev`) still works (hooks are no-op without electronAPI)
