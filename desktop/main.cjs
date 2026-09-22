const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = 8000;
const FRONTEND_DEV_PORT = 3000;
const isDevelopment = process.env.LEVI_DESKTOP_DEV === '1';

let backendProcess = null;
let frontendProcess = null;
let mainWindow = null;

function projectRoot() {
  const sourceRoot = path.resolve(__dirname, '..');
  const sourceFrontend = path.join(sourceRoot, 'frontend', 'dist', 'index.html');
  if (isDevelopment || fs.existsSync(sourceFrontend)) return sourceRoot;
  return process.resourcesPath;
}

function backendRoot() {
  return path.join(projectRoot(), 'backend');
}

function frontendDistRoot() {
  return path.join(projectRoot(), 'frontend', 'dist');
}

function pythonExecutable() {
  if (process.env.LEVI_PYTHON) return process.env.LEVI_PYTHON;
  const candidates = [
    path.join(projectRoot(), '.venv', 'Scripts', 'python.exe'),
    'D:\\Projects\\LEVI\\.venv\\Scripts\\python.exe',
  ];
  const available = candidates.find((candidate) => fs.existsSync(candidate));
  return available || 'python';
}

function defaultRepositoryRoot() {
  const conventionalRoot = 'D:\\Projects\\LEVI';
  if (fs.existsSync(conventionalRoot)) return conventionalRoot;
  return isDevelopment ? projectRoot() : path.dirname(process.execPath);
}

function childEnvironment() {
  return {
    ...process.env,
    LEVI_REPO_ROOT: process.env.LEVI_REPO_ROOT || defaultRepositoryRoot(),
    LEVI_REPO_POLL_SECONDS: process.env.LEVI_REPO_POLL_SECONDS || '1.0',
    LEVI_DATA_DIR: process.env.LEVI_DATA_DIR || path.join(app.getPath('userData'), 'data'),
    PYTHONUNBUFFERED: '1',
  };
}

function logChildOutput(label, child) {
  child.stdout?.on('data', (data) => console.log(`[${label}] ${data.toString().trimEnd()}`));
  child.stderr?.on('data', (data) => console.error(`[${label}] ${data.toString().trimEnd()}`));
  child.on('error', (error) => console.error(`[${label}] process error`, error));
  child.on('exit', (code, signal) => console.log(`[${label}] exited code=${code} signal=${signal || 'none'}`));
}

function startBackend() {
  const executable = pythonExecutable();
  backendProcess = spawn(
    executable,
    ['-m', 'uvicorn', 'main:app', '--host', BACKEND_HOST, '--port', String(BACKEND_PORT)],
    {
      cwd: backendRoot(),
      env: childEnvironment(),
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    },
  );
  logChildOutput('LEVI backend', backendProcess);
}

function findNpmCommand() {
  const nodeDirectory = path.dirname(process.execPath);
  const candidates = [
    path.join(process.env.ProgramW6432 || process.env.ProgramFiles || 'C:\\Program Files', 'nodejs', 'npm.cmd'),
    path.join(process.env.ProgramFiles || 'C:\\Program Files', 'nodejs', 'npm.cmd'),
    path.join(process.env.ProgramFiles || 'C:\\Program Files', 'nodejs', 'npm'),
    path.join(nodeDirectory, 'npm.cmd'),
    'npm.cmd',
    process.env.npm_execpath,
    'npm',
  ].filter(Boolean);
  return candidates.find((candidate) => candidate === 'npm' || candidate === 'npm.cmd' || fs.existsSync(candidate));
}

function startFrontendDevServer() {
  const rawNpmCommand = findNpmCommand();
  if (!rawNpmCommand) throw new Error('npm was not found. Install Node.js or set npm_execpath before starting LEVI.');
  const npmCommand = String(rawNpmCommand).replace(/^['"]|['"]$/g, '');
  const frontendArgs = ['run', 'dev', '--', '--host', BACKEND_HOST, '--port', String(FRONTEND_DEV_PORT)];

  if (process.platform === 'win32') {
    const commandLine = `call "${npmCommand}" ${frontendArgs.join(' ')}`;
    frontendProcess = spawn(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', commandLine], {
      cwd: path.join(projectRoot(), 'frontend'),
      env: childEnvironment(),
      windowsHide: true,
      windowsVerbatimArguments: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  } else {
    frontendProcess = spawn(npmCommand, frontendArgs, {
      cwd: path.join(projectRoot(), 'frontend'),
      env: childEnvironment(),
      windowsHide: true,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
  }
  logChildOutput('LEVI frontend', frontendProcess);
}

function waitForHttpService(port, label, timeoutMs = 30000) {
  const startedAt = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const request = http.get(
        { host: BACKEND_HOST, port, path: '/', timeout: 1500 },
        (response) => {
          response.resume();
          if (response.statusCode && response.statusCode < 500) {
            resolve();
          } else {
            retry();
          }
        },
      );
      request.on('error', retry);
      request.on('timeout', () => request.destroy());
    };

    const retry = () => {
      if (Date.now() - startedAt >= timeoutMs) {
        reject(new Error(`${label} did not become ready within 30 seconds.`));
        return;
      }
      setTimeout(check, 250);
    };

    check();
  });
}

function waitForBackend(timeoutMs = 30000) {
  return waitForHttpService(BACKEND_PORT, 'LEVI backend', timeoutMs);
}

function waitForFrontend(timeoutMs = 30000) {
  return waitForHttpService(FRONTEND_DEV_PORT, 'LEVI frontend', timeoutMs);
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1024,
    minHeight: 700,
    title: 'LEVI',
    backgroundColor: '#05030a',
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      spellcheck: false,
    },
  });

  if (isDevelopment) {
    const rendererUrl = `http://${BACKEND_HOST}:${FRONTEND_DEV_PORT}`;
    mainWindow.webContents.on('did-fail-load', (_event, errorCode, errorDescription, _validatedURL, isMainFrame) => {
      if (isMainFrame && mainWindow && !mainWindow.isDestroyed()) {
        console.error(`[LEVI renderer] load failed ${errorCode}: ${errorDescription}`);
        setTimeout(() => mainWindow?.loadURL(rendererUrl), 500);
      }
    });
    mainWindow.loadURL(rendererUrl);
    if (process.env.LEVI_OPEN_DEVTOOLS === '1') {
      mainWindow.webContents.openDevTools({ mode: 'detach' });
    }
  } else {
    const indexFile = path.join(frontendDistRoot(), 'index.html');
    if (!fs.existsSync(indexFile)) {
      throw new Error(`Packaged frontend not found at ${indexFile}. Run npm run build in frontend first.`);
    }
    mainWindow.loadFile(indexFile);
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function stopProcess(child) {
  if (!child || child.killed) return;
  if (process.platform === 'win32') {
    spawn('taskkill', ['/pid', String(child.pid), '/T', '/F'], { windowsHide: true });
  } else {
    child.kill('SIGTERM');
  }
}

function stopChildren() {
  stopProcess(frontendProcess);
  stopProcess(backendProcess);
  frontendProcess = null;
  backendProcess = null;
}

async function boot() {
  try {
    startBackend();
    if (isDevelopment) startFrontendDevServer();
    await waitForBackend();
    if (isDevelopment) await waitForFrontend();
    createMainWindow();
  } catch (error) {
    console.error('[LEVI desktop] startup failed', error);
    dialog.showErrorBox('LEVI could not start', error.message || String(error));
    stopChildren();
    app.quit();
  }
}

app.whenReady().then(boot);
app.on('before-quit', stopChildren);
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) boot();
});
