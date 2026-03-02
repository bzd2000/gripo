import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  dbSync: (payload: { table: string; op: string; id?: number; data?: Record<string, unknown> }) => {
    ipcRenderer.send('db:sync', payload);
  },
  dbRestore: (): Promise<Record<string, unknown[]>> => {
    return ipcRenderer.invoke('db:restore');
  },
  dbGetPath: (): Promise<string | undefined> => {
    return ipcRenderer.invoke('db:get-path');
  },
  dbSetPath: (newPath: string): Promise<void> => {
    return ipcRenderer.invoke('db:set-path', newPath);
  },
  dbPickPath: (): Promise<string | null> => {
    return ipcRenderer.invoke('db:pick-path');
  },
});
