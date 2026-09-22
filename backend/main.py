import asyncio
import json
import subprocess

try:
    import psutil
except ImportError:
    psutil = None

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from pending_actions import (
    get_pending_action,
    remove_pending_action
)
from assistant_service import run_assistant

from event_bus import event_bus

from services.background_monitor import in_background_check_topics
from services.proactive_engine import proactive_engine
from services.repo_watcher import get_repo_status, repo_watcher_loop
from integrations.mcp_manager import mcp_manager
from voice.wake_listener import wake_listener

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    event_bus.set_loop(loop)
    asyncio.create_task(periodic_telemetry_loop())
    asyncio.create_task(in_background_check_topics(event_bus))
    asyncio.create_task(periodic_proactive_loop())
    asyncio.create_task(repo_watcher_loop(event_bus))
    # Start the optional local wake listener without blocking API startup.
    wake_listener.start()

@app.on_event("shutdown")
async def shutdown_event():
    wake_listener.stop()
    mcp_manager.shutdown()


async def periodic_telemetry_loop():
    while True:
        if psutil is None:
            await asyncio.sleep(3)
            continue
        try:
            cpu = psutil.cpu_percent(interval=None)

            ram = psutil.virtual_memory()
            await event_bus.emit("system_metrics", {
                "cpu": {"usage": cpu},
                "ram": {
                    "usage": ram.percent,
                    "used_gb": round(ram.used / (1024**3), 2),
                    "total_gb": round(ram.total / (1024**3), 2)
                }
            })
        except Exception:
            pass
        await asyncio.sleep(3)

async def periodic_proactive_loop():
    while True:
        await asyncio.sleep(300) # Check every 5 minutes
        try:
            p_data = proactive_engine.generate_proactive_prompt()
            if p_data:
                await event_bus.emit("proactive_message", p_data)
        except Exception:
            pass



@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "status": "error",
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"(file://.*|http://(localhost|127\.0\.0\.1)(:\d+)?)",
    allow_origins=[
        "null",
        "file://",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    await event_bus.connect(websocket)
    try:
        while True:
            data_str = await websocket.receive_text()
            # Handle client incoming socket pings or commands
            try:
                data = json.loads(data_str)
                if data.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        event_bus.disconnect(websocket)

class Command(BaseModel):
    message: str
    session_id: str | None = None

class Approval(BaseModel):
    action_id: str
    approved: bool

@app.get("/")
def root():
    return {
        "name": "LEVI",
        "status": "online"
    }


@app.post("/chat")
def chat(command: Command):
    result = run_assistant(command.message, command.session_id)
    return {
        "response": result.get("response", ""),
        "status": result.get("status", "complete"),
        "pending_action": result.get("pending_action"),
    }


@app.post("/voice/stop")
def voice_stop():
    try:
        from voice import stop_speaking
        stop_speaking()
        return {"success": True, "status": "stopped"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/voice/state")
def voice_state():
    try:
        from voice import get_voice_state, is_speaking
        state = get_voice_state()
        return {
            "state": state.value if hasattr(state, "value") else str(state),
            "is_speaking": is_speaking(),
        }
    except Exception as e:
        return {"state": "UNKNOWN", "error": str(e)}



@app.get("/repo/status")
def repo_status():
    return get_repo_status()


@app.get("/wake/status")
def wake_status():
    return wake_listener.status()


@app.post("/wake/start")
def wake_start():
    return {"success": wake_listener.start(), "status": wake_listener.status()}


@app.post("/wake/stop")
def wake_stop():
    wake_listener.stop()
    return {"success": True, "status": wake_listener.status()}


@app.post("/wake/restart")
def wake_restart():
    return {"success": wake_listener.restart(), "status": wake_listener.status()}


@app.get("/mcp/status")
def mcp_status():
    return mcp_manager.status()


@app.get("/system")
def system_info():

    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()

    gpu_info = {}

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

        values = result.stdout.strip().split(",")

        gpu_info = {
            "name": values[0].strip(),
            "usage": float(values[1]),
            "vram_used": float(values[2]),
            "vram_total": float(values[3]),
            "temperature": float(values[4])
        }

    except Exception:
        gpu_info = {
            "status": "unavailable"
        }

    return {
        "cpu": {
            "usage": cpu
        },
        "ram": {
            "usage": ram.percent,
            "used_gb": round(ram.used / (1024**3), 2),
            "total_gb": round(ram.total / (1024**3), 2)
        },
        "gpu": gpu_info
    }

@app.post("/agent")
def agent(command: Command):
   return run_assistant(command.message, command.session_id)

@app.post("/approve")
def approve_action(approval: Approval):

    action = get_pending_action(
        approval.action_id
    )

    if not action:
        return {
            "success": False,
            "error": "Action not found or expired"
        }

    if not approval.approved:
        remove_pending_action(
            approval.action_id
        )

        return {
            "success": True,
            "status": "denied"
        }

    if action["type"] == "overwrite_file":

        data = action["data"]

        try:
            with open(
                data["path"],
                "w",
                encoding="utf-8"
            ) as file:
                file.write(data["content"])

            remove_pending_action(
                approval.action_id
            )

            return {
                "success": True,
                "status": "executed",
                "action": "overwrite_file",
                "path": data["path"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    if action["type"] == "run_terminal":
        data = action["data"]
        command = data.get("command", "")

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd="D:/Projects",
                capture_output=True,
                text=True,
                timeout=30
            )

            remove_pending_action(approval.action_id)

            return {
                "success": True,
                "status": "executed",
                "action": "run_terminal",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    if action["type"] == "launch_app":
        data = action["data"]
        app_path = data.get("path", "")

        try:
            subprocess.Popen(app_path)

            remove_pending_action(approval.action_id)

            return {
                "success": True,
                "status": "executed",
                "action": "launch_app",
                "path": app_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    return {
        "success": False,
        "error": "Unsupported action type"
    }
