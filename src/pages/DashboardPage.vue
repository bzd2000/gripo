<template>
  <q-page class="q-pa-md">
    <div v-if="isEmpty" class="welcome-state">
      <div class="welcome-icon">
        <q-icon name="rocket_launch" />
      </div>
      <div class="welcome-title">Welcome to Gripo</div>
      <div class="welcome-text">
        Get a grip on your work. Create your first subject to start
        organizing tasks, agenda points, and meeting notes.
      </div>
      <div class="welcome-text">
        Press <kbd>&#8984;K</kbd> then type <code>s: My First Project</code>
      </div>
    </div>

    <template v-else>
      <div class="page-title">Dashboard</div>
      <div class="page-subtitle">{{ greetingText }}</div>

      <div class="dashboard-grid stagger-in">
        <!-- Today -->
        <div class="dashboard-section">
          <div class="section-card">
            <div class="section-header">
              <div class="section-icon" style="background: rgba(196, 98, 62, 0.1); color: var(--g-accent);">
                <q-icon name="today" />
              </div>
              <span class="section-label">Today</span>
              <span class="section-count" v-if="tasksDueToday.length">{{ tasksDueToday.length }}</span>
            </div>
            <div v-if="tasksDueToday.length" class="section-body">
              <div
                v-for="task in tasksDueToday"
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
                <span class="dash-task-title" :class="{ 'is-done': task.status === 'done' }">
                  {{ stripHtml(task.title) }}
                </span>
                <span class="priority-pill" :class="`priority-${task.priority}`">{{ task.priority }}</span>
              </div>
            </div>
            <div v-else class="section-empty">Nothing due today</div>
          </div>
        </div>

        <!-- This Week -->
        <div class="dashboard-section">
          <div class="section-card">
            <div class="section-header">
              <div class="section-icon" style="background: rgba(78, 130, 160, 0.1); color: var(--g-info);">
                <q-icon name="date_range" />
              </div>
              <span class="section-label">This Week</span>
              <span class="section-count" v-if="tasksDueThisWeek.length">{{ tasksDueThisWeek.length }}</span>
            </div>
            <div v-if="tasksDueThisWeek.length" class="section-body">
              <div
                v-for="task in tasksDueThisWeek"
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
                <span class="dash-task-title" :class="{ 'is-done': task.status === 'done' }">
                  {{ stripHtml(task.title) }}
                </span>
                <span class="dash-task-subject">{{ subjectName(task.subjectId) }}</span>
              </div>
            </div>
            <div v-else class="section-empty">Nothing else this week</div>
          </div>
        </div>

        <!-- Next Week -->
        <div class="dashboard-section">
          <div class="section-card">
            <div class="section-header">
              <div class="section-icon" style="background: rgba(90, 138, 96, 0.1); color: var(--g-positive);">
                <q-icon name="event" />
              </div>
              <span class="section-label">Next Week</span>
              <span class="section-count" v-if="tasksDueNextWeek.length">{{ tasksDueNextWeek.length }}</span>
            </div>
            <div v-if="tasksDueNextWeek.length" class="section-body">
              <div
                v-for="task in tasksDueNextWeek"
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
                <span class="dash-task-title" :class="{ 'is-done': task.status === 'done' }">
                  {{ stripHtml(task.title) }}
                </span>
                <span class="dash-task-subject">{{ subjectName(task.subjectId) }}</span>
              </div>
            </div>
            <div v-else class="section-empty">Nothing next week</div>
          </div>
        </div>

        <!-- Pinned Subjects -->
        <div v-if="pinnedSubjects.length" class="dashboard-section">
          <div class="section-card">
            <div class="section-header">
              <div class="section-icon" style="background: rgba(196, 154, 60, 0.1); color: var(--g-warning);">
                <q-icon name="push_pin" />
              </div>
              <span class="section-label">Pinned</span>
            </div>
            <div class="section-body">
              <div
                v-for="subject in pinnedSubjects"
                :key="subject.id!"
                class="subject-card"
                @click="goToSubject(subject.id!)"
              >
                <div class="subject-card-dot" :style="{ backgroundColor: subject.color }" />
                <span class="subject-card-name">{{ subject.name }}</span>
                <q-icon name="push_pin" class="subject-card-pin" />
              </div>
            </div>
          </div>
        </div>

        <!-- Ongoing Subjects -->
        <div v-if="ongoingSubjects.length" class="dashboard-section dashboard-full">
          <div class="section-card">
            <div class="section-header">
              <div class="section-icon" style="background: rgba(90, 138, 96, 0.1); color: var(--g-positive);">
                <q-icon name="timelapse" />
              </div>
              <span class="section-label">Ongoing</span>
            </div>
            <div class="section-body">
              <div
                v-for="subject in ongoingSubjects"
                :key="subject.id!"
                class="subject-card"
                @click="goToSubject(subject.id!)"
              >
                <div class="subject-card-dot" :style="{ backgroundColor: subject.color }" />
                <span class="subject-card-name">{{ subject.name }}</span>
                <span class="subject-card-dates" v-if="subject.startDate && subject.endDate">
                  {{ formatDate(subject.startDate) }} &mdash; {{ formatDate(subject.endDate) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useSubjectStore } from 'stores/subject-store';
import { useTaskStore } from 'stores/task-store';
import { storeToRefs } from 'pinia';
import type { Task } from 'src/models/types';

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

const greetingText = computed(() => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning. Here\'s what needs your attention.';
  if (hour < 17) return 'Good afternoon. Here\'s what needs your attention.';
  return 'Good evening. Here\'s what needs your attention.';
});

function goToSubject(id: number) {
  void router.push({ name: 'subject', params: { id } });
}

function subjectName(subjectId: number): string {
  return subjectStore.subjects.find((s) => s.id === subjectId)?.name ?? '';
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '');
}

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

async function toggleDone(task: Task) {
  const newStatus = task.status === 'done' ? 'todo' : 'done';
  await taskStore.updateTask(task.id!, { status: newStatus });
  await taskStore.loadAllTasks();
}

onMounted(async () => {
  await Promise.all([
    subjectStore.loadSubjects(),
    taskStore.loadAllTasks(),
  ]);
});
</script>
