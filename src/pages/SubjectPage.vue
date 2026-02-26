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
import { ref, watch } from 'vue';
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
