import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { db } from 'src/db/database';
import type { Task, TaskPriority } from 'src/models/types';

function startOfDay(date: Date): Date {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

function endOfDay(date: Date): Date {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d;
}

function startOfWeek(date: Date): Date {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day + (day === 0 ? -6 : 1); // Monday start
  d.setDate(diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function endOfWeek(date: Date): Date {
  const start = startOfWeek(date);
  const d = new Date(start);
  d.setDate(d.getDate() + 6);
  d.setHours(23, 59, 59, 999);
  return d;
}

export const useTaskStore = defineStore('tasks', () => {
  const tasks = ref<Task[]>([]);
  const allTasks = ref<Task[]>([]);

  const activeTasks = computed(() =>
    tasks.value.filter((t) => !t.deleted)
  );

  const tasksDueToday = computed(() => {
    const todayStart = startOfDay(new Date());
    const todayEnd = endOfDay(new Date());
    return allTasks.value.filter(
      (t) =>
        !t.deleted &&
        t.status !== 'done' &&
        t.dueDate &&
        t.dueDate >= todayStart &&
        t.dueDate <= todayEnd
    );
  });

  const tasksDueThisWeek = computed(() => {
    const weekStart = startOfWeek(new Date());
    const weekEnd = endOfWeek(new Date());
    const todayEnd = endOfDay(new Date());
    return allTasks.value.filter(
      (t) =>
        !t.deleted &&
        t.status !== 'done' &&
        t.dueDate &&
        t.dueDate > todayEnd &&
        t.dueDate >= weekStart &&
        t.dueDate <= weekEnd
    );
  });

  const tasksDueNextWeek = computed(() => {
    const nextWeekStart = new Date(startOfWeek(new Date()));
    nextWeekStart.setDate(nextWeekStart.getDate() + 7);
    const nextWeekEnd = new Date(nextWeekStart);
    nextWeekEnd.setDate(nextWeekEnd.getDate() + 6);
    nextWeekEnd.setHours(23, 59, 59, 999);
    return allTasks.value.filter(
      (t) =>
        !t.deleted &&
        t.status !== 'done' &&
        t.dueDate &&
        t.dueDate >= nextWeekStart &&
        t.dueDate <= nextWeekEnd
    );
  });

  const overdueTasks = computed(() => {
    const todayStart = startOfDay(new Date());
    return allTasks.value.filter(
      (t) =>
        !t.deleted &&
        t.status !== 'done' &&
        t.dueDate &&
        t.dueDate < todayStart
    );
  });

  async function loadTasksForSubject(subjectId: number) {
    tasks.value = await db.tasks.where('subjectId').equals(subjectId).toArray();
  }

  async function loadAllTasks() {
    allTasks.value = await db.tasks
      .filter((t) => !t.deleted)
      .toArray();
  }

  async function createTask(data: {
    subjectId: number;
    title: string;
    priority: TaskPriority;
    description?: string;
    dueDate?: Date;
  }) {
    const now = new Date();
    const task: Task = {
      subjectId: data.subjectId,
      title: data.title,
      description: data.description ?? '',
      status: 'todo',
      priority: data.priority,
      deleted: false,
      createdAt: now,
      updatedAt: now,
    };
    if (data.dueDate) {
      task.dueDate = data.dueDate;
    }
    await db.tasks.add(task);
  }

  async function updateTask(id: number, data: Partial<Task>) {
    await db.tasks.update(id, { ...data, updatedAt: new Date() });
    const task = await db.tasks.get(id);
    if (task) {
      await loadTasksForSubject(task.subjectId);
    }
  }

  async function deleteTask(id: number) {
    await updateTask(id, { deleted: true });
  }

  return {
    tasks,
    allTasks,
    activeTasks,
    tasksDueToday,
    tasksDueThisWeek,
    tasksDueNextWeek,
    overdueTasks,
    loadTasksForSubject,
    loadAllTasks,
    createTask,
    updateTask,
    deleteTask,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useTaskStore, import.meta.hot));
}
