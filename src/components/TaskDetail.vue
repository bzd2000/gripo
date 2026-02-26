<template>
  <q-card flat bordered class="rounded-borders q-mb-sm">
    <q-card-section>
      <TiptapEditor v-model="localTitle" placeholder="Task title..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-section class="q-pt-none">
      <div class="text-caption text-grey q-mb-xs">Description</div>
      <TiptapEditor v-model="localDescription" placeholder="Add a description..." @update:model-value="debouncedSave" />
    </q-card-section>
    <q-card-actions>
      <q-btn flat label="Close" @click="$emit('close')" />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useTaskStore } from 'stores/task-store';
import type { Task } from 'src/models/types';
import TiptapEditor from 'components/TiptapEditor.vue';

const props = defineProps<{ task: Task }>();
defineEmits<{ close: [] }>();

const taskStore = useTaskStore();

const localTitle = ref(props.task.title);
const localDescription = ref(props.task.description);

let saveTimeout: ReturnType<typeof setTimeout>;

function debouncedSave() {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(() => {
    void taskStore.updateTask(props.task.id!, {
      title: localTitle.value,
      description: localDescription.value,
    });
  }, 500);
}

watch(() => props.task, (t) => {
  localTitle.value = t.title;
  localDescription.value = t.description;
});
</script>
