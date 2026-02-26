# Gripo Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build Gripo — a personal task/project/planning app with subjects, tasks, agenda points, meeting minutes, command palette, and rich text editing.

**Architecture:** Vue 3 + Quasar with Pinia stores backed by Dexie.js (IndexedDB). Tiptap for rich text. Command palette as primary interaction. Warm & friendly visual style.

**Tech Stack:** Vue 3, Quasar 2, TypeScript, Pinia, Tiptap (MIT), Dexie.js, Vitest, Vue Test Utils

**Design Doc:** `docs/plans/2026-02-26-gripo-design.md`

---

## Phase 1: Foundation

### Task 1: Install dependencies

**Files:**
- Modify: `package.json`

**Step 1: Install runtime dependencies**

Run: `cd /Users/bzd/Projects/gripo && pnpm add dexie @tiptap/vue-3 @tiptap/starter-kit @tiptap/extension-link @tiptap/extension-placeholder`

**Step 2: Install test dependencies**

Run: `pnpm add -D vitest @vue/test-utils happy-dom`

**Step 3: Commit**

```bash
git add package.json pnpm-lock.yaml
git commit -m "chore: add dexie, tiptap, and vitest dependencies"
```

---

### Task 2: Configure Vitest

**Files:**
- Create: `vitest.config.ts`
- Modify: `package.json` (test script)
- Create: `src/__tests__/setup.ts`

**Step 1: Create vitest config**

Create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    setupFiles: ['src/__tests__/setup.ts'],
    include: ['src/**/*.{test,spec}.ts'],
  },
  resolve: {
    alias: {
      src: fileURLToPath(new URL('./src', import.meta.url)),
      components: fileURLToPath(new URL('./src/components', import.meta.url)),
      layouts: fileURLToPath(new URL('./src/layouts', import.meta.url)),
      pages: fileURLToPath(new URL('./src/pages', import.meta.url)),
      stores: fileURLToPath(new URL('./src/stores', import.meta.url)),
      boot: fileURLToPath(new URL('./src/boot', import.meta.url)),
    },
  },
});
```

**Step 2: Create test setup file**

Create `src/__tests__/setup.ts`:

```typescript
// Global test setup
import 'fake-indexeddb/auto';
```

Note: We need `fake-indexeddb` for Dexie in tests:

Run: `pnpm add -D fake-indexeddb`

**Step 3: Update package.json test script**

Change `"test": "echo \"No test specified\" && exit 0"` to `"test": "vitest run"`.

**Step 4: Verify test setup works**

Create a trivial test `src/__tests__/sanity.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';

describe('sanity', () => {
  it('works', () => {
    expect(1 + 1).toBe(2);
  });
});
```

Run: `pnpm test`
Expected: 1 test passes.

**Step 5: Commit**

```bash
git add vitest.config.ts src/__tests__/setup.ts src/__tests__/sanity.test.ts package.json pnpm-lock.yaml
git commit -m "chore: configure vitest with happy-dom and fake-indexeddb"
```

---

### Task 3: Define TypeScript models

**Files:**
- Create: `src/models/types.ts`
- Delete content from: `src/components/models.ts` (replace with re-export)

**Step 1: Create the type definitions**

Create `src/models/types.ts`:

```typescript
export type SubjectType = 'project' | 'person' | 'team' | 'board' | 'other';
export type TaskStatus = 'todo' | 'in-progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface Subject {
  id?: number;
  name: string;
  type: SubjectType;
  color: string;
  pinned: boolean;
  archived: boolean;
  startDate?: Date;
  endDate?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface Task {
  id?: number;
  subjectId: number;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate?: Date;
  deleted: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface AgendaPoint {
  id?: number;
  subjectId: number;
  title: string;
  content: string;
  resolved: boolean;
  deleted: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface MeetingMinutes {
  id?: number;
  subjectId: number;
  title: string;
  content: string;
  date: Date;
  deleted: boolean;
  createdAt: Date;
  updatedAt: Date;
}
```

**Step 2: Update components/models.ts to re-export**

Replace content of `src/components/models.ts`:

```typescript
export type { Subject, Task, AgendaPoint, MeetingMinutes } from 'src/models/types';
export type { SubjectType, TaskStatus, TaskPriority } from 'src/models/types';
```

**Step 3: Commit**

```bash
git add src/models/types.ts src/components/models.ts
git commit -m "feat: define TypeScript models for subjects, tasks, agenda, minutes"
```

---

## Phase 2: Data Layer

### Task 4: Create Dexie database

**Files:**
- Create: `src/db/database.ts`
- Create: `src/db/__tests__/database.test.ts`

**Step 1: Write the failing test**

Create `src/db/__tests__/database.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { db } from '../database';

describe('GripoDB', () => {
  beforeEach(async () => {
    await db.delete();
    await db.open();
  });

  it('has subjects table', () => {
    expect(db.subjects).toBeDefined();
  });

  it('has tasks table', () => {
    expect(db.tasks).toBeDefined();
  });

  it('has agendaPoints table', () => {
    expect(db.agendaPoints).toBeDefined();
  });

  it('has meetingMinutes table', () => {
    expect(db.meetingMinutes).toBeDefined();
  });

  it('can add and retrieve a subject', async () => {
    const id = await db.subjects.add({
      name: 'Test Project',
      type: 'project',
      color: '#4A90D9',
      pinned: false,
      archived: false,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    const subject = await db.subjects.get(id);
    expect(subject?.name).toBe('Test Project');
    expect(subject?.type).toBe('project');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `pnpm test -- src/db/__tests__/database.test.ts`
Expected: FAIL — module not found.

**Step 3: Write the database implementation**

Create `src/db/database.ts`:

```typescript
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
```

**Step 4: Run test to verify it passes**

Run: `pnpm test -- src/db/__tests__/database.test.ts`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/db/database.ts src/db/__tests__/database.test.ts
git commit -m "feat: create Dexie database with subjects, tasks, agenda, minutes tables"
```

---

### Task 5: Create Subject Pinia store

**Files:**
- Create: `src/stores/subject-store.ts`
- Create: `src/stores/__tests__/subject-store.test.ts`

**Step 1: Write the failing tests**

Create `src/stores/__tests__/subject-store.test.ts`:

```typescript
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
```

**Step 2: Run test to verify it fails**

Run: `pnpm test -- src/stores/__tests__/subject-store.test.ts`
Expected: FAIL — module not found.

**Step 3: Implement the store**

Create `src/stores/subject-store.ts`:

```typescript
import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { db } from 'src/db/database';
import type { Subject, SubjectType } from 'src/models/types';

export const useSubjectStore = defineStore('subjects', () => {
  const subjects = ref<Subject[]>([]);

  const activeSubjects = computed(() =>
    subjects.value.filter((s) => !s.archived)
  );

  const pinnedSubjects = computed(() =>
    subjects.value.filter((s) => s.pinned && !s.archived)
  );

  async function loadSubjects() {
    subjects.value = await db.subjects.toArray();
  }

  async function createSubject(data: {
    name: string;
    type: SubjectType;
    color: string;
    startDate?: Date;
    endDate?: Date;
  }) {
    const now = new Date();
    const id = await db.subjects.add({
      ...data,
      pinned: false,
      archived: false,
      createdAt: now,
      updatedAt: now,
    });
    await loadSubjects();
    return id;
  }

  async function updateSubject(id: number, data: Partial<Subject>) {
    await db.subjects.update(id, { ...data, updatedAt: new Date() });
    await loadSubjects();
  }

  async function archiveSubject(id: number) {
    await updateSubject(id, { archived: true });
  }

  async function togglePin(id: number) {
    const subject = subjects.value.find((s) => s.id === id);
    if (subject) {
      await updateSubject(id, { pinned: !subject.pinned });
    }
  }

  return {
    subjects,
    activeSubjects,
    pinnedSubjects,
    loadSubjects,
    createSubject,
    updateSubject,
    archiveSubject,
    togglePin,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useSubjectStore, import.meta.hot));
}
```

**Step 4: Run tests to verify they pass**

Run: `pnpm test -- src/stores/__tests__/subject-store.test.ts`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/stores/subject-store.ts src/stores/__tests__/subject-store.test.ts
git commit -m "feat: add subject Pinia store with CRUD, archive, and pin"
```

---

### Task 6: Create Task Pinia store

**Files:**
- Create: `src/stores/task-store.ts`
- Create: `src/stores/__tests__/task-store.test.ts`

**Step 1: Write the failing tests**

Create `src/stores/__tests__/task-store.test.ts`:

```typescript
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
```

**Step 2: Run test to verify it fails**

Run: `pnpm test -- src/stores/__tests__/task-store.test.ts`
Expected: FAIL.

**Step 3: Implement the store**

Create `src/stores/task-store.ts`:

```typescript
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

  async function loadTasksForSubject(subjectId: number) {
    tasks.value = await db.tasks.where('subjectId').equals(subjectId).toArray();
  }

  async function loadAllTasks() {
    allTasks.value = await db.tasks.where('deleted').equals(0).toArray();
  }

  async function createTask(data: {
    subjectId: number;
    title: string;
    priority: TaskPriority;
    description?: string;
    dueDate?: Date;
  }) {
    const now = new Date();
    await db.tasks.add({
      subjectId: data.subjectId,
      title: data.title,
      description: data.description ?? '',
      status: 'todo',
      priority: data.priority,
      dueDate: data.dueDate,
      deleted: false,
      createdAt: now,
      updatedAt: now,
    });
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
```

**Step 4: Run tests to verify they pass**

Run: `pnpm test -- src/stores/__tests__/task-store.test.ts`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/stores/task-store.ts src/stores/__tests__/task-store.test.ts
git commit -m "feat: add task Pinia store with CRUD and date-bucketed getters"
```

---

### Task 7: Create Agenda Point Pinia store

**Files:**
- Create: `src/stores/agenda-store.ts`
- Create: `src/stores/__tests__/agenda-store.test.ts`

**Step 1: Write the failing tests**

Create `src/stores/__tests__/agenda-store.test.ts`:

```typescript
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

  it('soft-deletes an agenda point', async () => {
    const store = useAgendaStore();
    await store.createAgendaPoint({ subjectId: 1, title: 'Delete me' });
    await store.loadForSubject(1);
    const id = store.agendaPoints[0].id!;
    await store.deleteAgendaPoint(id);
    expect(store.activePoints).toHaveLength(0);
  });
});
```

**Step 2: Run test to verify it fails**

Run: `pnpm test -- src/stores/__tests__/agenda-store.test.ts`
Expected: FAIL.

**Step 3: Implement the store**

Create `src/stores/agenda-store.ts`:

```typescript
import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { db } from 'src/db/database';
import type { AgendaPoint } from 'src/models/types';

export const useAgendaStore = defineStore('agenda', () => {
  const agendaPoints = ref<AgendaPoint[]>([]);

  const activePoints = computed(() =>
    agendaPoints.value.filter((a) => !a.deleted)
  );

  const unresolvedPoints = computed(() =>
    agendaPoints.value.filter((a) => !a.deleted && !a.resolved)
  );

  async function loadForSubject(subjectId: number) {
    agendaPoints.value = await db.agendaPoints
      .where('subjectId')
      .equals(subjectId)
      .toArray();
  }

  async function loadAllUnresolved() {
    agendaPoints.value = await db.agendaPoints
      .where('deleted')
      .equals(0)
      .filter((a) => !a.resolved)
      .toArray();
  }

  async function createAgendaPoint(data: {
    subjectId: number;
    title: string;
    content?: string;
  }) {
    const now = new Date();
    await db.agendaPoints.add({
      subjectId: data.subjectId,
      title: data.title,
      content: data.content ?? '',
      resolved: false,
      deleted: false,
      createdAt: now,
      updatedAt: now,
    });
  }

  async function updateAgendaPoint(id: number, data: Partial<AgendaPoint>) {
    await db.agendaPoints.update(id, { ...data, updatedAt: new Date() });
    const point = await db.agendaPoints.get(id);
    if (point) {
      await loadForSubject(point.subjectId);
    }
  }

  async function toggleResolved(id: number) {
    const point = agendaPoints.value.find((a) => a.id === id);
    if (point) {
      await updateAgendaPoint(id, { resolved: !point.resolved });
    }
  }

  async function deleteAgendaPoint(id: number) {
    await updateAgendaPoint(id, { deleted: true });
  }

  return {
    agendaPoints,
    activePoints,
    unresolvedPoints,
    loadForSubject,
    loadAllUnresolved,
    createAgendaPoint,
    updateAgendaPoint,
    toggleResolved,
    deleteAgendaPoint,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAgendaStore, import.meta.hot));
}
```

**Step 4: Run tests to verify they pass**

Run: `pnpm test -- src/stores/__tests__/agenda-store.test.ts`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/stores/agenda-store.ts src/stores/__tests__/agenda-store.test.ts
git commit -m "feat: add agenda point Pinia store with CRUD and resolve toggle"
```

---

### Task 8: Create Meeting Minutes Pinia store

**Files:**
- Create: `src/stores/minutes-store.ts`
- Create: `src/stores/__tests__/minutes-store.test.ts`

**Step 1: Write the failing tests**

Create `src/stores/__tests__/minutes-store.test.ts`:

```typescript
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
```

**Step 2: Run test to verify it fails**

Run: `pnpm test -- src/stores/__tests__/minutes-store.test.ts`
Expected: FAIL.

**Step 3: Implement the store**

Create `src/stores/minutes-store.ts`:

```typescript
import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { db } from 'src/db/database';
import type { MeetingMinutes } from 'src/models/types';

export const useMinutesStore = defineStore('minutes', () => {
  const minutes = ref<MeetingMinutes[]>([]);

  const activeMinutes = computed(() =>
    minutes.value.filter((m) => !m.deleted)
  );

  const sortedMinutes = computed(() =>
    [...activeMinutes.value].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    )
  );

  async function loadForSubject(subjectId: number) {
    minutes.value = await db.meetingMinutes
      .where('subjectId')
      .equals(subjectId)
      .toArray();
  }

  async function loadRecent(limit = 10) {
    minutes.value = await db.meetingMinutes
      .where('deleted')
      .equals(0)
      .reverse()
      .sortBy('date');
    minutes.value = minutes.value.slice(0, limit);
  }

  async function createMinutes(data: {
    subjectId: number;
    title: string;
    date: Date;
    content?: string;
  }) {
    const now = new Date();
    await db.meetingMinutes.add({
      subjectId: data.subjectId,
      title: data.title,
      content: data.content ?? '',
      date: data.date,
      deleted: false,
      createdAt: now,
      updatedAt: now,
    });
  }

  async function updateMinutes(id: number, data: Partial<MeetingMinutes>) {
    await db.meetingMinutes.update(id, { ...data, updatedAt: new Date() });
    const item = await db.meetingMinutes.get(id);
    if (item) {
      await loadForSubject(item.subjectId);
    }
  }

  async function deleteMinutes(id: number) {
    await updateMinutes(id, { deleted: true });
  }

  return {
    minutes,
    activeMinutes,
    sortedMinutes,
    loadForSubject,
    loadRecent,
    createMinutes,
    updateMinutes,
    deleteMinutes,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useMinutesStore, import.meta.hot));
}
```

**Step 4: Run tests to verify they pass**

Run: `pnpm test -- src/stores/__tests__/minutes-store.test.ts`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/stores/minutes-store.ts src/stores/__tests__/minutes-store.test.ts
git commit -m "feat: add meeting minutes Pinia store with CRUD and date sorting"
```

---

## Phase 3: Layout & Navigation Shell

### Task 9: Clean up scaffolding and set up routes

**Files:**
- Modify: `src/router/routes.ts`
- Delete: `src/components/ExampleComponent.vue`
- Delete: `src/components/EssentialLink.vue`
- Delete: `src/stores/example-store.ts`
- Create: `src/pages/DashboardPage.vue` (placeholder)
- Create: `src/pages/SubjectPage.vue` (placeholder)

**Step 1: Remove template files**

Delete `src/components/ExampleComponent.vue`, `src/components/EssentialLink.vue`, and `src/stores/example-store.ts`.

**Step 2: Create placeholder pages**

Create `src/pages/DashboardPage.vue`:

```vue
<template>
  <q-page class="q-pa-md">
    <h5 class="q-mt-none">Dashboard</h5>
  </q-page>
</template>

<script setup lang="ts">
//
</script>
```

Create `src/pages/SubjectPage.vue`:

```vue
<template>
  <q-page class="q-pa-md">
    <h5 class="q-mt-none">Subject</h5>
  </q-page>
</template>

<script setup lang="ts">
//
</script>
```

**Step 3: Update routes**

Replace content of `src/router/routes.ts`:

```typescript
import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '', name: 'dashboard', component: () => import('pages/DashboardPage.vue') },
      { path: 'subject/:id', name: 'subject', component: () => import('pages/SubjectPage.vue'), props: true },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;
```

**Step 4: Delete IndexPage.vue**

Delete `src/pages/IndexPage.vue` (replaced by DashboardPage).

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: replace scaffolding with dashboard/subject routes and pages"
```

---

### Task 10: Build MainLayout with subject sidebar

**Files:**
- Modify: `src/layouts/MainLayout.vue`

**Step 1: Replace MainLayout**

Replace content of `src/layouts/MainLayout.vue`:

```vue
<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />
        <q-toolbar-title>Gripo</q-toolbar-title>
        <q-btn flat dense round icon="search" aria-label="Command palette" @click="openCommandPalette">
          <q-tooltip>Cmd+K</q-tooltip>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered class="bg-grey-1">
      <q-list>
        <q-item clickable :to="{ name: 'dashboard' }" active-class="text-primary">
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>Dashboard</q-item-section>
        </q-item>

        <q-separator class="q-my-sm" />

        <q-item-label header class="text-weight-bold">Subjects</q-item-label>

        <q-item
          v-for="subject in activeSubjects"
          :key="subject.id"
          clickable
          :to="{ name: 'subject', params: { id: subject.id } }"
          active-class="text-primary"
        >
          <q-item-section avatar>
            <q-badge :style="{ backgroundColor: subject.color }" rounded />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ subject.name }}</q-item-label>
          </q-item-section>
          <q-item-section side v-if="subject.pinned">
            <q-icon name="push_pin" size="xs" color="grey" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useSubjectStore } from 'stores/subject-store';
import { storeToRefs } from 'pinia';

const subjectStore = useSubjectStore();
const { activeSubjects } = storeToRefs(subjectStore);

const leftDrawerOpen = ref(false);

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

function openCommandPalette() {
  // Will be implemented in Task 13
}

onMounted(async () => {
  await subjectStore.loadSubjects();
});
</script>
```

**Step 2: Verify the app loads**

Run: `pnpm dev`
Expected: App opens with "Gripo" header, left sidebar with "Dashboard" link and "Subjects" section. No errors in console.

**Step 3: Commit**

```bash
git add src/layouts/MainLayout.vue
git commit -m "feat: build MainLayout with subject sidebar and navigation"
```

---

## Phase 4: Subject Detail View

### Task 11: Build SubjectPage with tabs

**Files:**
- Modify: `src/pages/SubjectPage.vue`
- Create: `src/components/TaskList.vue`
- Create: `src/components/AgendaList.vue`
- Create: `src/components/MinutesList.vue`

**Step 1: Create TaskList component**

Create `src/components/TaskList.vue`:

```vue
<template>
  <div>
    <q-list separator v-if="activeTasks.length">
      <q-item v-for="task in activeTasks" :key="task.id" class="rounded-borders q-my-xs">
        <q-item-section side>
          <q-checkbox
            :model-value="task.status === 'done'"
            @update:model-value="toggleDone(task)"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label :class="{ 'text-strike text-grey': task.status === 'done' }">
            <span v-html="task.title" />
          </q-item-label>
        </q-item-section>
        <q-item-section side>
          <q-badge
            :color="priorityColor(task.priority)"
            :label="task.priority"
            rounded
          />
        </q-item-section>
        <q-item-section side v-if="task.dueDate">
          <q-badge
            :color="dueDateColor(task.dueDate)"
            :label="formatDate(task.dueDate)"
            outline
            rounded
          />
        </q-item-section>
      </q-item>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No tasks yet. Press Cmd+K then type t: to add one.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useTaskStore } from 'stores/task-store';
import { storeToRefs } from 'pinia';
import type { Task, TaskPriority } from 'src/models/types';

const taskStore = useTaskStore();
const { activeTasks } = storeToRefs(taskStore);

function priorityColor(priority: TaskPriority): string {
  const colors: Record<TaskPriority, string> = {
    high: 'red-4',
    medium: 'orange-4',
    low: 'grey-4',
  };
  return colors[priority];
}

function dueDateColor(date: Date): string {
  const now = new Date();
  const d = new Date(date);
  now.setHours(0, 0, 0, 0);
  d.setHours(0, 0, 0, 0);
  if (d < now) return 'red';
  if (d.getTime() === now.getTime()) return 'orange';
  return 'grey';
}

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString();
}

async function toggleDone(task: Task) {
  const newStatus = task.status === 'done' ? 'todo' : 'done';
  await taskStore.updateTask(task.id!, { status: newStatus });
}
</script>
```

**Step 2: Create AgendaList component**

Create `src/components/AgendaList.vue`:

```vue
<template>
  <div>
    <q-list separator v-if="activePoints.length">
      <q-item v-for="point in activePoints" :key="point.id" class="rounded-borders q-my-xs">
        <q-item-section side>
          <q-checkbox
            :model-value="point.resolved"
            @update:model-value="toggleResolved(point)"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label :class="{ 'text-strike text-grey': point.resolved }">
            <span v-html="point.title" />
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No agenda points. Press Cmd+K then type a: to add one.
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAgendaStore } from 'stores/agenda-store';
import { storeToRefs } from 'pinia';
import type { AgendaPoint } from 'src/models/types';

const agendaStore = useAgendaStore();
const { activePoints } = storeToRefs(agendaStore);

async function toggleResolved(point: AgendaPoint) {
  await agendaStore.toggleResolved(point.id!);
}
</script>
```

**Step 3: Create MinutesList component**

Create `src/components/MinutesList.vue`:

```vue
<template>
  <div>
    <q-list separator v-if="sortedMinutes.length">
      <q-item
        v-for="item in sortedMinutes"
        :key="item.id"
        clickable
        class="rounded-borders q-my-xs"
        @click="$emit('select', item)"
      >
        <q-item-section>
          <q-item-label>
            <span v-html="item.title" />
          </q-item-label>
          <q-item-label caption>
            {{ formatDate(item.date) }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No meeting minutes. Press Cmd+K then type m: to add one.
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMinutesStore } from 'stores/minutes-store';
import { storeToRefs } from 'pinia';

defineEmits<{
  select: [item: import('src/models/types').MeetingMinutes];
}>();

const minutesStore = useMinutesStore();
const { sortedMinutes } = storeToRefs(minutesStore);

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString();
}
</script>
```

**Step 4: Build SubjectPage with tabs**

Replace `src/pages/SubjectPage.vue`:

```vue
<template>
  <q-page class="q-pa-md">
    <div v-if="subject" class="column">
      <div class="row items-center q-mb-md">
        <q-badge :style="{ backgroundColor: subject.color }" rounded class="q-mr-sm" />
        <h5 class="q-mt-none q-mb-none">{{ subject.name }}</h5>
        <q-space />
        <q-btn
          flat
          round
          :icon="subject.pinned ? 'push_pin' : 'o_push_pin'"
          @click="togglePin"
        />
      </div>

      <q-tabs v-model="activeTab" dense align="left" class="text-primary">
        <q-tab name="tasks" label="Tasks" />
        <q-tab name="agenda" label="Agenda" />
        <q-tab name="minutes" label="Minutes" />
      </q-tabs>

      <q-separator />

      <q-tab-panels v-model="activeTab" animated>
        <q-tab-panel name="tasks">
          <TaskList />
        </q-tab-panel>
        <q-tab-panel name="agenda">
          <AgendaList />
        </q-tab-panel>
        <q-tab-panel name="minutes">
          <MinutesList @select="openMinutes" />
        </q-tab-panel>
      </q-tab-panels>
    </div>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      Subject not found.
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import { useSubjectStore } from 'stores/subject-store';
import { useTaskStore } from 'stores/task-store';
import { useAgendaStore } from 'stores/agenda-store';
import { useMinutesStore } from 'stores/minutes-store';
import type { Subject, MeetingMinutes } from 'src/models/types';
import TaskList from 'components/TaskList.vue';
import AgendaList from 'components/AgendaList.vue';
import MinutesList from 'components/MinutesList.vue';

const route = useRoute();
const subjectStore = useSubjectStore();
const taskStore = useTaskStore();
const agendaStore = useAgendaStore();
const minutesStore = useMinutesStore();

const subject = ref<Subject | undefined>();
const activeTab = ref('tasks');

async function loadSubject(id: number) {
  await subjectStore.loadSubjects();
  subject.value = subjectStore.subjects.find((s) => s.id === id);
  if (subject.value) {
    await Promise.all([
      taskStore.loadTasksForSubject(id),
      agendaStore.loadForSubject(id),
      minutesStore.loadForSubject(id),
    ]);
  }
}

async function togglePin() {
  if (subject.value?.id) {
    await subjectStore.togglePin(subject.value.id);
    subject.value = subjectStore.subjects.find((s) => s.id === subject.value!.id);
  }
}

function openMinutes(item: MeetingMinutes) {
  // Will be implemented with rich text editor in Task 14
  console.log('Open minutes:', item.id);
}

watch(
  () => route.params.id,
  (id) => {
    if (id) loadSubject(Number(id));
  },
  { immediate: true }
);
</script>
```

**Step 5: Commit**

```bash
git add src/pages/SubjectPage.vue src/components/TaskList.vue src/components/AgendaList.vue src/components/MinutesList.vue
git commit -m "feat: build subject detail page with tasks, agenda, and minutes tabs"
```

---

## Phase 5: Dashboard

### Task 12: Build DashboardPage

**Files:**
- Modify: `src/pages/DashboardPage.vue`

**Step 1: Implement the dashboard**

Replace `src/pages/DashboardPage.vue`:

```vue
<template>
  <q-page class="q-pa-md">
    <h5 class="q-mt-none q-mb-md">Dashboard</h5>

    <!-- Today -->
    <DashboardSection title="Today" icon="today" :items="tasksDueToday" empty-text="Nothing due today." />

    <!-- This Week -->
    <DashboardSection title="This Week" icon="date_range" :items="tasksDueThisWeek" empty-text="Nothing else this week." />

    <!-- Next Week -->
    <DashboardSection title="Next Week" icon="event" :items="tasksDueNextWeek" empty-text="Nothing next week." />

    <!-- Ongoing Subjects -->
    <div class="q-mb-md" v-if="ongoingSubjects.length">
      <div class="row items-center q-mb-sm">
        <q-icon name="timelapse" class="q-mr-sm" />
        <span class="text-weight-bold">Ongoing</span>
      </div>
      <q-card
        v-for="subject in ongoingSubjects"
        :key="subject.id"
        flat
        bordered
        class="q-mb-sm rounded-borders cursor-pointer"
        @click="goToSubject(subject.id!)"
      >
        <q-card-section horizontal>
          <q-badge :style="{ backgroundColor: subject.color }" rounded class="q-ml-md self-center" />
          <q-card-section>
            <div class="text-subtitle2">{{ subject.name }}</div>
            <div class="text-caption text-grey" v-if="subject.startDate && subject.endDate">
              {{ formatDate(subject.startDate) }} — {{ formatDate(subject.endDate) }}
            </div>
          </q-card-section>
        </q-card-section>
      </q-card>
    </div>

    <!-- Pinned Subjects -->
    <div class="q-mb-md" v-if="pinnedSubjects.length">
      <div class="row items-center q-mb-sm">
        <q-icon name="push_pin" class="q-mr-sm" />
        <span class="text-weight-bold">Pinned</span>
      </div>
      <q-card
        v-for="subject in pinnedSubjects"
        :key="subject.id"
        flat
        bordered
        class="q-mb-sm rounded-borders cursor-pointer"
        @click="goToSubject(subject.id!)"
      >
        <q-card-section horizontal>
          <q-badge :style="{ backgroundColor: subject.color }" rounded class="q-ml-md self-center" />
          <q-card-section>
            <div class="text-subtitle2">{{ subject.name }}</div>
          </q-card-section>
        </q-card-section>
      </q-card>
    </div>

    <!-- Empty state -->
    <div v-if="isEmpty" class="text-grey-6 q-pa-xl text-center">
      <q-icon name="rocket_launch" size="48px" class="q-mb-md" />
      <div class="text-h6">Welcome to Gripo</div>
      <div>Press <kbd>Cmd+K</kbd> then type <code>s: My First Project</code> to create your first subject.</div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSubjectStore } from 'stores/subject-store';
import { useTaskStore } from 'stores/task-store';
import { storeToRefs } from 'pinia';
import DashboardSection from 'components/DashboardSection.vue';

const router = useRouter();
const subjectStore = useSubjectStore();
const taskStore = useTaskStore();

const { activeSubjects, pinnedSubjects } = storeToRefs(subjectStore);
const { tasksDueToday, tasksDueThisWeek, tasksDueNextWeek } = storeToRefs(taskStore);

const ongoingSubjects = computed(() =>
  activeSubjects.value.filter((s) => {
    if (!s.startDate || !s.endDate) return false;
    const now = new Date();
    return new Date(s.startDate) <= now && new Date(s.endDate) >= now;
  })
);

const isEmpty = computed(
  () =>
    tasksDueToday.value.length === 0 &&
    tasksDueThisWeek.value.length === 0 &&
    tasksDueNextWeek.value.length === 0 &&
    ongoingSubjects.value.length === 0 &&
    pinnedSubjects.value.length === 0
);

function goToSubject(id: number) {
  router.push({ name: 'subject', params: { id } });
}

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString();
}

onMounted(async () => {
  await Promise.all([
    subjectStore.loadSubjects(),
    taskStore.loadAllTasks(),
  ]);
});
</script>
```

**Step 2: Create DashboardSection component**

Create `src/components/DashboardSection.vue`:

```vue
<template>
  <div class="q-mb-md" v-if="items.length">
    <div class="row items-center q-mb-sm">
      <q-icon :name="icon" class="q-mr-sm" />
      <span class="text-weight-bold">{{ title }}</span>
    </div>
    <q-card flat bordered class="rounded-borders">
      <q-list separator>
        <q-item v-for="task in items" :key="task.id" clickable @click="goToSubject(task.subjectId)">
          <q-item-section side>
            <q-checkbox
              :model-value="task.status === 'done'"
              @update:model-value="toggleDone(task)"
            />
          </q-item-section>
          <q-item-section>
            <q-item-label>
              <span v-html="task.title" />
            </q-item-label>
            <q-item-label caption>{{ subjectName(task.subjectId) }}</q-item-label>
          </q-item-section>
          <q-item-section side>
            <q-badge
              :color="priorityColor(task.priority)"
              :label="task.priority"
              rounded
            />
          </q-item-section>
        </q-item>
      </q-list>
    </q-card>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useSubjectStore } from 'stores/subject-store';
import { useTaskStore } from 'stores/task-store';
import type { Task, TaskPriority } from 'src/models/types';

defineProps<{
  title: string;
  icon: string;
  items: Task[];
  emptyText: string;
}>();

const router = useRouter();
const subjectStore = useSubjectStore();
const taskStore = useTaskStore();

function subjectName(subjectId: number): string {
  const subject = subjectStore.subjects.find((s) => s.id === subjectId);
  return subject?.name ?? 'Unknown';
}

function priorityColor(priority: TaskPriority): string {
  const colors: Record<TaskPriority, string> = {
    high: 'red-4',
    medium: 'orange-4',
    low: 'grey-4',
  };
  return colors[priority];
}

function goToSubject(subjectId: number) {
  router.push({ name: 'subject', params: { id: subjectId } });
}

async function toggleDone(task: Task) {
  const newStatus = task.status === 'done' ? 'todo' : 'done';
  await taskStore.updateTask(task.id!, { status: newStatus });
  await taskStore.loadAllTasks();
}
</script>
```

**Step 3: Commit**

```bash
git add src/pages/DashboardPage.vue src/components/DashboardSection.vue
git commit -m "feat: build dashboard with time-bucketed tasks, ongoing and pinned subjects"
```

---

## Phase 6: Command Palette

### Task 13: Build command palette component

**Files:**
- Create: `src/components/CommandPalette.vue`
- Create: `src/composables/useCommandPalette.ts`
- Create: `src/composables/__tests__/useCommandPalette.test.ts`
- Modify: `src/layouts/MainLayout.vue` (wire up)

**Step 1: Write the failing tests for the parser**

Create `src/composables/__tests__/useCommandPalette.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { parseCommand } from '../useCommandPalette';

describe('parseCommand', () => {
  it('parses task creation', () => {
    const result = parseCommand('t: Buy supplies @ProjectAlpha');
    expect(result).toEqual({
      type: 'create',
      entityType: 'task',
      title: 'Buy supplies',
      subjectName: 'ProjectAlpha',
    });
  });

  it('parses agenda creation', () => {
    const result = parseCommand('a: Discuss budget @John');
    expect(result).toEqual({
      type: 'create',
      entityType: 'agenda',
      title: 'Discuss budget',
      subjectName: 'John',
    });
  });

  it('parses minutes creation', () => {
    const result = parseCommand('m: Weekly standup @DesignTeam');
    expect(result).toEqual({
      type: 'create',
      entityType: 'minutes',
      title: 'Weekly standup',
      subjectName: 'DesignTeam',
    });
  });

  it('parses subject creation', () => {
    const result = parseCommand('s: New Client Project');
    expect(result).toEqual({
      type: 'create',
      entityType: 'subject',
      title: 'New Client Project',
      subjectName: undefined,
    });
  });

  it('parses task without subject', () => {
    const result = parseCommand('t: Buy supplies');
    expect(result).toEqual({
      type: 'create',
      entityType: 'task',
      title: 'Buy supplies',
      subjectName: undefined,
    });
  });

  it('returns search for plain text', () => {
    const result = parseCommand('budget meeting');
    expect(result).toEqual({
      type: 'search',
      query: 'budget meeting',
    });
  });

  it('parses command mode', () => {
    const result = parseCommand('/done');
    expect(result).toEqual({
      type: 'command',
      command: 'done',
      args: '',
    });
  });

  it('parses command with args', () => {
    const result = parseCommand('/filter priority:high');
    expect(result).toEqual({
      type: 'command',
      command: 'filter',
      args: 'priority:high',
    });
  });
});
```

**Step 2: Run test to verify it fails**

Run: `pnpm test -- src/composables/__tests__/useCommandPalette.test.ts`
Expected: FAIL.

**Step 3: Implement the parser**

Create `src/composables/useCommandPalette.ts`:

```typescript
export type ParsedCreate = {
  type: 'create';
  entityType: 'task' | 'agenda' | 'minutes' | 'subject';
  title: string;
  subjectName: string | undefined;
};

export type ParsedSearch = {
  type: 'search';
  query: string;
};

export type ParsedCommand = {
  type: 'command';
  command: string;
  args: string;
};

export type ParsedInput = ParsedCreate | ParsedSearch | ParsedCommand;

const PREFIXES: Record<string, ParsedCreate['entityType']> = {
  't:': 'task',
  'a:': 'agenda',
  'm:': 'minutes',
  's:': 'subject',
};

export function parseCommand(input: string): ParsedInput {
  const trimmed = input.trim();

  // Command mode
  if (trimmed.startsWith('/')) {
    const parts = trimmed.slice(1).split(/\s+/);
    return {
      type: 'command',
      command: parts[0],
      args: parts.slice(1).join(' '),
    };
  }

  // Create mode
  for (const [prefix, entityType] of Object.entries(PREFIXES)) {
    if (trimmed.startsWith(prefix)) {
      const rest = trimmed.slice(prefix.length).trim();
      const subjectMatch = rest.match(/@(\S+)\s*$/);
      const title = subjectMatch
        ? rest.slice(0, subjectMatch.index).trim()
        : rest;
      return {
        type: 'create',
        entityType,
        title,
        subjectName: subjectMatch?.[1],
      };
    }
  }

  // Search mode
  return {
    type: 'search',
    query: trimmed,
  };
}
```

**Step 4: Run tests to verify they pass**

Run: `pnpm test -- src/composables/__tests__/useCommandPalette.test.ts`
Expected: All tests PASS.

**Step 5: Build the CommandPalette Vue component**

Create `src/components/CommandPalette.vue`:

```vue
<template>
  <q-dialog v-model="isOpen" position="top" seamless>
    <q-card class="command-palette" style="width: 600px; max-width: 90vw; margin-top: 80px;">
      <q-card-section class="q-pb-none">
        <q-input
          ref="inputRef"
          v-model="query"
          placeholder="Search, create (t: a: m: s:), or command (/)"
          dense
          outlined
          autofocus
          @keydown.down.prevent="moveDown"
          @keydown.up.prevent="moveUp"
          @keydown.enter.prevent="executeSelected"
          @keydown.escape.prevent="close"
        >
          <template #prepend>
            <q-icon name="search" />
          </template>
        </q-input>
      </q-card-section>

      <q-card-section class="q-pt-sm" v-if="results.length">
        <q-list dense>
          <q-item
            v-for="(result, index) in results"
            :key="result.id"
            clickable
            :active="index === selectedIndex"
            active-class="bg-blue-1"
            @click="executeResult(result)"
            @mouseover="selectedIndex = index"
          >
            <q-item-section avatar>
              <q-icon :name="result.icon" size="sm" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ result.label }}</q-item-label>
              <q-item-label caption v-if="result.caption">{{ result.caption }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>

      <q-card-section v-else-if="query && parsed.type === 'create'" class="text-center text-grey-6">
        Press Enter to create {{ parsed.entityType }}: "{{ parsed.title }}"
        <span v-if="!parsed.subjectName && parsed.entityType !== 'subject'">
          (select a subject)
        </span>
      </q-card-section>

      <q-card-section v-else-if="query" class="text-center text-grey-6">
        No results. Try t: a: m: s: to create.
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { parseCommand, type ParsedInput } from 'src/composables/useCommandPalette';
import { useSubjectStore } from 'stores/subject-store';
import { useTaskStore } from 'stores/task-store';
import { useAgendaStore } from 'stores/agenda-store';
import { useMinutesStore } from 'stores/minutes-store';
import { db } from 'src/db/database';

interface SearchResult {
  id: string;
  icon: string;
  label: string;
  caption?: string;
  action: () => void;
}

const router = useRouter();
const subjectStore = useSubjectStore();
const taskStore = useTaskStore();
const agendaStore = useAgendaStore();
const minutesStore = useMinutesStore();

const isOpen = ref(false);
const query = ref('');
const selectedIndex = ref(0);
const inputRef = ref();

const parsed = computed<ParsedInput>(() => parseCommand(query.value));

const results = ref<SearchResult[]>([]);

watch(query, async (q) => {
  selectedIndex.value = 0;
  if (!q.trim()) {
    results.value = [];
    return;
  }

  const p = parsed.value;
  if (p.type === 'search') {
    results.value = await search(p.query);
  } else if (p.type === 'create' && p.entityType !== 'subject' && !p.subjectName) {
    // Show subjects to pick from
    results.value = subjectStore.activeSubjects.map((s) => ({
      id: `subject-${s.id}`,
      icon: 'folder',
      label: s.name,
      caption: `Create ${p.entityType} under ${s.name}`,
      action: () => createItem(p.entityType as 'task' | 'agenda' | 'minutes', p.title, s.id!),
    }));
  } else {
    results.value = [];
  }
});

async function search(q: string): Promise<SearchResult[]> {
  const lower = q.toLowerCase();
  const found: SearchResult[] = [];

  // Search subjects
  subjectStore.subjects
    .filter((s) => s.name.toLowerCase().includes(lower) && !s.archived)
    .forEach((s) => {
      found.push({
        id: `subject-${s.id}`,
        icon: 'folder',
        label: s.name,
        caption: s.type,
        action: () => {
          router.push({ name: 'subject', params: { id: s.id } });
          close();
        },
      });
    });

  // Search tasks
  const tasks = await db.tasks.filter(
    (t) => !t.deleted && t.title.toLowerCase().includes(lower)
  ).toArray();
  tasks.forEach((t) => {
    found.push({
      id: `task-${t.id}`,
      icon: 'check_box',
      label: t.title.replace(/<[^>]*>/g, ''),
      caption: subjectStore.subjects.find((s) => s.id === t.subjectId)?.name,
      action: () => {
        router.push({ name: 'subject', params: { id: t.subjectId } });
        close();
      },
    });
  });

  // Search agenda points
  const agendas = await db.agendaPoints.filter(
    (a) => !a.deleted && a.title.toLowerCase().includes(lower)
  ).toArray();
  agendas.forEach((a) => {
    found.push({
      id: `agenda-${a.id}`,
      icon: 'chat_bubble_outline',
      label: a.title.replace(/<[^>]*>/g, ''),
      caption: subjectStore.subjects.find((s) => s.id === a.subjectId)?.name,
      action: () => {
        router.push({ name: 'subject', params: { id: a.subjectId } });
        close();
      },
    });
  });

  return found;
}

async function createItem(entityType: 'task' | 'agenda' | 'minutes', title: string, subjectId: number) {
  if (entityType === 'task') {
    await taskStore.createTask({ subjectId, title, priority: 'medium' });
  } else if (entityType === 'agenda') {
    await agendaStore.createAgendaPoint({ subjectId, title });
  } else if (entityType === 'minutes') {
    await minutesStore.createMinutes({ subjectId, title, date: new Date() });
  }
  router.push({ name: 'subject', params: { id: subjectId } });
  close();
}

async function executeSelected() {
  const p = parsed.value;

  if (results.value.length > 0) {
    results.value[selectedIndex.value].action();
    return;
  }

  if (p.type === 'create') {
    if (p.entityType === 'subject') {
      const colors = ['#4A90D9', '#E67E22', '#2ECC71', '#9B59B6', '#E74C3C', '#1ABC9C'];
      const color = colors[Math.floor(Math.random() * colors.length)];
      await subjectStore.createSubject({ name: p.title, type: 'project', color });
      close();
      return;
    }

    if (p.subjectName) {
      const subject = subjectStore.activeSubjects.find(
        (s) => s.name.toLowerCase() === p.subjectName!.toLowerCase()
      );
      if (subject) {
        await createItem(p.entityType as 'task' | 'agenda' | 'minutes', p.title, subject.id!);
      }
    }
  }
}

function moveDown() {
  if (selectedIndex.value < results.value.length - 1) {
    selectedIndex.value++;
  }
}

function moveUp() {
  if (selectedIndex.value > 0) {
    selectedIndex.value--;
  }
}

function executeResult(result: SearchResult) {
  result.action();
}

function open() {
  query.value = '';
  results.value = [];
  selectedIndex.value = 0;
  isOpen.value = true;
  nextTick(() => inputRef.value?.focus());
}

function close() {
  isOpen.value = false;
  query.value = '';
}

function handleKeydown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
    event.preventDefault();
    if (isOpen.value) {
      close();
    } else {
      open();
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});

defineExpose({ open, close });
</script>

<style lang="scss" scoped>
.command-palette {
  border-radius: 12px;
}
</style>
```

**Step 6: Wire command palette into MainLayout**

Add to `src/layouts/MainLayout.vue`:

In template, add before closing `</q-layout>`:
```vue
<CommandPalette ref="commandPaletteRef" />
```

In script, add:
```typescript
import CommandPalette from 'components/CommandPalette.vue';

const commandPaletteRef = ref<InstanceType<typeof CommandPalette>>();

function openCommandPalette() {
  commandPaletteRef.value?.open();
}
```

**Step 7: Commit**

```bash
git add src/composables/useCommandPalette.ts src/composables/__tests__/useCommandPalette.test.ts src/components/CommandPalette.vue src/layouts/MainLayout.vue
git commit -m "feat: build command palette with search, quick create, and keyboard navigation"
```

---

## Phase 7: Rich Text Editor

### Task 14: Create TiptapEditor component

**Files:**
- Create: `src/components/TiptapEditor.vue`

**Step 1: Create the editor component**

Create `src/components/TiptapEditor.vue`:

```vue
<template>
  <div class="tiptap-editor">
    <BubbleMenu :editor="editor" :tippy-options="{ duration: 100 }" v-if="editor">
      <q-btn-group flat>
        <q-btn
          flat
          dense
          icon="format_bold"
          :class="{ 'text-primary': editor.isActive('bold') }"
          @click="editor.chain().focus().toggleBold().run()"
        />
        <q-btn
          flat
          dense
          icon="format_italic"
          :class="{ 'text-primary': editor.isActive('italic') }"
          @click="editor.chain().focus().toggleItalic().run()"
        />
        <q-btn
          flat
          dense
          icon="strikethrough_s"
          :class="{ 'text-primary': editor.isActive('strike') }"
          @click="editor.chain().focus().toggleStrike().run()"
        />
        <q-btn
          flat
          dense
          icon="format_list_bulleted"
          :class="{ 'text-primary': editor.isActive('bulletList') }"
          @click="editor.chain().focus().toggleBulletList().run()"
        />
        <q-btn
          flat
          dense
          icon="format_list_numbered"
          :class="{ 'text-primary': editor.isActive('orderedList') }"
          @click="editor.chain().focus().toggleOrderedList().run()"
        />
        <q-btn
          flat
          dense
          icon="code"
          :class="{ 'text-primary': editor.isActive('codeBlock') }"
          @click="editor.chain().focus().toggleCodeBlock().run()"
        />
      </q-btn-group>
    </BubbleMenu>
    <EditorContent :editor="editor" />
  </div>
</template>

<script setup lang="ts">
import { watch, onBeforeUnmount } from 'vue';
import { useEditor, EditorContent, BubbleMenu } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';

const props = withDefaults(defineProps<{
  modelValue: string;
  placeholder?: string;
}>(), {
  placeholder: 'Start typing...',
});

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Link.configure({ openOnClick: false }),
    Placeholder.configure({ placeholder: props.placeholder }),
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML());
  },
});

watch(
  () => props.modelValue,
  (value) => {
    if (editor.value && editor.value.getHTML() !== value) {
      editor.value.commands.setContent(value, false);
    }
  }
);

onBeforeUnmount(() => {
  editor.value?.destroy();
});
</script>

<style lang="scss">
.tiptap-editor {
  .ProseMirror {
    min-height: 100px;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    outline: none;

    &:focus {
      border-color: var(--q-primary);
    }

    p.is-editor-empty:first-child::before {
      content: attr(data-placeholder);
      float: left;
      color: #adb5bd;
      pointer-events: none;
      height: 0;
    }
  }
}
</style>
```

**Step 2: Commit**

```bash
git add src/components/TiptapEditor.vue
git commit -m "feat: create TiptapEditor component with bubble menu and markdown shortcuts"
```

---

### Task 15: Integrate TiptapEditor into item detail views

**Files:**
- Create: `src/components/TaskDetail.vue`
- Create: `src/components/AgendaDetail.vue`
- Create: `src/components/MinutesDetail.vue`
- Modify: `src/components/TaskList.vue`
- Modify: `src/components/AgendaList.vue`
- Modify: `src/components/MinutesList.vue`

**Step 1: Create TaskDetail component**

Create `src/components/TaskDetail.vue`:

```vue
<template>
  <q-card flat bordered class="rounded-borders q-mb-sm">
    <q-card-section>
      <TiptapEditor v-model="localTitle" placeholder="Task title..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption text-grey q-mb-xs">Description</div>
      <TiptapEditor v-model="localDescription" placeholder="Add a description..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-actions>
      <q-btn flat label="Close" @click="$emit('close')" />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useTaskStore } from 'stores/task-store';
import type { Task } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ task: Task }>();
defineEmits<{ close: [] }>();

const taskStore = useTaskStore();

const localTitle = ref(props.task.title);
const localDescription = ref(props.task.description);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    await taskStore.updateTask(props.task.id!, {
      title: localTitle.value,
      description: localDescription.value,
    });
  }, 500);
}

watch(() => props.task, (t) => {
  localTitle.value = t.title;
  localDescription.value = t.description;
});
</script>
```

**Step 2: Create AgendaDetail component**

Create `src/components/AgendaDetail.vue`:

```vue
<template>
  <q-card flat bordered class="rounded-borders q-mb-sm">
    <q-card-section>
      <TiptapEditor v-model="localTitle" placeholder="Agenda point..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption text-grey q-mb-xs">Notes</div>
      <TiptapEditor v-model="localContent" placeholder="Add notes..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-actions>
      <q-btn flat label="Close" @click="$emit('close')" />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useAgendaStore } from 'stores/agenda-store';
import type { AgendaPoint } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ agendaPoint: AgendaPoint }>();
defineEmits<{ close: [] }>();

const agendaStore = useAgendaStore();

const localTitle = ref(props.agendaPoint.title);
const localContent = ref(props.agendaPoint.content);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    await agendaStore.updateAgendaPoint(props.agendaPoint.id!, {
      title: localTitle.value,
      content: localContent.value,
    });
  }, 500);
}

watch(() => props.agendaPoint, (a) => {
  localTitle.value = a.title;
  localContent.value = a.content;
});
</script>
```

**Step 3: Create MinutesDetail component**

Create `src/components/MinutesDetail.vue`:

```vue
<template>
  <q-card flat bordered class="rounded-borders q-mb-sm">
    <q-card-section>
      <TiptapEditor v-model="localTitle" placeholder="Meeting title..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption text-grey q-mb-xs">Minutes</div>
      <TiptapEditor v-model="localContent" placeholder="Write your meeting notes..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-actions>
      <q-btn flat label="Close" @click="$emit('close')" />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useMinutesStore } from 'stores/minutes-store';
import type { MeetingMinutes } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ minutes: MeetingMinutes }>();
defineEmits<{ close: [] }>();

const minutesStore = useMinutesStore();

const localTitle = ref(props.minutes.title);
const localContent = ref(props.minutes.content);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(async () => {
    await minutesStore.updateMinutes(props.minutes.id!, {
      title: localTitle.value,
      content: localContent.value,
    });
  }, 500);
}

watch(() => props.minutes, (m) => {
  localTitle.value = m.title;
  localContent.value = m.content;
});
</script>
```

**Step 4: Update TaskList, AgendaList, MinutesList to show detail on click**

Add expandable detail to each list component. In each list, add a `selectedId` ref, toggle it on click, and render the corresponding detail component when expanded.

For `TaskList.vue`, add:
```vue
<!-- After the q-item, add: -->
<TaskDetail v-if="selectedId === task.id" :task="task" @close="selectedId = undefined" />
```

Similarly for `AgendaList.vue` and `MinutesList.vue`.

**Step 5: Commit**

```bash
git add src/components/TaskDetail.vue src/components/AgendaDetail.vue src/components/MinutesDetail.vue src/components/TaskList.vue src/components/AgendaList.vue src/components/MinutesList.vue
git commit -m "feat: integrate TiptapEditor into task, agenda, and minutes detail views"
```

---

## Phase 8: Keyboard Navigation

### Task 16: Add keyboard navigation composable

**Files:**
- Create: `src/composables/useKeyboardNav.ts`
- Modify: `src/layouts/MainLayout.vue`

**Step 1: Create keyboard navigation composable**

Create `src/composables/useKeyboardNav.ts`:

```typescript
import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

export function useKeyboardNav() {
  const router = useRouter();

  function handleKeydown(event: KeyboardEvent) {
    // Skip if typing in an input/editor
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable ||
      target.closest('.ProseMirror')
    ) {
      return;
    }

    // Cmd+1 = Dashboard
    if ((event.metaKey || event.ctrlKey) && event.key === '1') {
      event.preventDefault();
      router.push({ name: 'dashboard' });
      return;
    }

    // Escape = go back / close
    if (event.key === 'Escape') {
      event.preventDefault();
      router.back();
      return;
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeydown);
  });

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown);
  });
}
```

**Step 2: Wire into MainLayout**

Add to `src/layouts/MainLayout.vue` script:

```typescript
import { useKeyboardNav } from 'src/composables/useKeyboardNav';

useKeyboardNav();
```

**Step 3: Commit**

```bash
git add src/composables/useKeyboardNav.ts src/layouts/MainLayout.vue
git commit -m "feat: add keyboard navigation with Cmd+1 for dashboard and Escape to go back"
```

---

## Phase 9: Styling

### Task 17: Apply warm & friendly theme

**Files:**
- Modify: `src/css/app.scss`
- Modify: `quasar.config.ts` (framework config for colors)

**Step 1: Set Quasar brand colors**

In `quasar.config.ts`, update the framework config:

```typescript
framework: {
  config: {
    brand: {
      primary: '#5C6BC0',
      secondary: '#FF8A65',
      accent: '#26A69A',
      positive: '#66BB6A',
      negative: '#EF5350',
      info: '#42A5F5',
      warning: '#FFA726',
    },
  },
  plugins: ['Notify'],
},
```

**Step 2: Add global styles**

Replace `src/css/app.scss`:

```scss
// Gripo — warm & friendly theme

body {
  font-family: 'Roboto', sans-serif;
  background-color: #fafafa;
}

// Rounded corners everywhere
.q-card {
  border-radius: 12px !important;
}

.q-btn {
  border-radius: 8px !important;
}

.q-dialog .q-card {
  border-radius: 12px !important;
}

// Comfortable spacing for list items
.q-item {
  border-radius: 8px;
  margin: 2px 0;
}

// Tabs styling
.q-tabs {
  .q-tab {
    border-radius: 8px 8px 0 0;
  }
}

// Keyboard shortcut hint
kbd {
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 0.85em;
  font-family: monospace;
}

// Badge as color dot
.q-badge {
  min-height: 12px;
  min-width: 12px;
}
```

**Step 3: Commit**

```bash
git add src/css/app.scss quasar.config.ts
git commit -m "style: apply warm and friendly theme with rounded corners and soft colors"
```

---

## Phase 10: Final Cleanup

### Task 18: Remove sanity test and clean up old models

**Files:**
- Delete: `src/__tests__/sanity.test.ts`
- Modify: `src/components/models.ts`

**Step 1: Remove sanity test**

Delete `src/__tests__/sanity.test.ts`.

**Step 2: Update models.ts**

Replace `src/components/models.ts`:

```typescript
export type {
  Subject,
  Task,
  AgendaPoint,
  MeetingMinutes,
  SubjectType,
  TaskStatus,
  TaskPriority,
} from 'src/models/types';
```

**Step 3: Run all tests**

Run: `pnpm test`
Expected: All tests pass (database, stores, command palette parser).

**Step 4: Run lint**

Run: `pnpm lint`
Expected: No errors.

**Step 5: Commit**

```bash
git add -A
git commit -m "chore: clean up scaffolding and finalize initial implementation"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1. Foundation | 1-3 | Dependencies, Vitest, TypeScript models |
| 2. Data Layer | 4-8 | Dexie DB, 4 Pinia stores with tests |
| 3. Layout | 9-10 | Routes, MainLayout with sidebar |
| 4. Subject Detail | 11 | SubjectPage with tabs, list components |
| 5. Dashboard | 12 | Time-bucketed dashboard |
| 6. Command Palette | 13 | Parser, UI, keyboard shortcut |
| 7. Rich Text | 14-15 | TiptapEditor, detail views |
| 8. Keyboard Nav | 16 | Global shortcuts composable |
| 9. Styling | 17 | Warm & friendly theme |
| 10. Cleanup | 18 | Remove scaffolding, final checks |
