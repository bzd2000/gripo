import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useTaskStore } from '../task-store';
import { db } from 'src/db/database';

describe('useTaskStore', () => {
  beforeEach(async () => {
    setActivePinia(createPinia());
    await db.delete();
    await db.open();
  });

  it('loads tasks for a subject', async () => {
    const store = useTaskStore();
    await store.loadTasksForSubject(1);
    expect(store.tasks).toEqual([]);
  });

  it('creates a task', async () => {
    const store = useTaskStore();
    await store.createTask({
      subjectId: 1,
      title: 'Buy supplies',
      priority: 'medium',
    });
    await store.loadTasksForSubject(1);
    expect(store.tasks).toHaveLength(1);
    expect(store.tasks[0].title).toBe('Buy supplies');
    expect(store.tasks[0].status).toBe('todo');
  });

  it('updates task status', async () => {
    const store = useTaskStore();
    await store.createTask({ subjectId: 1, title: 'Test', priority: 'low' });
    await store.loadTasksForSubject(1);
    const id = store.tasks[0].id!;
    await store.updateTask(id, { status: 'done' });
    expect(store.tasks[0].status).toBe('done');
  });

  it('soft-deletes a task', async () => {
    const store = useTaskStore();
    await store.createTask({ subjectId: 1, title: 'Delete me', priority: 'low' });
    await store.loadTasksForSubject(1);
    const id = store.tasks[0].id!;
    await store.deleteTask(id);
    expect(store.activeTasks).toHaveLength(0);
  });

  it('loads tasks due today', async () => {
    const store = useTaskStore();
    const today = new Date();
    today.setHours(12, 0, 0, 0);
    await store.createTask({ subjectId: 1, title: 'Due today', priority: 'high', dueDate: today });
    await store.createTask({ subjectId: 1, title: 'No due date', priority: 'low' });
    await store.loadAllTasks();
    expect(store.tasksDueToday).toHaveLength(1);
    expect(store.tasksDueToday[0].title).toBe('Due today');
  });
});
