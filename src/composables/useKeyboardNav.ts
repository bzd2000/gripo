import { onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

export function useKeyboardNav() {
  const router = useRouter();

  function handleKeydown(event: KeyboardEvent) {
    // Skip if typing in an input/editor
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable ||
      target.closest('.ProseMirror')
    ) {
      return;
    }

    // Cmd+1 = Dashboard
    if ((event.metaKey || event.ctrlKey) && event.key === '1') {
      event.preventDefault();
      router.push({ name: 'dashboard' });
      return;
    }

    // Escape = go back / close
    if (event.key === 'Escape') {
      event.preventDefault();
      router.back();
      return;
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeydown);
  });

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown);
  });
}
