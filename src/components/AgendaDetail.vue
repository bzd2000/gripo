<template>
  <div class="detail-panel" @click.stop @keydown="handleTab">
    <div class="detail-section">
      <div class="detail-label">Topic</div>
      <TiptapEditor ref="topicEditor" v-model="localTitle" placeholder="Agenda point..." data-field-index="0" @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="detail-label">Notes</div>
      <TiptapEditor ref="notesEditor" v-model="localContent" placeholder="Add notes..." :toolbar="true" data-field-index="1" @update:model-value="debouncedSave" />
    </div>
    <div class="detail-actions">
      <q-btn flat dense size="sm" icon="delete_outline" label="Delete" color="red-4" @click="deletePoint" />
      <q-space />
      <q-btn flat dense size="sm" label="Close" color="grey-7" @click="$emit('close')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useAgendaStore } from 'stores/agenda-store';
import { useUndoAction } from 'src/composables/useUndoAction';
import type { AgendaPoint } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ agendaPoint: AgendaPoint }>();
const emit = defineEmits<{ close: [] }>();

const agendaStore = useAgendaStore();
const { perform } = useUndoAction();

const topicEditor = ref<InstanceType<typeof TiptapEditor> | null>(null);
const notesEditor = ref<InstanceType<typeof TiptapEditor> | null>(null);

const localTitle = ref(props.agendaPoint.title);
const localContent = ref(props.agendaPoint.content);

const fieldCount = 2;
const editorRefs: Record<number, typeof topicEditor> = { 0: topicEditor, 1: notesEditor };

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
    void agendaStore.updateAgendaPoint(props.agendaPoint.id!, {
      title: localTitle.value,
      content: localContent.value,
    });
  }, 500);
}

function deletePoint() {
  perform({
    message: 'Agenda point deleted',
    action: async () => {
      await agendaStore.deleteAgendaPoint(props.agendaPoint.id!);
      emit('close');
    },
    undo: async () => {
      await agendaStore.updateAgendaPoint(props.agendaPoint.id!, { deleted: false });
    },
  });
}

watch(() => props.agendaPoint, (a) => {
  localTitle.value = a.title;
  localContent.value = a.content;
});
</script>
