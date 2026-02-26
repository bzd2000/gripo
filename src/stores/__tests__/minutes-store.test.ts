import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useMinutesStore } from '../minutes-store';
import { db } from 'src/db/database';

describe('useMinutesStore', () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    await db.delete();
    await db.open();
  });

  it('loads minutes for a subject', async () => {
    const store = useMinutesStore();
    await store.loadForSubject(1);
    expect(store.minutes).toEqual([]);
  });

  it('creates meeting minutes', async () => {
    const store = useMinutesStore();
    const date = new Date();
    await store.createMinutes({
      subjectId: 1,
      title: 'Weekly standup',
      date,
    });
    await store.loadForSubject(1);
    expect(store.minutes).toHaveLength(1);
    expect(store.minutes[0].title).toBe('Weekly standup');
  });

  it('updates minutes content', async () => {
    const store = useMinutesStore();
    await store.createMinutes({
      subjectId: 1,
      title: 'Standup',
      date: new Date(),
    });
    await store.loadForSubject(1);
    const id = store.minutes[0].id!;
    await store.updateMinutes(id, { content: '<p>Discussed roadmap</p>' });
    expect(store.minutes[0].content).toBe('<p>Discussed roadmap</p>');
  });

  it('soft-deletes minutes', async () => {
    const store = useMinutesStore();
    await store.createMinutes({
      subjectId: 1,
      title: 'Delete me',
      date: new Date(),
    });
    await store.loadForSubject(1);
    const id = store.minutes[0].id!;
    await store.deleteMinutes(id);
    expect(store.activeMinutes).toHaveLength(0);
  });

  it('sorts by date descending', async () => {
    const store = useMinutesStore();
    await store.createMinutes({ subjectId: 1, title: 'Older', date: new Date('2026-01-01') });
    await store.createMinutes({ subjectId: 1, title: 'Newer', date: new Date('2026-02-01') });
    await store.loadForSubject(1);
    expect(store.sortedMinutes[0].title).toBe('Newer');
    expect(store.sortedMinutes[1].title).toBe('Older');
  });
});
