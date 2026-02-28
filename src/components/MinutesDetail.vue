<template>
  <div class="detail-panel" @click.stop @keydown="handleTab">
    <div class="detail-section">
      <div class="detail-label">Title</div>
      <TiptapEditor ref="titleEditor" v-model="localTitle" placeholder="Meeting title..." data-field-index="0" @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="field-group">
        <div class="detail-label">Date</div>
        <input
          type="date"
          class="date-input"
          data-field-index="1"
          :value="localDateStr"
          @input="setDate(($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>
    <div class="detail-section">
      <div class="detail-label">Minutes</div>
      <TiptapEditor ref="contentEditor" v-model="localContent" placeholder="Write your meeting notes..." :toolbar="true" data-field-index="2" @update:model-value="debouncedSave" />
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

const titleEditor = ref<InstanceType<typeof TiptapEditor> | null>(null);
const contentEditor = ref<InstanceType<typeof TiptapEditor> | null>(null);

const localTitle = ref(props.minutes.title);
const localContent = ref(props.minutes.content);
const localDate = ref(new Date(props.minutes.date));

const localDateStr = computed(() => localDate.value.toISOString().split('T')[0]!);

const fieldCount = 3;
const editorRefs: Record<number, typeof titleEditor> = { 0: titleEditor, 2: contentEditor };

function handleTab(event: KeyboardEvent) {
  if (event.key !== 'Tab') return;
  if (!(event.currentTarget instanceof HTMLElement)) return;
  const panel = event.currentTarget;
  const fields = panel.querySelectorAll('[data-field-index]');
  if (!fields.length) return;

  event.preventDefault();
  const active = document.activeElement;
  const currentField = active?.closest('[data-field-index]');
  const currentIdx = currentField instanceof HTMLElement ? Number(currentField.dataset.fieldIndex) : -1;

  let nextIdx: number;
  if (event.shiftKey) {
    nextIdx = currentIdx > 0 ? currentIdx - 1 : fieldCount - 1;
  } else {
    nextIdx = currentIdx < fieldCount - 1 ? currentIdx + 1 : 0;
  }

  const nextField = panel.querySelector<HTMLElement>(`[data-field-index="${nextIdx}"]`);
  if (!nextField) return;

  const editorRef = editorRefs[nextIdx];
  if (editorRef?.value) {
    editorRef.value.focus();
  } else {
    nextField.focus();
  }
}

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
