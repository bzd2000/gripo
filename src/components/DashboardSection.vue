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
  void router.push({ name: 'subject', params: { id: subjectId } });
}

async function toggleDone(task: Task) {
  const newStatus = task.status === 'done' ? 'todo' : 'done';
  await taskStore.updateTask(task.id!, { status: newStatus });
  await taskStore.loadAllTasks();
}
</script>
