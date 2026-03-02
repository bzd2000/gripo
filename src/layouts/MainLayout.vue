<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary text-white">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above :width="240" :breakpoint="768">
      <div class="sidebar-brand">
        <div class="brand-mark">G</div>
        <div class="brand-name">Gripo</div>
      </div>

      <div
        class="sidebar-search-trigger"
        @click="openCommandPalette"
      >
        <q-icon name="search" size="16px" />
        Search or create...
        <kbd>&#8984;K</kbd>
      </div>

      <q-list>
        <q-item clickable :to="{ name: 'dashboard' }" active-class="text-primary">
          <q-item-section avatar>
            <q-icon name="space_dashboard" />
          </q-item-section>
          <q-item-section>Dashboard</q-item-section>
        </q-item>

        <q-item-label header>Subjects</q-item-label>

        <q-item
          v-for="subject in activeSubjects"
          :key="subject.id!"
          clickable
          :to="{ name: 'subject', params: { id: subject.id! } }"
          active-class="text-primary"
        >
          <q-item-section avatar>
            <q-badge :style="{ backgroundColor: subject.color }" rounded />
          </q-item-section>
          <q-item-section>
            <q-item-label>{{ subject.name }}</q-item-label>
          </q-item-section>
          <q-item-section side v-if="subject.pinned">
            <q-icon name="push_pin" size="xs" />
          </q-item-section>
        </q-item>

        <q-separator />
        <q-item clickable :to="{ name: 'settings' }" active-class="text-primary">
          <q-item-section avatar>
            <q-icon name="settings" />
          </q-item-section>
          <q-item-section>Settings</q-item-section>
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
