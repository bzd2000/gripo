<template>
  <div>
    <div v-if="activePoints.length">
      <div
        v-for="point in activePoints"
        :key="point.id!"
        class="item-card"
        :class="{
          'is-active': selectedId === point.id,
          'is-done': point.resolved,
        }"
        @click="toggleSelected(point.id!)"
      >
        <div style="display: flex; align-items: center; gap: 10px;">
          <q-checkbox
            :model-value="point.resolved"
            @update:model-value="toggleResolved(point)"
            @click.stop
            size="sm"
          />
          <div style="flex: 1; min-width: 0;">
            <div class="item-title">
              {{ stripHtml(point.title) }}
            </div>
          </div>
        </div>

        <AgendaDetail
          v-if="selectedId === point.id"
          :agenda-point="point"
          @close="selectedId = undefined"
        />
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon"><q-icon name="chat_bubble_outline" /></div>
      <div class="empty-title">No agenda points</div>
      <div class="empty-description">Press <kbd>&#8984;K</kbd> then type <code>a: Your topic</code> to add one.</div>
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

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '');
}

async function toggleResolved(point: AgendaPoint) {
  await agendaStore.toggleResolved(point.id!);
}
</script>
