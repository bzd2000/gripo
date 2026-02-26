<template>
  <div>
    <q-list separator v-if="activePoints.length">
      <template v-for="point in activePoints" :key="point.id">
        <q-item
          clickable
          class="rounded-borders q-my-xs"
          @click="toggleSelected(point.id!)"
        >
          <q-item-section side>
            <q-checkbox
              :model-value="point.resolved"
              @update:model-value="toggleResolved(point)"
              @click.stop
            />
          </q-item-section>
          <q-item-section>
            <q-item-label :class="{ 'text-strike text-grey': point.resolved }">
              <span v-html="point.title" />
            </q-item-label>
          </q-item-section>
        </q-item>
        <AgendaDetail
          v-if="selectedId === point.id"
          :agenda-point="point"
          @close="selectedId = undefined"
        />
      </template>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No agenda points. Press Cmd+K then type a: to add one.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useAgendaStore } from 'stores/agenda-store';
import { storeToRefs } from 'pinia';
import type { AgendaPoint } from 'src/models/types';
import AgendaDetail from 'components/AgendaDetail.vue';

const agendaStore = useAgendaStore();
const { activePoints } = storeToRefs(agendaStore);

const selectedId = ref<number | undefined>();

function toggleSelected(id: number) {
  selectedId.value = selectedId.value === id ? undefined : id;
}

async function toggleResolved(point: AgendaPoint) {
  await agendaStore.toggleResolved(point.id!);
}
</script>
