import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useSubjectStore } from '../subject-store';
import { db } from 'src/db/database';

describe('useSubjectStore', () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    await db.delete();
    await db.open();
  });

  it('starts with empty subjects', async () => {
    const store = useSubjectStore();
    await store.loadSubjects();
    expect(store.subjects).toEqual([]);
  });

  it('creates a subject', async () => {
    const store = useSubjectStore();
    await store.createSubject({ name: 'Project Alpha', type: 'project', color: '#4A90D9' });
    expect(store.subjects).toHaveLength(1);
    expect(store.subjects[0].name).toBe('Project Alpha');
  });

  it('updates a subject', async () => {
    const store = useSubjectStore();
    await store.createSubject({ name: 'Old Name', type: 'project', color: '#4A90D9' });
    const id = store.subjects[0].id!;
    await store.updateSubject(id, { name: 'New Name' });
    expect(store.subjects[0].name).toBe('New Name');
  });

  it('archives a subject', async () => {
    const store = useSubjectStore();
    await store.createSubject({ name: 'To Archive', type: 'project', color: '#4A90D9' });
    const id = store.subjects[0].id!;
    await store.archiveSubject(id);
    expect(store.activeSubjects).toHaveLength(0);
  });

  it('pins a subject', async () => {
    const store = useSubjectStore();
    await store.createSubject({ name: 'Pin Me', type: 'project', color: '#4A90D9' });
    const id = store.subjects[0].id!;
    await store.togglePin(id);
    expect(store.pinnedSubjects).toHaveLength(1);
  });
});
