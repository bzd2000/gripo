export interface ElectronAPI {
  dbSync: (payload: { table: string; op: string; id?: number; data?: Record<string, unknown> }) => void;
  dbRestore: () => Promise<Record<string, unknown[]>>;
  dbGetPath: () => Promise<string | undefined>;
  dbSetPath: (newPath: string) => Promise<void>;
  dbPickPath: () => Promise<string | null>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}
