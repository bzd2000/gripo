<template>
  <div class="detail-panel" @click.stop @keydown="handleTab">
    <div class="detail-section">
      <div class="detail-label">Title</div>
      <TiptapEditor ref="titleEditor" v-model="localTitle" placeholder="Task title..." data-field-index="0" @update:model-value="debouncedSave" />
    </div>

    <div class="detail-section detail-fields">
      <div class="field-group">
        <div class="detail-label">Status</div>
        <div
          class="pill-toggle"
          tabindex="0"
          data-field-index="1"
          @keydown="handlePillKeys($event, statuses, localStatus, setStatus)"
        >
          <button
            v-for="s in statuses"
            :key="s"
            class="pill-btn"
            tabindex="-1"
            :class="{ 'is-active': localStatus === s }"
            @click="setStatus(s)"
          >{{ statusLabels[s] }}</button>
        </div>
      </div>
      <div class="field-group">
        <div class="detail-label">Priority</div>
        <div
          class="pill-toggle"
          tabindex="0"
          data-field-index="2"
          @keydown="handlePillKeys($event, priorities, localPriority, setPriority)"
        >
          <button
            v-for="p in priorities"
            :key="p"
            class="pill-btn"
            tabindex="-1"
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
            data-field-index="3"
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
      <TiptapEditor ref="descEditor" v-model="localDescription" placeholder="Add a description..." :toolbar="true" data-field-index="4" @update:model-value="debouncedSave" />
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

const titleEditor = ref<InstanceType<typeof TiptapEditor> | null>(null);
const descEditor = ref<InstanceType<typeof TiptapEditor> | null>(null);

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

const fieldCount = 5;
const editorRefs: Record<number, typeof titleEditor> = { 0: titleEditor, 4: descEditor };

function handleTab(event: KeyboardEvent) {
  if (event.key !== 'Tab') return;
  if (!(event.currentTarget instanceof HTMLElement)) return;
  const panel = event.currentTarget;
  const fields = panel.querySelectorAll('[data-field-index]');
  if (!fields.length) return;

  event.preventDefault();
  const active = document.activeElement;
  const currentField = active?.closest('[data-field-index]');
  const currentIdx = currentField instanceof HTMLElement ? Number(currentField.dataset.fieldIndex) : -1;

  let nextIdx: number;
  if (event.shiftKey) {
    nextIdx = currentIdx > 0 ? currentIdx - 1 : fieldCount - 1;
  } else {
    nextIdx = currentIdx < fieldCount - 1 ? currentIdx + 1 : 0;
  }

  const nextField = panel.querySelector<HTMLElement>(`[data-field-index="${nextIdx}"]`);
  if (!nextField) return;

  const editorRef = editorRefs[nextIdx];
  if (editorRef?.value) {
    editorRef.value.focus();
  } else {
    nextField.focus();
  }
}

function handlePillKeys<T>(event: KeyboardEvent, options: T[], current: T, setter: (val: T) => void) {
  if (event.key === 'ArrowRight' || event.key === 'ArrowDown') {
    event.preventDefault();
    const idx = options.indexOf(current);
    const next = options[(idx + 1) % options.length]!;
    setter(next);
  } else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
    event.preventDefault();
    const idx = options.indexOf(current);
    const prev = options[(idx - 1 + options.length) % options.length]!;
    setter(prev);
  }
}

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
  void taskStore.updateTask(
    props.task.id!,
    { dueDate: undefined } as unknown as Partial<Task>,
  );
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
