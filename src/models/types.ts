export type SubjectType = 'project' | 'person' | 'team' | 'board' | 'other';
export type TaskStatus = 'todo' | 'in-progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high';

export interface Subject {
  id?: number;
  name: string;
  type: SubjectType;
  color: string;
  pinned: boolean;
  archived: boolean;
  startDate?: Date;
  endDate?: Date;
  createdAt: Date;
  updatedAt: Date;
}

export interface Task {
  id?: number;
  subjectId: number;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate?: Date;
  deleted: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface AgendaPoint {
  id?: number;
  subjectId: number;
  title: string;
  content: string;
  resolved: boolean;
  deleted: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface MeetingMinutes {
  id?: number;
  subjectId: number;
  title: string;
  content: string;
  date: Date;
  deleted: boolean;
  createdAt: Date;
  updatedAt: Date;
}
