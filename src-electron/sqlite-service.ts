import initSqlJs, { type Database } from 'sql.js';
import { app } from 'electron';
import fs from 'fs';
import path from 'path';

let db: Database | null = null;
let currentDbPath: string | null = null;

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

export async function setDbPath(dbPath: string) {
  close();
  writeConfig({ ...readConfig(), dbPath });
  await init(dbPath);
}

// --- Init ---

function save() {
  if (!db || !currentDbPath) return;
  const data = db.export();
  fs.writeFileSync(currentDbPath, Buffer.from(data));
}

export async function init(dbPath: string) {
  const SQL = await initSqlJs();

  if (fs.existsSync(dbPath)) {
    const fileBuffer = fs.readFileSync(dbPath);
    db = new SQL.Database(fileBuffer);
  } else {
    db = new SQL.Database();
  }
  currentDbPath = dbPath;

  db.run(`
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

  save();
}

export function close() {
  if (db) {
    save();
    db.close();
    db = null;
    currentDbPath = null;
  }
}

// --- Sync ---

interface SyncPayload {
  table: string;
  op: 'create' | 'update' | 'delete';
  id?: number;
  data?: Record<string, unknown>;
}

const VALID_TABLES = ['subjects', 'tasks', 'agendaPoints', 'meetingMinutes'];

const VALID_COLUMNS: Record<string, string[]> = {
  subjects: ['id', 'name', 'type', 'color', 'pinned', 'archived', 'startDate', 'endDate', 'createdAt', 'updatedAt'],
  tasks: ['id', 'subjectId', 'title', 'description', 'status', 'priority', 'dueDate', 'deleted', 'createdAt', 'updatedAt'],
  agendaPoints: ['id', 'subjectId', 'title', 'content', 'resolved', 'deleted', 'createdAt', 'updatedAt'],
  meetingMinutes: ['id', 'subjectId', 'title', 'content', 'date', 'deleted', 'createdAt', 'updatedAt'],
};

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
  const allowedCols = VALID_COLUMNS[table];
  if (!allowedCols) return;

  try {
    if (payload.op === 'create' && payload.data) {
      const data = serializeRecord(payload.data);
      const keys = Object.keys(data).filter((k) => allowedCols.includes(k));
      if (keys.length === 0) return;
      const placeholders = keys.map(() => '?').join(', ');
      db.run(
        `INSERT OR REPLACE INTO ${table} (${keys.join(', ')}) VALUES (${placeholders})`,
        keys.map((k) => data[k] as null | number | string),
      );
    }

    if (payload.op === 'update' && payload.id != null && payload.data) {
      const data = serializeRecord(payload.data);
      const keys = Object.keys(data).filter((k) => allowedCols.includes(k));
      if (keys.length === 0) return;
      const sets = keys.map((k) => `${k} = ?`).join(', ');
      const values = keys.map((k) => data[k] as null | number | string);
      db.run(`UPDATE ${table} SET ${sets} WHERE id = ?`, [...values, payload.id]);
    }

    if (payload.op === 'delete' && payload.id != null) {
      db.run(`DELETE FROM ${table} WHERE id = ?`, [payload.id]);
    }

    save();
  } catch (err) {
    console.error('[sqlite-service] sync error:', err);
  }
}

// --- Restore ---

export function restore(): Record<string, Record<string, unknown>[]> {
  if (!db) return {};
  const result: Record<string, Record<string, unknown>[]> = {};
  for (const table of VALID_TABLES) {
    const stmt = db.prepare(`SELECT * FROM ${table}`);
    const rows: Record<string, unknown>[] = [];
    while (stmt.step()) {
      rows.push(stmt.getAsObject() as Record<string, unknown>);
    }
    stmt.free();
    result[table] = rows;
  }
  return result;
}
