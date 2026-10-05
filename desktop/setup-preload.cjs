const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('horizonteSetup', {
  connect: (url) => ipcRenderer.invoke('configure-server', url),
});
