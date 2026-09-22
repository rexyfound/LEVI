import asyncio
import json
import time
import threading
from contextlib import contextmanager
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

class EventBus:
    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._loop = None
        self._local = threading.local()

    @contextmanager
    def suppress_thread_events(self):
        """Suppress synchronous events emitted by an isolated worker thread."""
        previous = getattr(self._local, "suppressed", False)
        self._local.suppressed = True
        try:
            yield
        finally:
            self._local.suppressed = previous

    def set_loop(self, loop):
        self._loop = loop

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self._active_connections.discard(websocket)

    async def emit(self, event_type: str, payload: dict = None):
        if payload is None:
            payload = {}
        
        event_data = {
            "type": event_type,
            "timestamp": time.time(),
            **payload
        }

        if not self._active_connections:
            return

        message_str = json.dumps(event_data, ensure_ascii=False)
        disconnected = set()

        for connection in list(self._active_connections):
            try:
                await connection.send_text(message_str)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self._active_connections.discard(conn)

    def emit_sync(self, event_type: str, payload: dict = None):
        """Thread-safe / synchronous wrapper to emit events from worker threads."""
        if getattr(self._local, "suppressed", False):
            return
        if payload is None:
            payload = {}
        
        event_data = {
            "type": event_type,
            "timestamp": time.time(),
            **payload
        }

        if not self._active_connections:
            return

        try:
            loop = self._loop or asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(self.emit(event_type, payload), loop)
            else:
                loop.run_until_complete(self.emit(event_type, payload))
        except Exception as e:
            print(f"[EVENT_BUS_ERROR] Failed to emit sync event: {e}")

event_bus = EventBus()
