import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url'
import * as sqliteService from './sqlite-service.js';

// needed in case process is undefined under Linux
const platform = process.platform || os.platform();

const currentDir = fileURLToPath(new URL('.', import.meta.url));

let mainWindow: BrowserWindow | undefined;

async function createWindow() {
  /**
   * Initial window options
   */
  mainWindow = new BrowserWindow({
    icon: path.resolve(currentDir, 'icons/icon.png'), // tray icon
    width: 1000,
    height: 600,
    useContentSize: true,
    webPreferences: {
      contextIsolation: true,
      // More info: https://v2.quasar.dev/quasar-cli-vite/developing-electron-apps/electron-preload-script
      preload: path.resolve(
        currentDir,
        path.join(process.env.QUASAR_ELECTRON_PRELOAD_FOLDER, 'electron-preload' + process.env.QUASAR_ELECTRON_PRELOAD_EXTENSION)
      ),
    },
  });

  // --- SQLite backup init ---
  let dbPath = sqliteService.getDbPath();
  if (!dbPath) {
    const result = dialog.showSaveDialogSync(mainWindow, {
      title: 'Choose backup database location',
      defaultPath: path.join(app.getPath('documents'), 'gripo-backup.db'),
      filters: [{ name: 'SQLite Database', extensions: ['db'] }],
    });
    if (result) {
      await sqliteService.setDbPath(result); // setDbPath calls init() internally
      dbPath = result;
    }
  } else {
    await sqliteService.init(dbPath);
  }

  if (process.env.DEV) {
    await mainWindow.loadURL(process.env.APP_URL);
  } else {
    await mainWindow.loadFile('index.html');
  }

  if (process.env.DEBUGGING) {
    // if on DEV or Production with debug enabled
    mainWindow.webContents.openDevTools();
  } else {
    // we're on production; no access to devtools pls
    mainWindow.webContents.on('devtools-opened', () => {
      mainWindow?.webContents.closeDevTools();
    });
  }

  mainWindow.on('closed', () => {
    mainWindow = undefined;
  });
}

void app.whenReady().then(createWindow);

// --- IPC handlers ---

ipcMain.on('db:sync', (_event, payload) => {
  sqliteService.sync(payload);
});

ipcMain.handle('db:restore', () => {
  return sqliteService.restore();
});

ipcMain.handle('db:get-path', () => {
  return sqliteService.getDbPath();
});

ipcMain.handle('db:set-path', async (_event, newPath: string) => {
  await sqliteService.setDbPath(newPath);
});

ipcMain.handle('db:pick-path', async () => {
  const result = await dialog.showSaveDialog({
    title: 'Choose backup database location',
    defaultPath: path.join(app.getPath('documents'), 'gripo-backup.db'),
    filters: [{ name: 'SQLite Database', extensions: ['db'] }],
  });
  if (!result.canceled && result.filePath) {
    await sqliteService.setDbPath(result.filePath);
    return result.filePath;
  }
  return null;
});

app.on('before-quit', () => {
  sqliteService.close();
});

app.on('window-all-closed', () => {
  if (platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === undefined) {
    void createWindow();
  }
});
