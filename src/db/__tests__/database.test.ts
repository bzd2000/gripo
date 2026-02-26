import { describe, it, expect, beforeEach } from 'vitest';
import { db } from '../database';

describe('GripoDB', () => {
  beforeEach(async () => {
    await db.delete();
    await db.open();
  });

  it('has subjects table', () => {
    expect(db.subjects).toBeDefined();
  });

  it('has tasks table', () => {
    expect(db.tasks).toBeDefined();
  });

  it('has agendaPoints table', () => {
    expect(db.agendaPoints).toBeDefined();
  });

  it('has meetingMinutes table', () => {
    expect(db.meetingMinutes).toBeDefined();
  });

  it('can add and retrieve a subject', async () => {
    const id = await db.subjects.add({
      name: 'Test Project',
      type: 'project',
      color: '#4A90D9',
      pinned: false,
      archived: false,
      createdAt: new Date(),
      updatedAt: new Date(),
    });

    const subject = await db.subjects.get(id);
    expect(subject?.name).toBe('Test Project');
    expect(subject?.type).toBe('project');
  });
});
