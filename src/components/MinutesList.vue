<template>
  <div>
    <div v-if="sortedMinutes.length">
      <div
        v-for="item in sortedMinutes"
        :key="item.id!"
        class="item-card"
        :class="{ 'is-active': selectedId === item.id }"
        @click="toggleSelected(item.id!)"
      >
        <div style="display: flex; align-items: center; gap: 10px;">
          <q-icon name="description" size="20px" style="color: var(--g-text-tertiary); flex-shrink: 0;" />
          <div style="flex: 1; min-width: 0;">
            <div class="item-title">{{ stripHtml(item.title) }}</div>
            <div class="item-meta">{{ formatDate(item.date) }}</div>
          </div>
        </div>

        <MinutesDetail
          v-if="selectedId === item.id"
          :minutes="item"
          @close="selectedId = undefined"
        />
      </div>
    </div>

    <div v-else class="empty-state">
      <div class="empty-icon"><q-icon name="edit_note" /></div>
      <div class="empty-title">No meeting minutes</div>
      <div class="empty-description">Press <kbd>&#8984;K</kbd> then type <code>m: Meeting title</code> to add notes.</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useMinutesStore } from 'stores/minutes-store';
import { storeToRefs } from 'pinia';
import MinutesDetail from 'components/MinutesDetail.vue';

const minutesStore = useMinutesStore();
const { sortedMinutes } = storeToRefs(minutesStore);

const selectedId = ref<number | undefined>();

function toggleSelected(id: number) {
  selectedId.value = selectedId.value === id ? undefined : id;
}

function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '');
}

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}
</script>
