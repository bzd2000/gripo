# Missing Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Complete all CRUD operations, data entry flows, and dashboard so Gripo is usable end-to-end.

**Architecture:** Bottom-up approach — build the reusable undo composable first, then quick-add bars, then enrich detail panels with editable fields and delete, then inline subject editing, then dashboard enhancements. All stores already have the backend methods; this is purely UI work.

**Tech Stack:** Vue 3 + Quasar (Notify plugin), Pinia stores, TypeScript strict mode, existing Dexie.js database.

---

### Task 1: Create useUndoAction composable

All delete/archive operations need an undo toast. Build this first so every subsequent task can use it.

**Files:**
- Create: `src/composables/useUndoAction.ts`

**Step 1: Create the composable**

```typescript
// src/composables/useUndoAction.ts
import { Notify } from 'quasar';

export function useUndoAction() {
  function perform(opts: {
    message: string;
    action: () => Promise<void>;
    undo: () => Promise<void>;
    timeout?: number;
  }) {
    let undone = false;
    void opts.action();
    Notify.create({
      message: opts.message,
      color: 'dark',
      position: 'bottom',
      timeout: opts.timeout ?? 5000,
      actions: [
        {
          label: 'Undo',
          color: 'yellow',
          handler: () => {
            undone = true;
            void opts.undo();
          },
        },
      ],
    });
  }

  return { perform };
}
```

**Step 2: Verify it compiles**

Run: `npx vue-tsc --noEmit`
Expected: no errors

**Step 3: Commit**

```bash
git add src/composables/useUndoAction.ts
git commit -m "feat: add useUndoAction composable for delete/archive with undo toast"
```

---

### Task 2: Add quick-add bars to TaskList, AgendaList, MinutesList

Each list component gets a text input at the top for quickly creating items. The lists need a `subjectId` prop so they know which subject to create items under.

**Files:**
- Modify: `src/components/TaskList.vue`
- Modify: `src/components/AgendaList.vue`
- Modify: `src/components/MinutesList.vue`
- Modify: `src/pages/SubjectPage.vue` (pass subjectId prop)

**Step 1: Add subjectId prop and quick-add to TaskList.vue**

Add a `subjectId` prop. Add an input above the list. On Enter, call `taskStore.createTask()` then reload.

In the `<template>`, add before the existing `<div v-if="activeTasks.length">`:

```html
<div class="quick-add" style="margin-bottom: 12px;">
  <input
    v-model="newTaskTitle"
    class="quick-add-input"
    placeholder="+ Add task..."
    @keydown.enter="addTask"
  />
</div>
```

In the `<script>`:

```typescript
const props = defineProps<{ subjectId: number }>();

const newTaskTitle = ref('');

async function addTask() {
  const title = newTaskTitle.value.trim();
  if (!title) return;
  await taskStore.createTask({ subjectId: props.subjectId, title, priority: 'medium' });
  newTaskTitle.value = '';
  await taskStore.loadTasksForSubject(props.subjectId);
}
```

**Step 2: Add quick-add to AgendaList.vue**

Same pattern. Add `subjectId` prop, input, and create function:

```typescript
const props = defineProps<{ subjectId: number }>();

const newPointTitle = ref('');

async function addPoint() {
  const title = newPointTitle.value.trim();
  if (!title) return;
  await agendaStore.createAgendaPoint({ subjectId: props.subjectId, title });
  newPointTitle.value = '';
  await agendaStore.loadForSubject(props.subjectId);
}
```

**Step 3: Add quick-add to MinutesList.vue**

Same pattern:

```typescript
const props = defineProps<{ subjectId: number }>();

const newMinutesTitle = ref('');

async function addMinutes() {
  const title = newMinutesTitle.value.trim();
  if (!title) return;
  await minutesStore.createMinutes({ subjectId: props.subjectId, title, date: new Date() });
  newMinutesTitle.value = '';
  await minutesStore.loadForSubject(props.subjectId);
}
```

**Step 4: Pass subjectId from SubjectPage.vue**

In `src/pages/SubjectPage.vue`, change the three list usages (lines 47-53) to pass the subject ID:

```html
<div v-show="activeTab === 'tasks'">
  <TaskList :subject-id="subject.id!" />
</div>
<div v-show="activeTab === 'agenda'">
  <AgendaList :subject-id="subject.id!" />
</div>
<div v-show="activeTab === 'minutes'">
  <MinutesList :subject-id="subject.id!" />
</div>
```

**Step 5: Add quick-add-input CSS to app.scss**

```scss
// ─── Quick Add ──────────────────────────────────────────────
.quick-add-input {
  width: 100%;
  padding: 8px 12px;
  font-family: var(--g-font);
  font-size: 0.82rem;
  background: var(--g-surface-sunken);
  border: 1px solid var(--g-border);
  border-radius: var(--g-radius);
  color: var(--g-text);
  outline: none;
  transition: border-color var(--g-duration) var(--g-ease);

  &::placeholder {
    color: var(--g-text-muted);
  }

  &:focus {
    border-color: var(--g-accent-border);
  }
}
```

**Step 6: Verify it compiles**

Run: `npx vue-tsc --noEmit && npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"`
Expected: no errors

**Step 7: Commit**

```bash
git add src/components/TaskList.vue src/components/AgendaList.vue src/components/MinutesList.vue src/pages/SubjectPage.vue src/css/app.scss
git commit -m "feat: add quick-add bars to task, agenda, and minutes lists"
```

---

### Task 3: Enrich TaskDetail with status, priority, due date, and delete

Add editable fields to the task detail panel: a status toggle (todo/in-progress/done), priority toggle (low/medium/high), date input, and delete button with undo toast.

**Files:**
- Modify: `src/components/TaskDetail.vue`
- Modify: `src/css/app.scss` (add field-row styles)

**Step 1: Rewrite TaskDetail.vue**

Replace the entire file. The new version adds a `.detail-fields` row between title and description with status pills, priority pills, date input, and a delete button in the actions bar.

```vue
<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-section">
      <div class="detail-label">Title</div>
      <TiptapEditor v-model="localTitle" placeholder="Task title..." @update:model-value="debouncedSave" />
    </div>

    <div class="detail-section detail-fields">
      <div class="field-group">
        <div class="detail-label">Status</div>
        <div class="pill-toggle">
          <button
            v-for="s in statuses"
            :key="s"
            class="pill-btn"
            :class="{ 'is-active': localStatus === s }"
            @click="setStatus(s)"
          >{{ statusLabels[s] }}</button>
        </div>
      </div>
      <div class="field-group">
        <div class="detail-label">Priority</div>
        <div class="pill-toggle">
          <button
            v-for="p in priorities"
            :key="p"
            class="pill-btn"
            :class="[`priority-${p}`, { 'is-active': localPriority === p }]"
            @click="setPriority(p)"
          >{{ p }}</button>
        </div>
      </div>
      <div class="field-group">
        <div class="detail-label">Due date</div>
        <div style="display: flex; align-items: center; gap: 6px;">
          <input
            type="date"
            class="date-input"
            :value="localDueDateStr"
            @input="setDueDate(($event.target as HTMLInputElement).value)"
          />
          <q-btn
            v-if="localDueDate"
            flat dense round size="xs" icon="close"
            @click="clearDueDate"
          />
        </div>
      </div>
    </div>

    <div class="detail-section">
      <div class="detail-label">Description</div>
      <TiptapEditor v-model="localDescription" placeholder="Add a description..." @update:model-value="debouncedSave" />
    </div>

    <div class="detail-actions">
      <q-btn flat dense size="sm" icon="delete_outline" label="Delete" color="red-4" @click="deleteTask" />
      <q-space />
      <q-btn flat dense size="sm" label="Close" color="grey-7" @click="$emit('close')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useTaskStore } from 'stores/task-store';
import { useUndoAction } from 'src/composables/useUndoAction';
import type { Task, TaskStatus, TaskPriority } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ task: Task }>();
const emit = defineEmits<{ close: [] }>();

const taskStore = useTaskStore();
const { perform } = useUndoAction();

const statuses: TaskStatus[] = ['todo', 'in-progress', 'done'];
const priorities: TaskPriority[] = ['low', 'medium', 'high'];
const statusLabels: Record<TaskStatus, string> = {
  'todo': 'Todo',
  'in-progress': 'In Progress',
  'done': 'Done',
};

const localTitle = ref(props.task.title);
const localDescription = ref(props.task.description);
const localStatus = ref<TaskStatus>(props.task.status);
const localPriority = ref<TaskPriority>(props.task.priority);
const localDueDate = ref<Date | undefined>(props.task.dueDate);

const localDueDateStr = computed(() => {
  if (!localDueDate.value) return '';
  const d = new Date(localDueDate.value);
  return d.toISOString().split('T')[0]!;
});

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    void saveAll();
  }, 500);
}

async function saveAll() {
  const data: Partial<Task> = {
    title: localTitle.value,
    description: localDescription.value,
    status: localStatus.value,
    priority: localPriority.value,
  };
  if (localDueDate.value) {
    data.dueDate = localDueDate.value;
  }
  await taskStore.updateTask(props.task.id!, data);
}

function setStatus(s: TaskStatus) {
  localStatus.value = s;
  void saveAll();
}

function setPriority(p: TaskPriority) {
  localPriority.value = p;
  void saveAll();
}

function setDueDate(value: string) {
  if (value) {
    localDueDate.value = new Date(value + 'T00:00:00');
  } else {
    localDueDate.value = undefined;
  }
  void saveAll();
}

function clearDueDate() {
  localDueDate.value = undefined;
  void taskStore.updateTask(props.task.id!, { dueDate: undefined });
}

function deleteTask() {
  perform({
    message: 'Task deleted',
    action: async () => {
      await taskStore.deleteTask(props.task.id!);
      emit('close');
    },
    undo: async () => {
      await taskStore.updateTask(props.task.id!, { deleted: false });
    },
  });
}

watch(() => props.task, (t) => {
  localTitle.value = t.title;
  localDescription.value = t.description;
  localStatus.value = t.status;
  localPriority.value = t.priority;
  localDueDate.value = t.dueDate;
});
</script>
```

**Step 2: Add detail-fields and pill-toggle CSS to app.scss**

Append to `src/css/app.scss`:

```scss
// ─── Detail Fields Row ──────────────────────────────────────
.detail-fields {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.field-group {
  .detail-label {
    margin-bottom: 4px;
  }
}

.pill-toggle {
  display: flex;
  gap: 2px;
  background: var(--g-surface-sunken);
  border-radius: var(--g-radius);
  padding: 2px;

  .pill-btn {
    padding: 3px 10px;
    font-family: var(--g-font);
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: capitalize;
    border: none;
    background: none;
    color: var(--g-text-dim);
    cursor: pointer;
    border-radius: var(--g-radius-sm);
    transition: all var(--g-duration) var(--g-ease);

    &:hover {
      color: var(--g-text);
    }

    &.is-active {
      background: var(--g-surface);
      color: var(--g-text-bright);
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    }

    &.priority-high.is-active { color: var(--g-red); }
    &.priority-medium.is-active { color: var(--g-yellow); }
    &.priority-low.is-active { color: var(--g-text-secondary); }
  }
}

.date-input {
  padding: 3px 8px;
  font-family: var(--g-font);
  font-size: 0.72rem;
  background: var(--g-surface-sunken);
  border: 1px solid var(--g-border);
  border-radius: var(--g-radius);
  color: var(--g-text);
  color-scheme: dark;
  outline: none;

  &:focus {
    border-color: var(--g-accent-border);
  }
}
```

**Step 3: Verify it compiles**

Run: `npx vue-tsc --noEmit && npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"`
Expected: no errors

**Step 4: Commit**

```bash
git add src/components/TaskDetail.vue src/css/app.scss
git commit -m "feat: add status, priority, due date, and delete to task detail panel"
```

---

### Task 4: Add delete to AgendaDetail and date picker + delete to MinutesDetail

**Files:**
- Modify: `src/components/AgendaDetail.vue`
- Modify: `src/components/MinutesDetail.vue`

**Step 1: Update AgendaDetail.vue**

Add delete button using `useUndoAction`:

```vue
<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-section">
      <div class="detail-label">Topic</div>
      <TiptapEditor v-model="localTitle" placeholder="Agenda point..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="detail-label">Notes</div>
      <TiptapEditor v-model="localContent" placeholder="Add notes..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-actions">
      <q-btn flat dense size="sm" icon="delete_outline" label="Delete" color="red-4" @click="deletePoint" />
      <q-space />
      <q-btn flat dense size="sm" label="Close" color="grey-7" @click="$emit('close')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useAgendaStore } from 'stores/agenda-store';
import { useUndoAction } from 'src/composables/useUndoAction';
import type { AgendaPoint } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ agendaPoint: AgendaPoint }>();
const emit = defineEmits<{ close: [] }>();

const agendaStore = useAgendaStore();
const { perform } = useUndoAction();

const localTitle = ref(props.agendaPoint.title);
const localContent = ref(props.agendaPoint.content);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    void agendaStore.updateAgendaPoint(props.agendaPoint.id!, {
      title: localTitle.value,
      content: localContent.value,
    });
  }, 500);
}

function deletePoint() {
  perform({
    message: 'Agenda point deleted',
    action: async () => {
      await agendaStore.deleteAgendaPoint(props.agendaPoint.id!);
      emit('close');
    },
    undo: async () => {
      await agendaStore.updateAgendaPoint(props.agendaPoint.id!, { deleted: false });
    },
  });
}

watch(() => props.agendaPoint, (a) => {
  localTitle.value = a.title;
  localContent.value = a.content;
});
</script>
```

**Step 2: Update MinutesDetail.vue**

Add date picker and delete button:

```vue
<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-section">
      <div class="detail-label">Title</div>
      <TiptapEditor v-model="localTitle" placeholder="Meeting title..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="field-group">
        <div class="detail-label">Date</div>
        <input
          type="date"
          class="date-input"
          :value="localDateStr"
          @input="setDate(($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
    <div class="detail-section">
      <div class="detail-label">Minutes</div>
      <TiptapEditor v-model="localContent" placeholder="Write your meeting notes..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-actions">
      <q-btn flat dense size="sm" icon="delete_outline" label="Delete" color="red-4" @click="deleteMinutes" />
      <q-space />
      <q-btn flat dense size="sm" label="Close" color="grey-7" @click="$emit('close')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useMinutesStore } from 'stores/minutes-store';
import { useUndoAction } from 'src/composables/useUndoAction';
import type { MeetingMinutes } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ minutes: MeetingMinutes }>();
const emit = defineEmits<{ close: [] }>();

const minutesStore = useMinutesStore();
const { perform } = useUndoAction();

const localTitle = ref(props.minutes.title);
const localContent = ref(props.minutes.content);
const localDate = ref(new Date(props.minutes.date));

const localDateStr = computed(() => localDate.value.toISOString().split('T')[0]!);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    void minutesStore.updateMinutes(props.minutes.id!, {
      title: localTitle.value,
      content: localContent.value,
      date: localDate.value,
    });
  }, 500);
}

function setDate(value: string) {
  if (value) {
    localDate.value = new Date(value + 'T00:00:00');
    void minutesStore.updateMinutes(props.minutes.id!, { date: localDate.value });
  }
}

function deleteMinutes() {
  perform({
    message: 'Meeting minutes deleted',
    action: async () => {
      await minutesStore.deleteMinutes(props.minutes.id!);
      emit('close');
    },
    undo: async () => {
      await minutesStore.updateMinutes(props.minutes.id!, { deleted: false });
    },
  });
}

watch(() => props.minutes, (m) => {
  localTitle.value = m.title;
  localContent.value = m.content;
  localDate.value = new Date(m.date);
});
</script>
```

**Step 3: Verify it compiles**

Run: `npx vue-tsc --noEmit && npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"`
Expected: no errors

**Step 4: Commit**

```bash
git add src/components/AgendaDetail.vue src/components/MinutesDetail.vue
git commit -m "feat: add delete to agenda detail and date picker + delete to minutes detail"
```

---

### Task 5: Inline subject editing on SubjectPage

Make the subject name, color, type, and dates editable directly on the subject page header. Add archive button.

**Files:**
- Modify: `src/pages/SubjectPage.vue`
- Modify: `src/css/app.scss` (color picker, editable name styles)

**Step 1: Rewrite the subject-header in SubjectPage.vue**

Replace the `<div class="subject-header">` block and add new script logic. The name becomes a text input on click. The color dot opens a popover with preset colors. Type is a cycling button. Dates are inline date inputs. Archive uses `useUndoAction`.

Full replacement for SubjectPage.vue:

```vue
<template>
  <q-page class="q-pa-md">
    <div v-if="subject" class="stagger-in">
      <div class="subject-header">
        <div
          class="subject-color"
          :style="{ backgroundColor: subject.color }"
          @click="showColorPicker = !showColorPicker"
          style="cursor: pointer;"
        >
          <div v-if="showColorPicker" class="color-picker" @click.stop>
            <div
              v-for="c in presetColors"
              :key="c"
              class="color-swatch"
              :class="{ 'is-active': subject.color === c }"
              :style="{ backgroundColor: c }"
              @click="setColor(c)"
            />
          </div>
        </div>

        <div class="subject-info">
          <input
            v-if="editingName"
            ref="nameInputRef"
            v-model="editName"
            class="subject-name-input"
            @blur="saveName"
            @keydown.enter="saveName"
            @keydown.escape="cancelEditName"
          />
          <div v-else class="subject-name" @click="startEditName" style="cursor: pointer;">
            {{ subject.name }}
          </div>
          <button class="subject-type-btn" @click="cycleType">{{ subject.type }}</button>
          <div class="subject-dates">
            <template v-if="showDates || subject.startDate">
              <input
                type="date"
                class="date-input"
                :value="formatDateInput(subject.startDate)"
                @input="setStartDate(($event.target as HTMLInputElement).value)"
              />
              <span class="date-separator">&mdash;</span>
              <input
                type="date"
                class="date-input"
                :value="formatDateInput(subject.endDate)"
                @input="setEndDate(($event.target as HTMLInputElement).value)"
              />
            </template>
            <button
              v-else
              class="set-dates-btn"
              @click="showDates = true"
            >+ Set dates</button>
          </div>
        </div>

        <q-btn
          flat round size="sm"
          :icon="subject.pinned ? 'push_pin' : 'o_push_pin'"
          :color="subject.pinned ? 'primary' : 'grey-6'"
          @click="togglePin"
        >
          <q-tooltip>{{ subject.pinned ? 'Unpin' : 'Pin to dashboard' }}</q-tooltip>
        </q-btn>
        <q-btn
          flat round size="sm"
          icon="archive"
          color="grey-6"
          @click="archiveSubject"
        >
          <q-tooltip>Archive subject</q-tooltip>
        </q-btn>
      </div>

      <div class="tab-bar">
        <button class="tab-item" :class="{ 'is-active': activeTab === 'tasks' }" @click="activeTab = 'tasks'">Tasks</button>
        <button class="tab-item" :class="{ 'is-active': activeTab === 'agenda' }" @click="activeTab = 'agenda'">Agenda</button>
        <button class="tab-item" :class="{ 'is-active': activeTab === 'minutes' }" @click="activeTab = 'minutes'">Minutes</button>
      </div>

      <div v-show="activeTab === 'tasks'">
        <TaskList :subject-id="subject.id!" />
      </div>
      <div v-show="activeTab === 'agenda'">
        <AgendaList :subject-id="subject.id!" />
      </div>
      <div v-show="activeTab === 'minutes'">
        <MinutesList :subject-id="subject.id!" />
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon"><q-icon name="search_off" /></div>
      <div class="empty-title">Subject not found</div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useSubjectStore } from 'stores/subject-store';
import { useTaskStore } from 'stores/task-store';
import { useAgendaStore } from 'stores/agenda-store';
import { useMinutesStore } from 'stores/minutes-store';
import { useUndoAction } from 'src/composables/useUndoAction';
import type { Subject, SubjectType } from 'src/models/types';
import TaskList from 'components/TaskList.vue';
import AgendaList from 'components/AgendaList.vue';
import MinutesList from 'components/MinutesList.vue';

const route = useRoute();
const router = useRouter();
const subjectStore = useSubjectStore();
const taskStore = useTaskStore();
const agendaStore = useAgendaStore();
const minutesStore = useMinutesStore();
const { perform } = useUndoAction();

const subject = ref<Subject | undefined>();
const activeTab = ref('tasks');

// Name editing
const editingName = ref(false);
const editName = ref('');
const nameInputRef = ref<HTMLInputElement | null>(null);

// Color picker
const showColorPicker = ref(false);
const presetColors = ['#4A90D9', '#E67E22', '#2ECC71', '#9B59B6', '#E74C3C', '#1ABC9C', '#F39C12', '#34495E'];

// Dates
const showDates = ref(false);

// Type cycling
const subjectTypes: SubjectType[] = ['project', 'person', 'team', 'board', 'other'];

function startEditName() {
  editName.value = subject.value?.name ?? '';
  editingName.value = true;
  void nextTick(() => nameInputRef.value?.select());
}

function saveName() {
  const name = editName.value.trim();
  if (name && subject.value?.id) {
    void subjectStore.updateSubject(subject.value.id, { name });
    subject.value = { ...subject.value, name };
  }
  editingName.value = false;
}

function cancelEditName() {
  editingName.value = false;
}

function setColor(color: string) {
  if (subject.value?.id) {
    void subjectStore.updateSubject(subject.value.id, { color });
    subject.value = { ...subject.value, color };
  }
  showColorPicker.value = false;
}

function cycleType() {
  if (!subject.value?.id) return;
  const idx = subjectTypes.indexOf(subject.value.type);
  const next = subjectTypes[(idx + 1) % subjectTypes.length]!;
  void subjectStore.updateSubject(subject.value.id, { type: next });
  subject.value = { ...subject.value, type: next };
}

function formatDateInput(date: Date | undefined): string {
  if (!date) return '';
  return new Date(date).toISOString().split('T')[0]!;
}

function setStartDate(value: string) {
  if (!subject.value?.id) return;
  const date = value ? new Date(value + 'T00:00:00') : undefined;
  void subjectStore.updateSubject(subject.value.id, { startDate: date });
  subject.value = { ...subject.value, startDate: date };
}

function setEndDate(value: string) {
  if (!subject.value?.id) return;
  const date = value ? new Date(value + 'T00:00:00') : undefined;
  void subjectStore.updateSubject(subject.value.id, { endDate: date });
  subject.value = { ...subject.value, endDate: date };
}

function archiveSubject() {
  if (!subject.value?.id) return;
  const id = subject.value.id;
  perform({
    message: 'Subject archived',
    action: async () => {
      await subjectStore.archiveSubject(id);
      void router.push({ name: 'dashboard' });
    },
    undo: async () => {
      await subjectStore.updateSubject(id, { archived: false });
    },
  });
}

async function togglePin() {
  if (subject.value?.id) {
    await subjectStore.togglePin(subject.value.id);
    subject.value = subjectStore.subjects.find((s) => s.id === subject.value!.id);
  }
}

async function loadSubject(id: number) {
  await subjectStore.loadSubjects();
  subject.value = subjectStore.subjects.find((s) => s.id === id);
  if (subject.value) {
    showDates.value = !!(subject.value.startDate || subject.value.endDate);
    await Promise.all([
      taskStore.loadTasksForSubject(id),
      agendaStore.loadForSubject(id),
      minutesStore.loadForSubject(id),
    ]);
  }
}

watch(
  () => route.params.id,
  (id) => {
    if (id) void loadSubject(Number(id));
  },
  { immediate: true }
);
</script>
```

**Step 2: Add subject editing CSS to app.scss**

```scss
// ─── Subject Editing ────────────────────────────────────────
.subject-name-input {
  font-family: var(--g-font);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--g-text-bright);
  background: var(--g-surface-sunken);
  border: 1px solid var(--g-accent-border);
  border-radius: var(--g-radius);
  padding: 2px 8px;
  outline: none;
  width: 100%;
}

.subject-type-btn {
  font-family: var(--g-font);
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--g-text-dim);
  background: none;
  border: 1px dashed var(--g-border);
  border-radius: var(--g-radius-sm);
  padding: 1px 8px;
  cursor: pointer;
  margin-top: 4px;
  transition: all var(--g-duration) var(--g-ease);

  &:hover {
    border-color: var(--g-border-bright);
    color: var(--g-text);
  }
}

.subject-dates {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;

  .date-separator {
    color: var(--g-text-muted);
    font-size: 0.75rem;
  }
}

.set-dates-btn {
  font-family: var(--g-font);
  font-size: 0.7rem;
  color: var(--g-text-dim);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;

  &:hover {
    color: var(--g-accent);
  }
}

.color-picker {
  position: absolute;
  top: 20px;
  left: 0;
  z-index: 10;
  display: flex;
  gap: 4px;
  padding: 6px;
  background: var(--g-surface-raised);
  border: 1px solid var(--g-border-bright);
  border-radius: var(--g-radius);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
}

.color-swatch {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: border-color var(--g-duration) var(--g-ease);

  &:hover {
    border-color: var(--g-text-secondary);
  }

  &.is-active {
    border-color: var(--g-text-bright);
  }
}

// Make subject-color relative for color picker positioning
.subject-header .subject-color {
  position: relative;
}
```

**Step 3: Verify it compiles**

Run: `npx vue-tsc --noEmit && npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"`
Expected: no errors

**Step 4: Commit**

```bash
git add src/pages/SubjectPage.vue src/css/app.scss
git commit -m "feat: add inline subject editing (name, color, type, dates, archive)"
```

---

### Task 6: Add overdue tasks and unresolved agendas to Dashboard

Add two new sections to the dashboard: overdue tasks (top priority) and unresolved agenda points across all subjects.

**Files:**
- Modify: `src/pages/DashboardPage.vue`
- Modify: `src/stores/task-store.ts` (add `overdueTasks` computed)

**Step 1: Add overdueTasks computed to task-store.ts**

After the `tasksDueNextWeek` computed (line 85), add:

```typescript
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
```

Add `overdueTasks` to the return statement (line 133).

**Step 2: Update DashboardPage.vue**

Import `useAgendaStore` and load unresolved agendas on mount. Add the two new dashboard sections. The overdue section goes first in the grid. The unresolved agendas section goes after Next Week.

In `<script>`, add:

```typescript
import { useAgendaStore } from 'stores/agenda-store';

const agendaStore = useAgendaStore();
const { overdueTasks } = storeToRefs(taskStore);
const { unresolvedPoints } = storeToRefs(agendaStore);
```

In `onMounted`, add `agendaStore.loadAllUnresolved()` to the `Promise.all`.

Update `isEmpty` to also check `overdueTasks.value.length === 0` and `unresolvedPoints.value.length === 0`.

In the template, add the Overdue section as the FIRST item in the dashboard grid:

```html
<!-- Overdue -->
<div v-if="overdueTasks.length" class="dashboard-section">
  <div class="section-card">
    <div class="section-header">
      <div class="section-icon" style="background: rgba(248, 113, 113, 0.12); color: var(--g-red);">
        <q-icon name="warning" />
      </div>
      <span class="section-label">Overdue</span>
      <span class="section-count" v-if="overdueTasks.length">{{ overdueTasks.length }}</span>
    </div>
    <div class="section-body">
      <div
        v-for="task in overdueTasks"
        :key="task.id!"
        class="dash-task"
        @click="goToSubject(task.subjectId)"
      >
        <q-checkbox
          class="dash-task-check"
          :model-value="task.status === 'done'"
          @update:model-value="toggleDone(task)"
          @click.stop
          size="sm"
        />
        <span class="dash-task-title">{{ stripHtml(task.title) }}</span>
        <span class="dash-task-subject">{{ subjectName(task.subjectId) }}</span>
      </div>
    </div>
  </div>
</div>
```

Add the Unresolved Agendas section after the Next Week section:

```html
<!-- Unresolved Agendas -->
<div v-if="unresolvedPoints.length" class="dashboard-section">
  <div class="section-card">
    <div class="section-header">
      <div class="section-icon" style="background: rgba(103, 232, 249, 0.1); color: var(--g-cyan);">
        <q-icon name="chat_bubble_outline" />
      </div>
      <span class="section-label">To Discuss</span>
      <span class="section-count">{{ unresolvedPoints.length }}</span>
    </div>
    <div class="section-body">
      <div
        v-for="point in unresolvedPoints"
        :key="point.id!"
        class="dash-task"
        @click="goToSubject(point.subjectId)"
      >
        <span class="dash-task-title" style="padding-left: 4px;">{{ stripHtml(point.title) }}</span>
        <span class="dash-task-subject">{{ agendaSubjectName(point.subjectId) }}</span>
      </div>
    </div>
  </div>
</div>
```

Add `agendaSubjectName` function (same as `subjectName`, just renamed for clarity — or reuse `subjectName`).

**Step 3: Verify it compiles**

Run: `npx vue-tsc --noEmit && npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"`
Expected: no errors

**Step 4: Commit**

```bash
git add src/stores/task-store.ts src/pages/DashboardPage.vue
git commit -m "feat: add overdue tasks and unresolved agendas to dashboard"
```

---

### Task 7: Final verification

**Step 1: Run all checks**

```bash
npx vue-tsc --noEmit
npx eslint -c ./eslint.config.js "./src*/**/*.{ts,js,mjs,cjs,vue}"
npx vitest run
```

All should pass.

**Step 2: Commit any fixes if needed**
