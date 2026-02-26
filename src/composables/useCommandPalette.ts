export type ParsedCreate = {
  type: 'create';
  entityType: 'task' | 'agenda' | 'minutes' | 'subject';
  title: string;
  subjectName: string | undefined;
};

export type ParsedSearch = {
  type: 'search';
  query: string;
};

export type ParsedCommand = {
  type: 'command';
  command: string;
  args: string;
};

export type ParsedInput = ParsedCreate | ParsedSearch | ParsedCommand;

const PREFIXES: Record<string, ParsedCreate['entityType']> = {
  't:': 'task',
  'a:': 'agenda',
  'm:': 'minutes',
  's:': 'subject',
};

export function parseCommand(input: string): ParsedInput {
  const trimmed = input.trim();

  // Command mode
  if (trimmed.startsWith('/')) {
    const parts = trimmed.slice(1).split(/\s+/);
    return {
      type: 'command',
      command: parts[0] ?? '',
      args: parts.slice(1).join(' '),
    };
  }

  // Create mode
  for (const [prefix, entityType] of Object.entries(PREFIXES)) {
    if (trimmed.startsWith(prefix)) {
      const rest = trimmed.slice(prefix.length).trim();
      const subjectMatch = rest.match(/@(\S+)\s*$/);
      const title = subjectMatch
        ? rest.slice(0, subjectMatch.index).trim()
        : rest;
      return {
        type: 'create',
        entityType,
        title,
        subjectName: subjectMatch?.[1],
      };
    }
  }

  // Search mode
  return {
    type: 'search',
    query: trimmed,
  };
}
