<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-section">
      <div class="detail-label">Title</div>
      <TiptapEditor v-model="localTitle" placeholder="Meeting title..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="detail-label">Minutes</div>
      <TiptapEditor v-model="localContent" placeholder="Write your meeting notes..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-actions">
      <q-btn flat dense size="sm" label="Close" color="grey-7" @click="$emit('close')" />
    </div>
  </div>
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
