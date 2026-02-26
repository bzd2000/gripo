<template>
  <div>
    <q-list separator v-if="activePoints.length">
      <q-item v-for="point in activePoints" :key="point.id" class="rounded-borders q-my-xs">
        <q-item-section side>
          <q-checkbox
            :model-value="point.resolved"
            @update:model-value="toggleResolved(point)"
          />
        </q-item-section>
        <q-item-section>
          <q-item-label :class="{ 'text-strike text-grey': point.resolved }">
            <span v-html="point.title" />
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No agenda points. Press Cmd+K then type a: to add one.
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAgendaStore } from 'stores/agenda-store';
import { storeToRefs } from 'pinia';
import type { AgendaPoint } from 'src/models/types';

const agendaStore = useAgendaStore();
const { activePoints } = storeToRefs(agendaStore);

async function toggleResolved(point: AgendaPoint) {
  await agendaStore.toggleResolved(point.id!);
}
</script>
