<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-section">
      <div class="detail-label">Topic</div>
      <TiptapEditor v-model="localTitle" placeholder="Agenda point..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="detail-label">Notes</div>
      <TiptapEditor v-model="localContent" placeholder="Add notes..." @update:model-value="debouncedSave" />
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

const localTitle = ref(props.agendaPoint.title);
const localContent = ref(props.agendaPoint.content);

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
