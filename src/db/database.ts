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
