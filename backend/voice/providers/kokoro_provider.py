"""Persistent local Kokoro TTS adapter running in an isolated Python 3.12 runtime."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import subprocess
import threading
from typing import Optional

from voice.base_provider import BaseTTSProvider


class KokoroTTSProvider(BaseTTSProvider):
    """Use a warm local worker so model load happens once, not per reply."""

    output_extension = "wav"

    def __init__(self) -> None:
        voice_root = Path(__file__).resolve().parents[1]
        runtime = Path(os.getenv("KOKORO_RUNTIME_DIR", voice_root / ".kokoro_runtime"))
        self._python = Path(os.getenv("KOKORO_PYTHON", runtime / "Scripts" / "python.exe"))
        self._worker_script = voice_root / "kokoro_worker.py"
        self._voice = os.getenv("TTS_VOICE", "af_heart")
        self._speed = os.getenv("KOKORO_SPEED", "1.0")
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.RLock()

    def is_available(self) -> bool:
        return self._python.is_file() and self._worker_script.is_file()

    async def synthesize(self, text: str, output_file_path: str, voice: Optional[str] = None) -> str:
        return await asyncio.to_thread(self._synthesize_sync, text, output_file_path, voice)

    def _start_worker(self) -> subprocess.Popen[str]:
        if self._process and self._process.poll() is None:
            return self._process
        self._process = subprocess.Popen(
            [str(self._python), str(self._worker_script)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        assert self._process.stdout is not None
        ready = self._process.stdout.readline().strip()
        try:
            payload = json.loads(ready)
        except json.JSONDecodeError as exc:
            self.cleanup()
            raise RuntimeError("Kokoro worker did not start correctly.") from exc
        if payload.get("status") != "ready":
            self.cleanup()
            raise RuntimeError(payload.get("error") or "Kokoro worker failed to initialize.")
        return self._process

    def _synthesize_sync(self, text: str, output_file_path: str, voice: Optional[str]) -> str:
        with self._lock:
            process = self._start_worker()
            if process.stdin is None or process.stdout is None:
                raise RuntimeError("Kokoro worker I/O is unavailable.")
            request = {
                "text": text,
                "output_file": output_file_path,
                "voice": voice or self._voice,
                "speed": self._speed,
            }
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            line = process.stdout.readline().strip()
            try:
                response = json.loads(line)
            except json.JSONDecodeError as exc:
                self.cleanup()
                raise RuntimeError("Kokoro worker returned an invalid response.") from exc
            if response.get("status") != "ok":
                raise RuntimeError(response.get("error") or "Kokoro synthesis failed.")
            return str(response["path"])

    def cleanup(self) -> None:
        with self._lock:
            process, self._process = self._process, None
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

