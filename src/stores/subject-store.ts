import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { db } from 'src/db/database';
import type { Subject, SubjectType } from 'src/models/types';

export const useSubjectStore = defineStore('subjects', () => {
  const subjects = ref<Subject[]>([]);

  const activeSubjects = computed(() =>
    subjects.value.filter((s) => !s.archived)
  );

  const pinnedSubjects = computed(() =>
    subjects.value.filter((s) => s.pinned && !s.archived)
  );

  async function loadSubjects() {
    subjects.value = await db.subjects.toArray();
  }

  async function createSubject(data: {
    name: string;
    type: SubjectType;
    color: string;
    startDate?: Date;
    endDate?: Date;
  }) {
    const now = new Date();
    const id = await db.subjects.add({
      ...data,
      pinned: false,
      archived: false,
      createdAt: now,
      updatedAt: now,
    });
    await loadSubjects();
    return id;
  }

  async function updateSubject(id: number, data: Partial<Subject>) {
    await db.subjects.update(id, { ...data, updatedAt: new Date() });
    await loadSubjects();
  }

  async function archiveSubject(id: number) {
    await updateSubject(id, { archived: true });
  }

  async function togglePin(id: number) {
    const subject = subjects.value.find((s) => s.id === id);
    if (subject) {
      await updateSubject(id, { pinned: !subject.pinned });
    }
  }

  return {
    subjects,
    activeSubjects,
    pinnedSubjects,
    loadSubjects,
    createSubject,
    updateSubject,
    archiveSubject,
    togglePin,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useSubjectStore, import.meta.hot));
}
