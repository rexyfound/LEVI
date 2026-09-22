# LEVI Lightweight Personal Assistant Backend

LEVI now keeps `backend/ui.py` as the lightweight user interface and concentrates orchestration in the existing Python backend. The system is not a chatbot-only wrapper: `run_agent()` classifies each request, selects a specialist role, uses approved tools, remembers important context, and speaks the final answer when voice output is enabled.

## Specialist routing

| Request type | Primary providers | Typical work |
|---|---|---|
| Coding | Claude, optional Manus advisory delegate, OpenRouter, Ollama | Repository changes, debugging, tests, terminal work |
| Design | Gemini, OpenRouter, Ollama | UI/UX direction, visual analysis, styling, mockups |
| Research | Gemini, OpenRouter, Ollama | Comparisons, summaries, current-information tasks |
| Automation | Claude, OpenRouter, Ollama | Browser, desktop, filesystem, and personal workflows |
| General assistant | OpenRouter, Gemini, Ollama | Conversation, planning, reminders, and everyday help |

The router skips providers whose credentials are absent, remembers failing providers for a short period, and falls back automatically. `LEVI_PROVIDER_ORDER` can override the role defaults with a comma-separated list when needed.

## Voice

The existing `voice_manager` remains the only voice pipeline. The agent sends its final answer to `speak()` without blocking the task loop. `TTS_PROVIDER=edge` is the lightweight default; OpenAI and ElevenLabs remain optional alternatives. Voice errors do not fail the main assistant response.

## MCP

MCP is optional and lazy. Configure servers through `MCP_SERVERS_FILE` or `MCP_SERVERS_JSON`. LEVI starts a configured stdio server only when a request needs its discovered tools, exposes those tools through the existing provider tool schema, and shuts the processes down with FastAPI. MCP actions still pass through LEVI’s normal tool result and confirmation flow.

Example configuration:

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "D:/Projects"]
    }
  }
}
```

## Memory and personal behavior

LEVI stores lightweight JSON memory under `LEVI_DATA_DIR` when configured, or inside the backend data directory by default. The memory bridge searches local memory first when OpenClaw is not installed, so recall does not depend on an external process. Use the existing memory tools for durable preferences, project settings, and summaries; never store secrets.

## Simple startup

For normal Windows use, double-click `run-levi.bat`. It creates the virtual environment, installs dependencies only on first run, configures writable personal-assistant data under `%USERPROFILE%\\.levi`, and starts the existing lightweight `backend/ui.py`.

To start it manually, run:

```bat
cd /d D:\Projects\LEVI
.venv\Scripts\activate
python backend\ui.py
```

For API/WebSocket mode, use the existing FastAPI command. The desktop shell is optional and should not be required for backend development.

## Configuration rule

Keep all credentials in a local `.env` file that is excluded from Git. Copy `.env.example` to `.env`, fill only the providers you intend to use, and leave the others blank. OpenRouter and Ollama are the practical backup path when specialist cloud providers are unavailable.
