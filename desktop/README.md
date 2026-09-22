# LEVI Native Desktop Window

The `desktop` folder contains the Electron shell for LEVI. It starts the FastAPI backend, waits for `http://127.0.0.1:8000/` to respond, and opens the LEVI interface in a native desktop window. In development mode it also starts the Vite frontend server. In packaged mode it loads `frontend/dist/index.html` from the application resources.

## Development

From a Windows Command Prompt at the project root:

```bat
cd /d D:\Projects\LEVI
.venv\Scripts\activate
set LEVI_REPO_ROOT=D:\Projects\LEVI
cd desktop
npm install
npm run dev
```

The native window opens with the Vite development server. Hot reload remains available, and Electron DevTools open automatically.

## Portable Windows build

Build the frontend first:

```bat
cd /d D:\Projects\LEVI\frontend
npm install
npm run build
```

Then build the portable desktop executable:

```bat
cd /d D:\Projects\LEVI\desktop
npm install
npm run dist
```

The portable executable is written to `desktop/dist/`. The target machine still needs Python, the LEVI Python dependencies, and provider credentials unless the backend is later bundled with a Python packager such as PyInstaller.

## Browser fallback

For a one-command browser-mode launch, run `desktop\\run-browser-dev.bat`. It opens separate backend and frontend terminals and then opens the local UI in the default browser.

The browser workflow remains available manually:

```bat
cd /d D:\Projects\LEVI\backend
.venv\Scripts\activate
python -m uvicorn main:app --reload --port 8000
```

In a second terminal:

```bat
cd /d D:\Projects\LEVI\frontend
npm run dev
```

Open the Vite URL, normally `http://localhost:3000`, in Chrome or Edge.

## Environment

The desktop shell recognizes these optional variables:

```bat
set LEVI_PYTHON=D:\Projects\LEVI\.venv\Scripts\python.exe
set LEVI_REPO_ROOT=D:\Projects\LEVI
set LEVI_REPO_POLL_SECONDS=1.0
set LEVI_DATA_DIR=%APPDATA%\LEVI\data
```

Keep API keys outside tracked files. Use a local `.env` file or Windows environment variables and rotate any credential that was previously exposed in the old run instructions.
