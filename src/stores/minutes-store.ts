import { defineStore, acceptHMRUpdate } from 'pinia';
import { ref, computed } from 'vue';
import { db } from 'src/db/database';
import type { MeetingMinutes } from 'src/models/types';

export const useMinutesStore = defineStore('minutes', () => {
  const minutes = ref<MeetingMinutes[]>([]);

  const activeMinutes = computed(() =>
    minutes.value.filter((m) => !m.deleted)
  );

  const sortedMinutes = computed(() =>
    [...activeMinutes.value].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    )
  );

  async function loadForSubject(subjectId: number) {
    minutes.value = await db.meetingMinutes
      .where('subjectId')
      .equals(subjectId)
      .toArray();
  }

  async function loadRecent(limit = 10) {
    minutes.value = await db.meetingMinutes
      .filter((m) => !m.deleted)
      .reverse()
      .sortBy('date');
    minutes.value = minutes.value.slice(0, limit);
  }

  async function createMinutes(data: {
    subjectId: number;
    title: string;
    date: Date;
    content?: string;
  }) {
    const now = new Date();
    await db.meetingMinutes.add({
      subjectId: data.subjectId,
      title: data.title,
      content: data.content ?? '',
      date: data.date,
      deleted: false,
      createdAt: now,
      updatedAt: now,
    });
  }

  async function updateMinutes(id: number, data: Partial<MeetingMinutes>) {
    await db.meetingMinutes.update(id, { ...data, updatedAt: new Date() });
    const item = await db.meetingMinutes.get(id);
    if (item) {
      await loadForSubject(item.subjectId);
    }
  }

  async function deleteMinutes(id: number) {
    await updateMinutes(id, { deleted: true });
  }

  return {
    minutes,
    activeMinutes,
    sortedMinutes,
    loadForSubject,
    loadRecent,
    createMinutes,
    updateMinutes,
    deleteMinutes,
  };
});

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useMinutesStore, import.meta.hot));
}
