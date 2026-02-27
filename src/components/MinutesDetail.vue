<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-section">
      <div class="detail-label">Title</div>
      <TiptapEditor v-model="localTitle" placeholder="Meeting title..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="field-group">
        <div class="detail-label">Date</div>
        <input
          type="date"
          class="date-input"
          :value="localDateStr"
          @input="setDate(($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
    <div class="detail-section">
      <div class="detail-label">Minutes</div>
      <TiptapEditor v-model="localContent" placeholder="Write your meeting notes..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-actions">
      <q-btn flat dense size="sm" icon="delete_outline" label="Delete" color="red-4" @click="deleteMinutes" />
      <q-space />
      <q-btn flat dense size="sm" label="Close" color="grey-7" @click="$emit('close')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useMinutesStore } from 'stores/minutes-store';
import { useUndoAction } from 'src/composables/useUndoAction';
import type { MeetingMinutes } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ minutes: MeetingMinutes }>();
const emit = defineEmits<{ close: [] }>();

const minutesStore = useMinutesStore();
const { perform } = useUndoAction();

const localTitle = ref(props.minutes.title);
const localContent = ref(props.minutes.content);
const localDate = ref(new Date(props.minutes.date));

const localDateStr = computed(() => localDate.value.toISOString().split('T')[0]!);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    void minutesStore.updateMinutes(props.minutes.id!, {
      title: localTitle.value,
      content: localContent.value,
      date: localDate.value,
    });
  }, 500);
}

function setDate(value: string) {
  if (value) {
    localDate.value = new Date(value + 'T00:00:00');
    void minutesStore.updateMinutes(props.minutes.id!, { date: localDate.value });
  }
}

function deleteMinutes() {
  perform({
    message: 'Meeting minutes deleted',
    action: async () => {
      await minutesStore.deleteMinutes(props.minutes.id!);
      emit('close');
    },
    undo: async () => {
      await minutesStore.updateMinutes(props.minutes.id!, { deleted: false });
    },
  });
}

watch(() => props.minutes, (m) => {
  localTitle.value = m.title;
  localContent.value = m.content;
  localDate.value = new Date(m.date);
});
</script>
