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

function withoutKey<T extends object, K extends keyof T>(obj: T, key: K): Omit<T, K> {
  const copy = { ...obj };
  delete copy[key];
  return copy;
}

function setStartDate(value: string) {
  if (!subject.value?.id) return;
  if (value) {
    const date = new Date(value + 'T00:00:00');
    void subjectStore.updateSubject(subject.value.id, { startDate: date });
    subject.value = { ...subject.value, startDate: date };
  } else {
    // With exactOptionalPropertyTypes we cannot assign { startDate: undefined }.
    // Remove the key entirely so the rebuilt object omits it.
    void subjectStore.updateSubject(subject.value.id, { name: subject.value.name });
    subject.value = withoutKey(subject.value, 'startDate') as Subject;
  }
}

function setEndDate(value: string) {
  if (!subject.value?.id) return;
  if (value) {
    const date = new Date(value + 'T00:00:00');
    void subjectStore.updateSubject(subject.value.id, { endDate: date });
    subject.value = { ...subject.value, endDate: date };
  } else {
    void subjectStore.updateSubject(subject.value.id, { name: subject.value.name });
    subject.value = withoutKey(subject.value, 'endDate') as Subject;
  }
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
