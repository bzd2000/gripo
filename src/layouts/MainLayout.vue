<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />
        <q-toolbar-title>Gripo</q-toolbar-title>
        <q-btn flat dense round icon="search" aria-label="Command palette" @click="openCommandPalette">
          <q-tooltip>Cmd+K</q-tooltip>
        </q-btn>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered class="bg-grey-1">
      <q-list>
        <q-item clickable :to="{ name: 'dashboard' }" active-class="text-primary">
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>Dashboard</q-item-section>
        </q-item>

        <q-separator class="q-my-sm" />

        <q-item-label header class="text-weight-bold">Subjects</q-item-label>

        <q-item
          v-for="subject in activeSubjects"
          :key="subject.id"
          clickable
          :to="{ name: 'subject', params: { id: subject.id } }"
          active-class="text-primary"
        >
          <q-item-section avatar>
            <q-badge :style="{ backgroundColor: subject.color }" rounded />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ subject.name }}</q-item-label>
          </q-item-section>
          <q-item-section side v-if="subject.pinned">
            <q-icon name="push_pin" size="xs" color="grey" />
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>

    <CommandPalette ref="commandPaletteRef" />
  </q-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useSubjectStore } from 'stores/subject-store';
import { storeToRefs } from 'pinia';
import CommandPalette from 'components/CommandPalette.vue';
import { useKeyboardNav } from 'src/composables/useKeyboardNav';

useKeyboardNav();

const subjectStore = useSubjectStore();
const { activeSubjects } = storeToRefs(subjectStore);

const leftDrawerOpen = ref(false);
const commandPaletteRef = ref<InstanceType<typeof CommandPalette>>();

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value;
}

function openCommandPalette() {
  commandPaletteRef.value?.open();
}

onMounted(async () => {
  await subjectStore.loadSubjects();
});
</script>
