<template>
  <q-card flat bordered class="rounded-borders q-mb-sm">
    <q-card-section>
      <TiptapEditor v-model="localTitle" placeholder="Meeting title..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption text-grey q-mb-xs">Minutes</div>
      <TiptapEditor v-model="localContent" placeholder="Write your meeting notes..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-actions>
      <q-btn flat label="Close" @click="$emit('close')" />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useMinutesStore } from 'stores/minutes-store';
import type { MeetingMinutes } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ minutes: MeetingMinutes }>();
defineEmits<{ close: [] }>();

const minutesStore = useMinutesStore();

const localTitle = ref(props.minutes.title);
const localContent = ref(props.minutes.content);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    void minutesStore.updateMinutes(props.minutes.id!, {
      title: localTitle.value,
      content: localContent.value,
    });
  }, 500);
}

watch(() => props.minutes, (m) => {
  localTitle.value = m.title;
  localContent.value = m.content;
});
</script>
