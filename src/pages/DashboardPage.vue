<template>
  <q-page class="q-pa-md">
    <h5 class="q-mt-none q-mb-md">Dashboard</h5>

    <DashboardSection title="Today" icon="today" :items="tasksDueToday" empty-text="Nothing due today." />
    <DashboardSection title="This Week" icon="date_range" :items="tasksDueThisWeek" empty-text="Nothing else this week." />
    <DashboardSection title="Next Week" icon="event" :items="tasksDueNextWeek" empty-text="Nothing next week." />

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
  void router.push({ name: 'subject', params: { id } });
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
