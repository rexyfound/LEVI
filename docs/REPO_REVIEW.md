# LEVI Project Review and Local Watcher

## Executive summary

The uploaded LEVI snapshot is a Windows-oriented desktop AI application with a FastAPI backend, a React/Vite frontend, model-provider routing, desktop and browser tools, persistent JSON memory, voice support, and an existing hourly external-topic monitor. The existing monitor is not a repository watcher: it checks configured news topics and emits `monitor_alert` events.

A read-only local repository watcher has now been added. It polls the configured checkout, ignores dependency folders and generated artifacts, batches added/modified/deleted file events, and publishes them through LEVI’s existing WebSocket event bus. The watcher does not execute shell commands and does not read file contents.

## Changes made

| Area | Change | Purpose |
|---|---|---|
| Backend watcher | Added `backend/services/repo_watcher.py` | Detect local repository changes using standard-library metadata polling |
| Backend startup | Updated `backend/main.py` | Start the watcher with FastAPI and add `GET /repo/status` |
| WebSocket events | Added `repo_watcher_ready`, `repo_changed`, and `repo_watcher_error` | Provide live status and change notifications to the UI |
| Frontend state | Updated `frontend/src/types/events.ts` and `frontend/src/store/agentStore.ts` | Render watcher activity in the console and timeline |
| Configuration | Added `.env.example` and updated `to run` | Document local Windows configuration without retaining credentials |
| Documentation | Updated `README.MD` | Explain watcher behavior and safe secret handling |
| Tests | Added `backend/tests/test_repo_watcher.py` | Verify ignored paths and change classification |

## Windows startup

Open Command Prompt in the project directory and configure the repository path before starting the backend:

```bat
cd /d D:\Projects\LEVI
.venv\Scripts\activate
set LEVI_REPO_ROOT=D:\Projects\LEVI
set LEVI_REPO_POLL_SECONDS=1.0
cd backend
python -m uvicorn main:app --reload --port 8000
```

Start the frontend in a separate Command Prompt:

```bat
cd /d D:\Projects\LEVI\frontend
npm install
npm run dev
```

The watcher status endpoint is `http://localhost:8000/repo/status`. When the frontend is connected to `ws://localhost:8000/ws/agent`, repository changes appear in the LEVI console and activity timeline.

## Validation

The backend source compiled successfully, and the focused watcher test suite passed with two tests. Frontend build validation was not run because the uploaded snapshot did not include `frontend/node_modules`; run `npm install` on Windows and then `npm run build` locally.

## Important existing issues

The project still contains broader platform and runtime assumptions that should be addressed in a later pass. Several backend tools hardcode `D:/Projects`, desktop automation is Windows-specific, and the uploaded snapshot includes generated artifacts and a bundled virtual environment. The backend and frontend also have event-model gaps for some older proactive and topic-monitor events.

A provider credential was present in the original `to run` file. The delivered copy has been sanitized, but the credential should be revoked and replaced immediately if it was ever active or committed to Git. Store replacement credentials only in local environment variables or an ignored `.env` file, and consider removing the compromised value from repository history.

## Native desktop window

The `desktop` folder now contains an Electron shell. In development mode it starts the backend and Vite server, waits for the backend health endpoint, and opens the React UI in a native window. In packaged mode it loads the built frontend from local resources and starts the backend as a child process. The browser workflow remains available for development and fallback use.

From Windows, the fastest native development launch is:

```bat
cd /d D:\Projects\LEVI
desktop\run-native-dev.bat
```

For a portable build, run `npm install` and `npm run dist` inside `desktop` after building the frontend with `npm run build`. The current portable shell expects Python and the LEVI dependencies to be installed on the target machine; a later packaging pass can embed the backend with PyInstaller if a single self-contained installer is required.

## Monitoring scope

The watcher reports file metadata changes. It does not automatically run tests, builds, formatters, or arbitrary commands. This is intentional: automatic command execution can be unsafe and can create noisy or expensive feedback loops. A future enhancement can add explicit, allowlisted checks such as backend syntax validation and frontend build execution behind a user-controlled setting.
