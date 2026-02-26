import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { db } from 'src/db/database';
import type { AgendaPoint } from 'src/models/types';

export const useAgendaStore = defineStore('agenda', () => {
  const agendaPoints = ref<AgendaPoint[]>([]);

  const activePoints = computed(() =>
    agendaPoints.value.filter((a) => !a.deleted)
  );

  const unresolvedPoints = computed(() =>
    agendaPoints.value.filter((a) => !a.deleted && !a.resolved)
  );

  async function loadForSubject(subjectId: number) {
    agendaPoints.value = await db.agendaPoints
      .where('subjectId')
      .equals(subjectId)
      .toArray();
  }

  async function loadAllUnresolved() {
    agendaPoints.value = await db.agendaPoints
      .filter((a) => !a.deleted && !a.resolved)
      .toArray();
  }

  async function createAgendaPoint(data: {
    subjectId: number;
    title: string;
    content?: string;
  }) {
    const now = new Date();
    await db.agendaPoints.add({
      subjectId: data.subjectId,
      title: data.title,
      content: data.content ?? '',
      resolved: false,
      deleted: false,
      createdAt: now,
      updatedAt: now,
    });
  }

  async function updateAgendaPoint(id: number, data: Partial<AgendaPoint>) {
    await db.agendaPoints.update(id, { ...data, updatedAt: new Date() });
    const point = await db.agendaPoints.get(id);
    if (point) {
      await loadForSubject(point.subjectId);
    }
  }

  async function toggleResolved(id: number) {
    const point = agendaPoints.value.find((a) => a.id === id);
    if (point) {
      await updateAgendaPoint(id, { resolved: !point.resolved });
    }
  }

  async function deleteAgendaPoint(id: number) {
    await updateAgendaPoint(id, { deleted: true });
  }

  return {
    agendaPoints,
    activePoints,
    unresolvedPoints,
    loadForSubject,
    loadAllUnresolved,
    createAgendaPoint,
    updateAgendaPoint,
    toggleResolved,
    deleteAgendaPoint,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useAgendaStore, import.meta.hot));
}
