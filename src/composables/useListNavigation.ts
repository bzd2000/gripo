import { ref, onMounted, onUnmounted, type Ref } from 'vue';

interface UseListNavigationOptions<T> {
  items: Ref<T[]>;
  getId: (item: T) => number;
  selectedId: Ref<number | undefined>;
  isActive: Ref<boolean>;
}

export function useListNavigation<T>({
  items,
  getId,
  selectedId,
  isActive,
}: UseListNavigationOptions<T>) {
  const focusedId = ref<number | undefined>();

  function shouldSkip(event: KeyboardEvent): boolean {
    const target = event.target as HTMLElement;
    if (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.isContentEditable ||
      target.closest('.ProseMirror')
    ) {
      return true;
    }
    // Skip if command palette is open
    if (document.querySelector('.command-palette')) {
      return true;
    }
    return false;
  }

  function handleKeydown(event: KeyboardEvent) {
    if (!isActive.value) return;
    if (shouldSkip(event)) return;

    const list = items.value;
    if (!list.length) return;

    switch (event.key) {
      case 'j':
      case 'ArrowDown': {
        event.preventDefault();
        const currentIdx = list.findIndex((item) => getId(item) === focusedId.value);
        const nextIdx = currentIdx < list.length - 1 ? currentIdx + 1 : 0;
        focusedId.value = getId(list[nextIdx]!);
        break;
      }
      case 'k':
      case 'ArrowUp': {
        event.preventDefault();
        const currentIdx = list.findIndex((item) => getId(item) === focusedId.value);
        const prevIdx = currentIdx > 0 ? currentIdx - 1 : list.length - 1;
        focusedId.value = getId(list[prevIdx]!);
        break;
      }
      case 'Enter': {
        if (focusedId.value != null) {
          event.preventDefault();
          selectedId.value = selectedId.value === focusedId.value ? undefined : focusedId.value;
        }
        break;
      }
      case 'Escape': {
        if (selectedId.value != null) {
          event.preventDefault();
          event.stopPropagation();
          selectedId.value = undefined;
        }
        break;
      }
    }
  }

  onMounted(() => {
    document.addEventListener('keydown', handleKeydown, true);
  });

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeydown, true);
  });

  return { focusedId };
}
