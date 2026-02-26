<template>
  <div>
    <q-list separator v-if="sortedMinutes.length">
      <q-item
        v-for="item in sortedMinutes"
        :key="item.id"
        clickable
        class="rounded-borders q-my-xs"
        @click="$emit('select', item)"
      >
        <q-item-section>
          <q-item-label>
            <span v-html="item.title" />
          </q-item-label>
          <q-item-label caption>
            {{ formatDate(item.date) }}
          </q-item-label>
        </q-item-section>
      </q-item>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No meeting minutes. Press Cmd+K then type m: to add one.
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMinutesStore } from 'stores/minutes-store';
import { storeToRefs } from 'pinia';

defineEmits<{
  select: [item: import('src/models/types').MeetingMinutes];
}>();

const minutesStore = useMinutesStore();
const { sortedMinutes } = storeToRefs(minutesStore);

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString();
}
</script>
