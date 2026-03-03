import Dexie, { type Table } from 'dexie';
import type { Subject, Task, AgendaPoint, MeetingMinutes } from 'src/models/types';

export class GripoDB extends Dexie {
  subjects!: Table<Subject, number>;
  tasks!: Table<Task, number>;
  agendaPoints!: Table<AgendaPoint, number>;
  meetingMinutes!: Table<MeetingMinutes, number>;

  constructor() {
    super('GripoDB');

    this.version(1).stores({
      subjects: '++id, name, type, pinned, archived',
      tasks: '++id, subjectId, status, priority, dueDate, deleted',
      agendaPoints: '++id, subjectId, resolved, deleted',
      meetingMinutes: '++id, subjectId, date, deleted',
    });
  }
}

export const db = new GripoDB();

let syncPaused = false;
export function pauseSync() { syncPaused = true; }
export function resumeSync() { syncPaused = false; }

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
      if (syncPaused) return;
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
      if (syncPaused) return;
      window.electronAPI!.dbSync({
        table: name,
        op: 'update',
        id: primKey as number,
        data: modifications as Record<string, unknown>,
      });
    });

    table.hook('deleting', (primKey) => {
      if (syncPaused) return;
      window.electronAPI!.dbSync({
        table: name,
        op: 'delete',
        id: primKey as number,
      });
    });
  }
}

registerSyncHooks();
