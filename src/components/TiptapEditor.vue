<template>
  <div class="tiptap-editor">
    <div ref="bubbleMenuEl" class="bubble-menu" v-show="bubbleMenuVisible">
      <q-btn-group flat>
        <q-btn
          flat
          dense
          icon="format_bold"
          :class="{ 'text-primary': editorInstance?.isActive('bold') }"
          @click="editorInstance?.chain().focus().toggleBold().run()"
        />
        <q-btn
          flat
          dense
          icon="format_italic"
          :class="{ 'text-primary': editorInstance?.isActive('italic') }"
          @click="editorInstance?.chain().focus().toggleItalic().run()"
        />
        <q-btn
          flat
          dense
          icon="strikethrough_s"
          :class="{ 'text-primary': editorInstance?.isActive('strike') }"
          @click="editorInstance?.chain().focus().toggleStrike().run()"
        />
        <q-btn
          flat
          dense
          icon="format_list_bulleted"
          :class="{ 'text-primary': editorInstance?.isActive('bulletList') }"
          @click="editorInstance?.chain().focus().toggleBulletList().run()"
        />
        <q-btn
          flat
          dense
          icon="format_list_numbered"
          :class="{ 'text-primary': editorInstance?.isActive('orderedList') }"
          @click="editorInstance?.chain().focus().toggleOrderedList().run()"
        />
        <q-btn
          flat
          dense
          icon="code"
          :class="{ 'text-primary': editorInstance?.isActive('codeBlock') }"
          @click="editorInstance?.chain().focus().toggleCodeBlock().run()"
        />
      </q-btn-group>
    </div>
    <EditorContent :editor="editor" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, computed } from 'vue';
import { useEditor, EditorContent } from '@tiptap/vue-3';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import Placeholder from '@tiptap/extension-placeholder';
import { BubbleMenuPlugin } from '@tiptap/extension-bubble-menu';

const props = withDefaults(defineProps<{
  modelValue: string;
  placeholder?: string;
}>(), {
  placeholder: 'Start typing...',
});

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const bubbleMenuEl = ref<HTMLElement | null>(null);
const bubbleMenuVisible = ref(false);

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit,
    Link.configure({ openOnClick: false }),
    Placeholder.configure({ placeholder: props.placeholder }),
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML());
  },
});

const editorInstance = computed(() => editor.value);

onMounted(() => {
  // Register bubble menu plugin once editor is ready
  const tryRegister = () => {
    if (editor.value && bubbleMenuEl.value) {
      editor.value.registerPlugin(
        BubbleMenuPlugin({
          pluginKey: 'bubbleMenu',
          editor: editor.value,
          element: bubbleMenuEl.value,
          options: {
            onShow: () => { bubbleMenuVisible.value = true; },
            onHide: () => { bubbleMenuVisible.value = false; },
          },
        })
      );
    } else {
      requestAnimationFrame(tryRegister);
    }
  };
  tryRegister();
});

watch(
  () => props.modelValue,
  (value) => {
    if (editor.value && editor.value.getHTML() !== value) {
      editor.value.commands.setContent(value, false);
    }
  }
);

onBeforeUnmount(() => {
  editor.value?.destroy();
});
</script>

<style lang="scss">
.tiptap-editor {
  .bubble-menu {
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    padding: 2px;
  }

  .ProseMirror {
    min-height: 100px;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    outline: none;

    &:focus {
      border-color: var(--q-primary);
    }

    p.is-editor-empty:first-child::before {
      content: attr(data-placeholder);
      float: left;
      color: #adb5bd;
      pointer-events: none;
      height: 0;
    }
  }
}
</style>
