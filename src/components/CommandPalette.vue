<template>
  <q-dialog v-model="isOpen" position="top" seamless>
    <q-card class="command-palette" style="width: 600px; max-width: 90vw; margin-top: 80px;">
      <q-card-section class="q-pb-none">
        <q-input
          ref="inputRef"
          v-model="query"
          placeholder="Search, create (t: a: m: s:), or command (/)"
          dense
          outlined
          autofocus
          @keydown.down.prevent="moveDown"
          @keydown.up.prevent="moveUp"
          @keydown.enter.prevent="executeSelected"
          @keydown.escape.prevent="close"
        >
          <template #prepend>
            <q-icon name="search" />
          </template>
        </q-input>
      </q-card-section>

      <q-card-section class="q-pt-sm" v-if="results.length">
        <q-list dense>
          <q-item
            v-for="(result, index) in results"
            :key="result.id"
            clickable
            :active="index === selectedIndex"
            active-class="bg-blue-1"
            @click="executeResult(result)"
            @mouseover="selectedIndex = index"
          >
            <q-item-section avatar>
              <q-icon :name="result.icon" size="sm" />
            </q-item-section>
            <q-item-section>
              <q-item-label>{{ result.label }}</q-item-label>
              <q-item-label caption v-if="result.caption">{{ result.caption }}</q-item-label>
            </q-item-section>
          </q-item>
        </q-list>
      </q-card-section>

      <q-card-section v-else-if="query && parsed.type === 'create'" class="text-center text-grey-6">
        Press Enter to create {{ parsed.entityType }}: "{{ parsed.title }}"
        <span v-if="!parsed.subjectName && parsed.entityType !== 'subject'">
          (select a subject)
        </span>
      </q-card-section>

      <q-card-section v-else-if="query" class="text-center text-grey-6">
        No results. Try t: a: m: s: to create.
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';
import { parseCommand, type ParsedInput } from 'src/composables/useCommandPalette';
import { useSubjectStore } from 'stores/subject-store';
import { useTaskStore } from 'stores/task-store';
import { useAgendaStore } from 'stores/agenda-store';
import { useMinutesStore } from 'stores/minutes-store';
import { db } from 'src/db/database';

interface SearchResult {
  id: string;
  icon: string;
  label: string;
  caption?: string;
  action: () => void;
}

const router = useRouter();
const subjectStore = useSubjectStore();
const taskStore = useTaskStore();
const agendaStore = useAgendaStore();
const minutesStore = useMinutesStore();

const isOpen = ref(false);
const query = ref('');
const selectedIndex = ref(0);
const inputRef = ref();

const parsed = computed<ParsedInput>(() => parseCommand(query.value));

const results = ref<SearchResult[]>([]);

watch(query, async (q) => {
  selectedIndex.value = 0;
  if (!q.trim()) {
    results.value = [];
    return;
  }

  const p = parsed.value;
  if (p.type === 'search') {
    results.value = await search(p.query);
  } else if (p.type === 'create' && p.entityType !== 'subject' && !p.subjectName) {
    // Show subjects to pick from
    results.value = subjectStore.activeSubjects.map((s) => ({
      id: `subject-${s.id}`,
      icon: 'folder',
      label: s.name,
      caption: `Create ${p.entityType} under ${s.name}`,
      action: () => createItem(p.entityType as 'task' | 'agenda' | 'minutes', p.title, s.id!),
    }));
  } else {
    results.value = [];
  }
});

async function search(q: string): Promise<SearchResult[]> {
  const lower = q.toLowerCase();
  const found: SearchResult[] = [];

  // Search subjects
  subjectStore.subjects
    .filter((s) => s.name.toLowerCase().includes(lower) && !s.archived)
    .forEach((s) => {
      found.push({
        id: `subject-${s.id}`,
        icon: 'folder',
        label: s.name,
        caption: s.type,
        action: () => {
          router.push({ name: 'subject', params: { id: s.id } });
          close();
        },
      });
    });

  // Search tasks
  const tasks = await db.tasks.filter(
    (t) => !t.deleted && t.title.toLowerCase().includes(lower)
  ).toArray();
  tasks.forEach((t) => {
    found.push({
      id: `task-${t.id}`,
      icon: 'check_box',
      label: t.title.replace(/<[^>]*>/g, ''),
      caption: subjectStore.subjects.find((s) => s.id === t.subjectId)?.name,
      action: () => {
        router.push({ name: 'subject', params: { id: t.subjectId } });
        close();
      },
    });
  });

  // Search agenda points
  const agendas = await db.agendaPoints.filter(
    (a) => !a.deleted && a.title.toLowerCase().includes(lower)
  ).toArray();
  agendas.forEach((a) => {
    found.push({
      id: `agenda-${a.id}`,
      icon: 'chat_bubble_outline',
      label: a.title.replace(/<[^>]*>/g, ''),
      caption: subjectStore.subjects.find((s) => s.id === a.subjectId)?.name,
      action: () => {
        router.push({ name: 'subject', params: { id: a.subjectId } });
        close();
      },
    });
  });

  return found;
}

async function createItem(entityType: 'task' | 'agenda' | 'minutes', title: string, subjectId: number) {
  if (entityType === 'task') {
    await taskStore.createTask({ subjectId, title, priority: 'medium' });
  } else if (entityType === 'agenda') {
    await agendaStore.createAgendaPoint({ subjectId, title });
  } else if (entityType === 'minutes') {
    await minutesStore.createMinutes({ subjectId, title, date: new Date() });
  }
  router.push({ name: 'subject', params: { id: subjectId } });
  close();
}

async function executeSelected() {
  const p = parsed.value;

  if (results.value.length > 0) {
    results.value[selectedIndex.value].action();
    return;
  }

  if (p.type === 'create') {
    if (p.entityType === 'subject') {
      const colors = ['#4A90D9', '#E67E22', '#2ECC71', '#9B59B6', '#E74C3C', '#1ABC9C'];
      const color = colors[Math.floor(Math.random() * colors.length)];
      await subjectStore.createSubject({ name: p.title, type: 'project', color });
      close();
      return;
    }

    if (p.subjectName) {
      const subject = subjectStore.activeSubjects.find(
        (s) => s.name.toLowerCase() === p.subjectName!.toLowerCase()
      );
      if (subject) {
        await createItem(p.entityType as 'task' | 'agenda' | 'minutes', p.title, subject.id!);
      }
    }
  }
}

function moveDown() {
  if (selectedIndex.value < results.value.length - 1) {
    selectedIndex.value++;
  }
}

function moveUp() {
  if (selectedIndex.value > 0) {
    selectedIndex.value--;
  }
}

function executeResult(result: SearchResult) {
  result.action();
}

function open() {
  query.value = '';
  results.value = [];
  selectedIndex.value = 0;
  isOpen.value = true;
  nextTick(() => inputRef.value?.focus());
}

function close() {
  isOpen.value = false;
  query.value = '';
}

function handleKeydown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
    event.preventDefault();
    if (isOpen.value) {
      close();
    } else {
      open();
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown);
});

defineExpose({ open, close });
</script>

<style lang="scss" scoped>
.command-palette {
  border-radius: 12px;
}
</style>
