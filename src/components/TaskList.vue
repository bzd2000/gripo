<template>
  <div>
    <div class="quick-add" style="margin-bottom: 12px;">
      <input
        v-model="newTaskTitle"
        class="quick-add-input"
        placeholder="+ Add task..."
        @keydown.enter="addTask"
      />
    </div>

    <div v-if="activeTasks.length">
      <div
        v-for="task in activeTasks"
        :key="task.id!"
        class="item-card"
        :class="{
          'is-active': selectedId === task.id,
          'is-done': task.status === 'done',
        }"
        @click="toggleSelected(task.id!)"
      >
        <div style="display: flex; align-items: center; gap: 10px;">
          <q-checkbox
            :model-value="task.status === 'done'"
            @update:model-value="toggleDone(task)"
            @click.stop
            size="sm"
          />
          <div style="flex: 1; min-width: 0;">
            <div class="item-title">
              {{ stripHtml(task.title) }}
            </div>
          </div>
          <span class="priority-pill" :class="`priority-${task.priority}`">{{ task.priority }}</span>
          <span v-if="task.dueDate" class="due-pill" :class="dueDateClass(task.dueDate)">
            {{ formatDate(task.dueDate) }}
          </span>
        </div>

        <TaskDetail
          v-if="selectedId === task.id"
          :task="task"
          @close="selectedId = undefined"
        />
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon"><q-icon name="check_circle_outline" /></div>
      <div class="empty-title">No tasks yet</div>
      <div class="empty-description">Press <kbd>&#8984;K</kbd> then type <code>t: Your task</code> to add one.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useTaskStore } from 'stores/task-store';
import { storeToRefs } from 'pinia';
import type { Task } from 'src/models/types';
import TaskDetail from 'components/TaskDetail.vue';

const props = defineProps<{ subjectId: number }>();

const taskStore = useTaskStore();
const { activeTasks } = storeToRefs(taskStore);

const selectedId = ref<number | undefined>();
const newTaskTitle = ref('');

async function addTask() {
  const title = newTaskTitle.value.trim();
  if (!title) return;
  await taskStore.createTask({ subjectId: props.subjectId, title, priority: 'medium' });
  newTaskTitle.value = '';
  await taskStore.loadTasksForSubject(props.subjectId);
}

function toggleSelected(id: number) {
  selectedId.value = selectedId.value === id ? undefined : id;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '');
}

function dueDateClass(date: Date): string {
  const now = new Date();
  const d = new Date(date);
  now.setHours(0, 0, 0, 0);
  d.setHours(0, 0, 0, 0);
  if (d < now) return 'is-overdue';
  if (d.getTime() === now.getTime()) return 'is-today';
  return 'is-future';
}

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

async function toggleDone(task: Task) {
  const newStatus = task.status === 'done' ? 'todo' : 'done';
  await taskStore.updateTask(task.id!, { status: newStatus });
}
</script>
