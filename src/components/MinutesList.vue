<template>
  <div>
    <q-list separator v-if="sortedMinutes.length">
      <template v-for="item in sortedMinutes" :key="item.id">
        <q-item
          clickable
          class="rounded-borders q-my-xs"
          @click="toggleSelected(item.id!)"
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
        <MinutesDetail
          v-if="selectedId === item.id"
          :minutes="item"
          @close="selectedId = undefined"
        />
      </template>
    </q-list>

    <div v-else class="text-grey-6 q-pa-lg text-center">
      No meeting minutes. Press Cmd+K then type m: to add one.
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

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString();
}
</script>
