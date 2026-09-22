# LEVI

> Autonomous Desktop AI Operating System

LEVI is an AI agent capable of:

- Multi-provider routing (Gemini, Groq, Ollama)
- Browser automation
- Desktop automation
- Long-term memory
- File operations
- Terminal execution
- Intelligent tool selection

## Roadmap

- [x] Browser Agent
- [x] Desktop Agent
- [x] Memory
- [x] Tool Router
- [ ] Vision
- [ ] Planner V2
- [ ] React Frontend
- [ ] Voice

## Local Repository Watcher

LEVI now includes a read-only local repository watcher. When the backend starts, it polls the configured checkout and publishes batched file-change events through the existing WebSocket connection at `/ws/agent`. Generated output, dependency folders, caches, media artifacts, and `.git` are ignored to keep the event stream useful. The watcher does not execute commands or read file contents.

For the Windows checkout used by this project, configure the repository path before starting the backend:

```bat
set LEVI_REPO_ROOT=D:\Projects\LEVI
set LEVI_REPO_POLL_SECONDS=1.0
```

The current one-shot watcher status is available at `GET http://localhost:8000/repo/status`. The frontend console and activity timeline display `repo_watcher_ready`, `repo_changed`, and `repo_watcher_error` events.

Keep provider credentials in local environment variables or an ignored `.env` file. Never place API keys in run instructions, source files, screenshots, or Git history. If a credential has already been committed, revoke it and create a replacement before continuing.
