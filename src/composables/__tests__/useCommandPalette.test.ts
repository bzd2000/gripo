import { describe, it, expect } from 'vitest';
import { parseCommand } from '../useCommandPalette';

describe('parseCommand', () => {
  it('parses task creation', () => {
    const result = parseCommand('t: Buy supplies @ProjectAlpha');
    expect(result).toEqual({
      type: 'create',
      entityType: 'task',
      title: 'Buy supplies',
      subjectName: 'ProjectAlpha',
    });
  });

  it('parses agenda creation', () => {
    const result = parseCommand('a: Discuss budget @John');
    expect(result).toEqual({
      type: 'create',
      entityType: 'agenda',
      title: 'Discuss budget',
      subjectName: 'John',
    });
  });

  it('parses minutes creation', () => {
    const result = parseCommand('m: Weekly standup @DesignTeam');
    expect(result).toEqual({
      type: 'create',
      entityType: 'minutes',
      title: 'Weekly standup',
      subjectName: 'DesignTeam',
    });
  });

  it('parses subject creation', () => {
    const result = parseCommand('s: New Client Project');
    expect(result).toEqual({
      type: 'create',
      entityType: 'subject',
      title: 'New Client Project',
      subjectName: undefined,
    });
  });

  it('parses task without subject', () => {
    const result = parseCommand('t: Buy supplies');
    expect(result).toEqual({
      type: 'create',
      entityType: 'task',
      title: 'Buy supplies',
      subjectName: undefined,
    });
  });

  it('returns search for plain text', () => {
    const result = parseCommand('budget meeting');
    expect(result).toEqual({
      type: 'search',
      query: 'budget meeting',
    });
  });

  it('parses command mode', () => {
    const result = parseCommand('/done');
    expect(result).toEqual({
      type: 'command',
      command: 'done',
      args: '',
    });
  });

  it('parses command with args', () => {
    const result = parseCommand('/filter priority:high');
    expect(result).toEqual({
      type: 'command',
      command: 'filter',
      args: 'priority:high',
    });
  });
});
