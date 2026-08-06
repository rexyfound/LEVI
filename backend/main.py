from pending_actions import (
    get_pending_action,
    remove_pending_action
)
from agent import run_agent
import psutil
import subprocess
from fastapi import FastAPI
from pydantic import BaseModel

from ollama_client import ask_ollama

app = FastAPI()

class Command(BaseModel):
    message: str

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

    messages = [
        {
            "role": "system",
            "content": """
You are LEVI, a local desktop AI assistant.

Be concise and technical.
Help with programming, debugging and computer tasks.
Never claim a tool was executed unless it actually was.
"""
        },
        {
            "role": "user",
            "content": command.message
        }
    ]

    answer = ask_ollama(messages)

    return {
        "response": answer
    }



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
   return run_agent(command.message)

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

    return {
        "success": False,
        "error": "Unsupported action type"
    }