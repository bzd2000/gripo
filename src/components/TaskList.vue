<template>
  <div>
    <q-list separator v-if="activeTasks.length">
      <template v-for="task in activeTasks" :key="task.id">
        <q-item
          clickable
          class="rounded-borders q-my-xs"
          @click="toggleSelected(task.id!)"
        >
          <q-item-section side>
            <q-checkbox
              :model-value="task.status === 'done'"
              @update:model-value="toggleDone(task)"
              @click.stop
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
        <TaskDetail
          v-if="selectedId === task.id"
          :task="task"
          @close="selectedId = undefined"
        />
      </template>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No tasks yet. Press Cmd+K then type t: to add one.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useTaskStore } from 'stores/task-store';
import { storeToRefs } from 'pinia';
import type { Task, TaskPriority } from 'src/models/types';
import TaskDetail from 'components/TaskDetail.vue';

const taskStore = useTaskStore();
const { activeTasks } = storeToRefs(taskStore);

const selectedId = ref<number | undefined>();

function toggleSelected(id: number) {
  selectedId.value = selectedId.value === id ? undefined : id;
}

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
