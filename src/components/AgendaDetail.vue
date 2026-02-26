<template>
  <q-card flat bordered class="rounded-borders q-mb-sm">
    <q-card-section>
      <TiptapEditor v-model="localTitle" placeholder="Agenda point..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption text-grey q-mb-xs">Notes</div>
      <TiptapEditor v-model="localContent" placeholder="Add notes..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-actions>
      <q-btn flat label="Close" @click="$emit('close')" />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useAgendaStore } from 'stores/agenda-store';
import type { AgendaPoint } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ agendaPoint: AgendaPoint }>();
defineEmits<{ close: [] }>();

const agendaStore = useAgendaStore();

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

watch(() => props.agendaPoint, (a) => {
  localTitle.value = a.title;
  localContent.value = a.content;
});
</script>
