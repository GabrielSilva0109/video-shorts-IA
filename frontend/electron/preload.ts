import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  // App info
  getVersion: () => ipcRenderer.invoke('app:version'),

  // Shell
  openPath: (p: string) => ipcRenderer.invoke('shell:openPath', p),
  showInFolder: (p: string) => ipcRenderer.invoke('shell:showItemInFolder', p),

  // Window controls
  minimize: () => ipcRenderer.send('window:minimize'),
  maximize: () => ipcRenderer.send('window:maximize'),
  close: () => ipcRenderer.send('window:close'),
});
