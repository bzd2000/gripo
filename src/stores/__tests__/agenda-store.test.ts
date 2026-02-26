import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useAgendaStore } from '../agenda-store';
import { db } from 'src/db/database';

describe('useAgendaStore', () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    await db.delete();
    await db.open();
  });

  it('loads agenda points for a subject', async () => {
    const store = useAgendaStore();
    await store.loadForSubject(1);
    expect(store.agendaPoints).toEqual([]);
  });

  it('creates an agenda point', async () => {
    const store = useAgendaStore();
    await store.createAgendaPoint({ subjectId: 1, title: 'Discuss budget' });
    await store.loadForSubject(1);
    expect(store.agendaPoints).toHaveLength(1);
    expect(store.agendaPoints[0].title).toBe('Discuss budget');
    expect(store.agendaPoints[0].resolved).toBe(false);
  });

  it('resolves an agenda point', async () => {
    const store = useAgendaStore();
    await store.createAgendaPoint({ subjectId: 1, title: 'Budget' });
    await store.loadForSubject(1);
    const id = store.agendaPoints[0].id!;
    await store.toggleResolved(id);
    expect(store.agendaPoints[0].resolved).toBe(true);
  });

  it('filters unresolved agenda points', async () => {
    const store = useAgendaStore();
    await store.createAgendaPoint({ subjectId: 1, title: 'Open' });
    await store.createAgendaPoint({ subjectId: 1, title: 'Done' });
    await store.loadForSubject(1);
    const doneId = store.agendaPoints[1].id!;
    await store.toggleResolved(doneId);
    expect(store.unresolvedPoints).toHaveLength(1);
    expect(store.unresolvedPoints[0].title).toBe('Open');
  });

  it('loads all unresolved across subjects', async () => {
    const store = useAgendaStore();
    await store.createAgendaPoint({ subjectId: 1, title: 'Open 1' });
    await store.createAgendaPoint({ subjectId: 2, title: 'Open 2' });
    await store.createAgendaPoint({ subjectId: 1, title: 'Resolved' });
    // Resolve the third one
    await store.loadForSubject(1);
    const resolvedId = store.agendaPoints.find((a) => a.title === 'Resolved')!.id!;
    await store.toggleResolved(resolvedId);
    // Now load all unresolved
    await store.loadAllUnresolved();
    expect(store.agendaPoints).toHaveLength(2);
  });

  it('soft-deletes an agenda point', async () => {
    const store = useAgendaStore();
    await store.createAgendaPoint({ subjectId: 1, title: 'Delete me' });
    await store.loadForSubject(1);
    const id = store.agendaPoints[0].id!;
    await store.deleteAgendaPoint(id);
    expect(store.activePoints).toHaveLength(0);
  });
});
