<template>
  <div class="detail-panel" @click.stop>
    <div class="detail-section">
      <div class="detail-label">Title</div>
      <TiptapEditor v-model="localTitle" placeholder="Task title..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-section">
      <div class="detail-label">Description</div>
      <TiptapEditor v-model="localDescription" placeholder="Add a description..." @update:model-value="debouncedSave" />
    </div>
    <div class="detail-actions">
      <q-btn flat dense size="sm" label="Close" color="grey-7" @click="$emit('close')" />
    </div>
  </div>
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
