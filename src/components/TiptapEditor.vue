<template>
  <div class="tiptap-editor" :class="{ 'has-toolbar': toolbar }">
    <div v-if="toolbar" class="editor-toolbar">
      <q-btn-group flat>
        <q-btn
          flat dense size="sm"
          icon="format_bold"
          :class="{ 'text-primary': editorInstance?.isActive('bold') }"
          @click="editorInstance?.chain().focus().toggleBold().run()"
        >
          <q-tooltip>Bold ({{ modKey }}+B)</q-tooltip>
        </q-btn>
        <q-btn
          flat dense size="sm"
          icon="format_italic"
          :class="{ 'text-primary': editorInstance?.isActive('italic') }"
          @click="editorInstance?.chain().focus().toggleItalic().run()"
        >
          <q-tooltip>Italic ({{ modKey }}+I)</q-tooltip>
        </q-btn>
        <q-btn
          flat dense size="sm"
          icon="strikethrough_s"
          :class="{ 'text-primary': editorInstance?.isActive('strike') }"
          @click="editorInstance?.chain().focus().toggleStrike().run()"
        >
          <q-tooltip>Strikethrough ({{ modKey }}+Shift+X)</q-tooltip>
        </q-btn>
        <div class="toolbar-divider" />
        <q-btn
          flat dense size="sm"
          icon="format_list_bulleted"
          :class="{ 'text-primary': editorInstance?.isActive('bulletList') }"
          @click="editorInstance?.chain().focus().toggleBulletList().run()"
        >
          <q-tooltip>Bullet list ({{ modKey }}+Shift+8)</q-tooltip>
        </q-btn>
        <q-btn
          flat dense size="sm"
          icon="format_list_numbered"
          :class="{ 'text-primary': editorInstance?.isActive('orderedList') }"
          @click="editorInstance?.chain().focus().toggleOrderedList().run()"
        >
          <q-tooltip>Ordered list ({{ modKey }}+Shift+7)</q-tooltip>
        </q-btn>
        <q-btn
          flat dense size="sm"
          icon="code"
          :class="{ 'text-primary': editorInstance?.isActive('codeBlock') }"
          @click="editorInstance?.chain().focus().toggleCodeBlock().run()"
        >
          <q-tooltip>Code block ({{ modKey }}+Alt+C)</q-tooltip>
        </q-btn>
      </q-btn-group>
    </div>
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
    <EditorContent v-if="editor" :editor="editor" />
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
  toolbar?: boolean;
}>(), {
  placeholder: 'Start typing...',
  toolbar: false,
});

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const modKey = navigator.platform.includes('Mac') ? '\u2318' : 'Ctrl';

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
      editor.value.commands.setContent(value, { emitUpdate: false });
    }
  }
);

onBeforeUnmount(() => {
  editor.value?.destroy();
});

function focus() {
  editor.value?.commands.focus();
}

defineExpose({ focus });
</script>

<style lang="scss">
.tiptap-editor {
  .bubble-menu {
    background: var(--g-surface-raised);
    border: 1px solid var(--g-border-bright);
    border-radius: var(--g-radius);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    padding: 3px;
  }

  .ProseMirror {
    min-height: 100px;
    padding: 8px 12px;
    border: 1px solid var(--g-border);
    border-radius: var(--g-radius);
    outline: none;
    color: var(--g-text);
    background: var(--g-surface-sunken);
    font-family: var(--g-font);
    font-size: 0.82rem;
    line-height: 1.6;

    &:focus {
      border-color: var(--g-accent-border);
    }

    p.is-editor-empty:first-child::before {
      content: attr(data-placeholder);
      float: left;
      color: var(--g-text-muted);
      pointer-events: none;
      height: 0;
    }
  }

  &.has-toolbar .ProseMirror {
    border-top-left-radius: 0;
    border-top-right-radius: 0;
    border-top-color: var(--g-border);
  }
}
</style>
