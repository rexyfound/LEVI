"""Lightweight, optional MCP stdio integration for LEVI.

MCP remains lazy: configured servers start only when LEVI needs their tools.
Each server has bounded startup and call timeouts so a broken process cannot
block the assistant indefinitely.
"""
from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import time
from typing import Any


def _seconds(value: Any, default: float) -> float:
    try:
        return max(0.5, float(value))
    except (TypeError, ValueError):
        return default


class MCPServer:
    def __init__(self, name: str, config: dict[str, Any]):
        self.name = name
        self.config = config
        self.process: subprocess.Popen | None = None
        self.lock = threading.RLock()
        self.request_id = 0
        self.tools: list[dict[str, Any]] = []
        self.startup_timeout = _seconds(
            config.get("startupTimeoutSeconds") or os.getenv("MCP_STARTUP_TIMEOUT"),
            12.0,
        )
        self.call_timeout = _seconds(
            config.get("callTimeoutSeconds") or os.getenv("MCP_CALL_TIMEOUT"),
            20.0,
        )
        self.status = "configured"
        self.last_error: str | None = None
        self.last_started_at: float | None = None
        self.last_call_at: float | None = None

    def start(self):
        if self.process and self.process.poll() is None:
            return

        command = self.config.get("command")
        if not command:
            raise ValueError(f"MCP server '{self.name}' has no command")

        env = os.environ.copy()
        env.update({str(k): str(v) for k, v in (self.config.get("env") or {}).items()})
        self.status = "starting"
        self.last_error = None
        self.process = subprocess.Popen(
            [command, *(self.config.get("args") or [])],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
            text=True,
            bufsize=1,
        )
        self.last_started_at = time.time()
        try:
            self._request(
                "initialize",
                {
                    "protocolVersion": self.config.get("protocolVersion", "2024-11-05"),
                    "capabilities": {},
                    "clientInfo": {"name": "LEVI", "version": "0.1"},
                },
                timeout=self.startup_timeout,
            )
            self._notify("notifications/initialized", {})
            self.refresh_tools(timeout=self.startup_timeout)
            self.status = "ready"
        except Exception as exc:
            self.status = "error"
            self.last_error = str(exc)
            self.stop()
            raise

    def stop(self):
        process = self.process
        self.process = None
        self.tools = []
        if not process:
            self.status = "stopped"
            return
        try:
            process.terminate()
            process.wait(timeout=1.5)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
            except OSError:
                pass
        self.status = "stopped"

    def _notify(self, method: str, params: dict[str, Any]):
        if not self.process or not self.process.stdin:
            return
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.process.stdin.flush()

    def _readline_with_timeout(self, timeout: float) -> str:
        if not self.process or not self.process.stdout:
            raise RuntimeError(f"MCP server '{self.name}' is not running")

        result: queue.Queue[str | BaseException] = queue.Queue(maxsize=1)

        def read_line():
            try:
                result.put(self.process.stdout.readline())
            except BaseException as exc:  # pragma: no cover - platform/process dependent
                result.put(exc)

        threading.Thread(target=read_line, daemon=True, name=f"levi-mcp-{self.name}").start()
        try:
            line = result.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError(f"MCP server '{self.name}' timed out after {timeout:g}s") from exc
        if isinstance(line, BaseException):
            raise RuntimeError(f"MCP server '{self.name}' read failed: {line}") from line
        return line

    def _request(self, method: str, params: dict[str, Any] | None = None, timeout: float | None = None):
        with self.lock:
            if not self.process or not self.process.stdin or not self.process.stdout:
                raise RuntimeError(f"MCP server '{self.name}' is not running")
            self.request_id += 1
            request_id = self.request_id
            self.process.stdin.write(
                json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}})
                + "\n"
            )
            self.process.stdin.flush()

            deadline = time.monotonic() + (timeout or self.call_timeout)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"MCP server '{self.name}' timed out")
                line = self._readline_with_timeout(remaining)
                if not line:
                    raise RuntimeError(f"MCP server '{self.name}' closed its output")
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if message.get("id") != request_id:
                    continue
                if message.get("error"):
                    raise RuntimeError(str(message["error"]))
                return message.get("result", {})

    def refresh_tools(self, timeout: float | None = None):
        result = self._request("tools/list", timeout=timeout or self.startup_timeout)
        self.tools = result.get("tools", []) or []
        return self.tools

    def call_tool(self, tool_name: str, arguments: dict[str, Any]):
        self.last_call_at = time.time()
        return self._request(
            "tools/call",
            {"name": tool_name, "arguments": arguments or {}},
            timeout=self.call_timeout,
        )

    def report(self) -> dict[str, Any]:
        running = bool(self.process and self.process.poll() is None)
        return {
            "name": self.name,
            "status": "ready" if running and self.status == "ready" else self.status,
            "running": running,
            "tool_count": len(self.tools),
            "last_error": self.last_error,
            "startup_timeout_seconds": self.startup_timeout,
            "call_timeout_seconds": self.call_timeout,
            "last_started_at": self.last_started_at,
            "last_call_at": self.last_call_at,
        }


class MCPManager:
    def __init__(self):
        self.servers: dict[str, MCPServer] = {}
        self.lock = threading.RLock()
        self._load_config()

    def _load_config(self):
        raw = os.getenv("MCP_SERVERS_JSON", "").strip()
        path = os.getenv("MCP_SERVERS_FILE", "").strip()
        if not raw and path and os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as file:
                    raw = file.read()
            except OSError as exc:
                print(f"[LEVI MCP] Cannot read config file: {exc}")
                return
        if not raw:
            return
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"[LEVI MCP] Invalid MCP configuration: {exc}")
            return

        server_config = config.get("servers", config) if isinstance(config, dict) else {}
        for name, item in server_config.items():
            if isinstance(item, dict):
                self.servers[str(name)] = MCPServer(str(name), item)

    def tool_schemas(self) -> list[dict[str, Any]]:
        schemas = []
        for server in self.servers.values():
            try:
                with self.lock:
                    server.start()
            except Exception as exc:
                server.status = "error"
                server.last_error = str(exc)
                print(f"[LEVI MCP] {server.name} unavailable: {exc}")
                continue
            for tool in server.tools:
                name = f"mcp__{server.name}__{tool.get('name', 'tool')}"
                schemas.append(
                    {
                        "type": "function",
                        "function": {
                            "name": name,
                            "description": f"MCP {server.name}: {tool.get('description', '')}",
                            "parameters": tool.get("inputSchema", {"type": "object", "properties": {}}),
                        },
                    }
                )
        return schemas

    def call(self, qualified_name: str, arguments: dict[str, Any]):
        if not qualified_name.startswith("mcp__"):
            return {"success": False, "error": "Not an MCP tool"}
        try:
            _, server_name, tool_name = qualified_name.split("__", 2)
        except ValueError:
            return {"success": False, "error": "Invalid MCP tool name"}
        server = self.servers.get(server_name)
        if not server:
            return {"success": False, "error": f"Unknown MCP server: {server_name}"}
        try:
            with self.lock:
                server.start()
                return {"success": True, "server": server_name, "result": server.call_tool(tool_name, arguments)}
        except Exception as exc:
            server.status = "error"
            server.last_error = str(exc)
            server.stop()
            return {"success": False, "server": server_name, "error": str(exc)}

    def status(self) -> dict[str, Any]:
        return {
            "configured": bool(self.servers),
            "servers": [server.report() for server in self.servers.values()],
        }

    def shutdown(self):
        for server in self.servers.values():
            server.stop()


mcp_manager = MCPManager()


def get_mcp_tools():
    return mcp_manager.tool_schemas()


def call_mcp_tool(name, arguments):
    return mcp_manager.call(name, arguments)


__all__ = ["mcp_manager", "get_mcp_tools", "call_mcp_tool"]
