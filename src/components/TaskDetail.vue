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
