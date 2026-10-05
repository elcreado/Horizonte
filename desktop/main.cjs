const { app, BrowserWindow, Menu, ipcMain, dialog } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
const { validateEndpoint } = require('./endpoint.cjs');
let window;
let setupWindow;
let endpoint;
const configPath = () => path.join(app.getPath('userData'), 'server.json');
const setupUrl = pathToFileURL(path.join(__dirname, 'setup.html')).href;
const smoke = process.argv.includes('--smoke-test');
function denyPermissions(session) {
  session.setPermissionCheckHandler(() => false);
  session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
  session.setDevicePermissionHandler(() => false);
}
if (smoke) {
  const profile = fs.mkdtempSync(path.join(app.getPath('temp'), 'horizonte-smoke-'));
  app.setPath('userData', profile);
}

function openSetup() {
  if (setupWindow && !setupWindow.isDestroyed()) { setupWindow.focus(); return; }
  setupWindow = new BrowserWindow({ width: 980, height: 720, show: false,
    webPreferences: { preload: path.join(__dirname, 'setup-preload.cjs'), nodeIntegration: false, contextIsolation: true, sandbox: true, offscreen: smoke } });
  denyPermissions(setupWindow.webContents.session);
  setupWindow.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  setupWindow.webContents.on('will-navigate', (event) => event.preventDefault());
  setupWindow.once('ready-to-show', () => { if (!smoke) setupWindow.show(); });
  if (smoke) setupWindow.webContents.once('did-finish-load', async () => {
    try {
      const result = await setupWindow.webContents.executeJavaScript(`(async () => {
        let blocked = false;
        try { await window.horizonteSetup.connect('http://example.com'); } catch { blocked = true; }
        const permissions = await Promise.all(['geolocation', 'camera', 'microphone'].map(async name => ({ name, state: (await navigator.permissions.query({ name })).state })));
        return { title: document.title, input: Boolean(document.getElementById('server')),
          nodeHidden: typeof window.require === 'undefined' && typeof window.process === 'undefined',
          invalidEndpointBlocked: blocked, permissions };
      })()`);
      if (!result.input || !result.nodeHidden || !result.invalidEndpointBlocked) throw new Error('Falló smoke test');
      if (result.permissions.some(permission => permission.state !== 'denied')) throw new Error('Permisos no bloqueados');
      await new Promise((resolve) => setTimeout(resolve, 500));
      const output = process.env.HORIZONTE_SMOKE_OUTPUT;
      if (output) {
        fs.mkdirSync(output, { recursive: true });
        fs.writeFileSync(path.join(output, 'setup.png'), (await setupWindow.webContents.capturePage()).toPNG());
        fs.writeFileSync(path.join(output, 'result.json'), JSON.stringify(result));
      }
      app.exit(0);
    } catch (error) { console.error(error); app.exit(1); }
  });
  setupWindow.loadFile(path.join(__dirname, 'setup.html'));
}

async function openApplication() {
  const previous = window;
  window = new BrowserWindow({ width: 1440, height: 960, minWidth: 780, minHeight: 600, show: false,
    webPreferences: { nodeIntegration: false, contextIsolation: true, sandbox: true, webSecurity: true, partition: 'persist:horizonte' } });
  const current = window;
  if (previous && !previous.isDestroyed()) previous.close();
  denyPermissions(current.webContents.session);
  current.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
  const restrict = (event, url) => { try { if (new URL(url).origin !== endpoint) event.preventDefault(); } catch { event.preventDefault(); } };
  current.webContents.on('will-navigate', restrict);
  current.webContents.on('will-redirect', restrict);
  current.once('ready-to-show', () => current.show());
  try { await current.loadURL(endpoint + '/#/'); }
  catch {
    // Una carga reemplazada puede fallar al cerrar su ventana; no mostrar un aviso obsoleto.
    if (current.isDestroyed() || current !== window) return;
    current.show();
    const { response } = await dialog.showMessageBox(current, {
      type: 'error', title: 'Servidor no disponible', message: 'No se pudo conectar con Horizonte.',
      detail: 'Comprueba internet y la dirección del servidor. Si el servidor gratuito está suspendido, su primera conexión puede tardar; espera y reintenta. Tus datos permanecen en el servidor.',
      buttons: ['Reintentar', 'Configurar servidor', 'Cerrar aviso'], defaultId: 0, cancelId: 2,
    });
    if (current.isDestroyed() || current !== window) return;
    if (response === 0) await openApplication();
    else if (response === 1) openSetup();
  }
}

if (!app.requestSingleInstanceLock()) app.quit();
else {
  app.on('second-instance', () => { const target = setupWindow && !setupWindow.isDestroyed() ? setupWindow : window; if (target) { if (target.isMinimized()) target.restore(); target.focus(); } });
  app.whenReady().then(() => {
    Menu.setApplicationMenu(Menu.buildFromTemplate([
      { label: 'Servidor', submenu: [{ label: 'Configurar conexión', click: openSetup }, { label: 'Reintentar', click: () => endpoint ? openApplication() : openSetup() }, { type: 'separator' }, { role: 'quit', label: 'Salir' }] },
      { label: 'Vista', submenu: [{ role: 'reload', label: 'Recargar' }, { role: 'resetZoom' }, { role: 'zoomIn' }, { role: 'zoomOut' }] },
      { label: 'Edición', submenu: [{ role: 'undo' }, { role: 'redo' }, { role: 'cut' }, { role: 'copy' }, { role: 'paste' }, { role: 'selectAll' }] },
    ]));
    ipcMain.handle('configure-server', async (event, value) => {
      if (event.senderFrame.url !== setupUrl) throw new Error('Solicitud no autorizada.');
      const next = validateEndpoint(value, !app.isPackaged);
      if (next !== endpoint && window && !window.isDestroyed()) await window.webContents.session.clearStorageData();
      fs.writeFileSync(configPath(), JSON.stringify({ endpoint: next }), { encoding: 'utf8', mode: 0o600 });
      endpoint = next;
      const opening = openApplication();
      setupWindow.close();
      await opening;
    });
    try { endpoint = validateEndpoint(JSON.parse(fs.readFileSync(configPath(), 'utf8')).endpoint, !app.isPackaged); }
    catch { endpoint = null; }
    if (endpoint) openApplication(); else openSetup();
  });
  app.on('window-all-closed', () => app.quit());
}
