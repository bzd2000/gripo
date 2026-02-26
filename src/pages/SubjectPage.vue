<template>
  <q-page class="q-pa-md">
    <div v-if="subject" class="stagger-in">
      <div class="subject-header">
        <div class="subject-color" :style="{ backgroundColor: subject.color }" />
        <div class="subject-info">
          <div class="subject-name">{{ subject.name }}</div>
          <div class="subject-type">{{ subject.type }}</div>
        </div>
        <q-btn
          flat
          round
          size="sm"
          :icon="subject.pinned ? 'push_pin' : 'o_push_pin'"
          :color="subject.pinned ? 'primary' : 'grey-6'"
          @click="togglePin"
        >
          <q-tooltip>{{ subject.pinned ? 'Unpin' : 'Pin to dashboard' }}</q-tooltip>
        </q-btn>
      </div>

      <div class="tab-bar">
        <button
          class="tab-item"
          :class="{ 'is-active': activeTab === 'tasks' }"
          @click="activeTab = 'tasks'"
        >
          Tasks
        </button>
        <button
          class="tab-item"
          :class="{ 'is-active': activeTab === 'agenda' }"
          @click="activeTab = 'agenda'"
        >
          Agenda
        </button>
        <button
          class="tab-item"
          :class="{ 'is-active': activeTab === 'minutes' }"
          @click="activeTab = 'minutes'"
        >
          Minutes
        </button>
      </div>

      <div v-show="activeTab === 'tasks'">
        <TaskList />
      </div>
      <div v-show="activeTab === 'agenda'">
        <AgendaList />
      </div>
      <div v-show="activeTab === 'minutes'">
        <MinutesList />
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon">
        <q-icon name="search_off" />
      </div>
      <div class="empty-title">Subject not found</div>
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
import type { Subject } from 'src/models/types';
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

watch(
  () => route.params.id,
  (id) => {
    if (id) void loadSubject(Number(id));
  },
  { immediate: true }
);
</script>
