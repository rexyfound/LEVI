"""Local wake-word and voice-command listener for LEVI.

The listener is intentionally optional.  LEVI still starts when the audio
packages or local models are missing; the API reports the unavailable reason
and typed/manual microphone paths continue to work.

Audio flow:
    microphone -> bounded queue -> openWakeWord -> short command buffer
    -> faster-whisper -> callback(text)

The listener runs its own daemon thread and never blocks FastAPI or Qt.  TTS
is stopped before command capture when voice activity is detected while LEVI
is speaking.
"""
from __future__ import annotations

import os
import re
import threading
import time
from pathlib import Path
from collections import deque
from typing import Callable, Optional

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency
    np = None

try:
    import sounddevice as sd
except ImportError:  # pragma: no cover - optional dependency
    sd = None

try:
    from openwakeword.model import Model as WakeWordModel
except ImportError:  # pragma: no cover - optional dependency
    WakeWordModel = None

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover - optional dependency
    WhisperModel = None

from event_bus import event_bus


DEFAULT_WAKE_PHRASE = "LEVI"
DEFAULT_WAKE_MODEL = "hey_jarvis"
DEFAULT_SAMPLE_RATE = 16_000
DEFAULT_BLOCK_SECONDS = 0.08
DEFAULT_COMMAND_TIMEOUT = 8.0
DEFAULT_SILENCE_TIMEOUT = 1.15
DEFAULT_MIN_COMMAND_SECONDS = 0.35
DEFAULT_MAX_COMMAND_SECONDS = 15.0
DEFAULT_WAKE_THRESHOLD = 0.55
DEFAULT_VOICE_THRESHOLD = 0.018
DEFAULT_INTERRUPT_BLOCKS = 3


def _env_float(name: str, default: float, minimum: float, maximum: float) -> float:
    try:
        return max(minimum, min(maximum, float(os.getenv(name, str(default)))))
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(os.getenv(name, str(default)))))
    except (TypeError, ValueError):
        return default


def _emit(event_type: str, payload: Optional[dict] = None) -> None:
    try:
        event_bus.emit_sync(event_type, payload or {})
    except Exception:
        pass


class WakeListener:
    """Threaded local listener with explicit lifecycle and bounded buffers."""

    def __init__(self, on_command: Optional[Callable[[str], None]] = None):
        self.on_command = on_command
        self.wake_phrase = os.getenv("LEVI_WAKE_PHRASE", DEFAULT_WAKE_PHRASE)
        self.wake_model_name = os.getenv("LEVI_WAKE_MODEL", DEFAULT_WAKE_MODEL)
        self.sample_rate = _env_int("LEVI_AUDIO_SAMPLE_RATE", DEFAULT_SAMPLE_RATE, 8_000, 48_000)
        self.block_seconds = _env_float("LEVI_AUDIO_BLOCK_SECONDS", DEFAULT_BLOCK_SECONDS, 0.04, 0.25)
        self.command_timeout = _env_float("LEVI_COMMAND_TIMEOUT", DEFAULT_COMMAND_TIMEOUT, 2.0, 30.0)
        self.silence_timeout = _env_float("LEVI_SILENCE_TIMEOUT", DEFAULT_SILENCE_TIMEOUT, 0.4, 3.0)
        self.min_command_seconds = _env_float("LEVI_MIN_COMMAND_SECONDS", DEFAULT_MIN_COMMAND_SECONDS, 0.2, 2.0)
        self.max_command_seconds = _env_float("LEVI_MAX_COMMAND_SECONDS", DEFAULT_MAX_COMMAND_SECONDS, 3.0, 30.0)
        self.wake_threshold = _env_float("LEVI_WAKE_THRESHOLD", DEFAULT_WAKE_THRESHOLD, 0.1, 0.99)
        self.voice_threshold = _env_float("LEVI_VOICE_THRESHOLD", DEFAULT_VOICE_THRESHOLD, 0.001, 0.2)
        self.interrupt_while_speaking = os.getenv("LEVI_INTERRUPT_WHILE_SPEAKING", "1").lower() not in {"0", "false", "no", "off"}
        self.interrupt_blocks = _env_int("LEVI_INTERRUPT_BLOCKS", DEFAULT_INTERRUPT_BLOCKS, 1, 10)
        self.device = os.getenv("LEVI_AUDIO_DEVICE", "").strip() or None
        self.whisper_model_name = os.getenv("LEVI_WHISPER_MODEL", "small.en")
        self.whisper_device = os.getenv("LEVI_WHISPER_DEVICE", "cpu")
        self.whisper_compute_type = os.getenv(
            "LEVI_WHISPER_COMPUTE_TYPE",
            "int8" if self.whisper_device == "cpu" else "float16",
        )
        self.wake_mode = "whisper" if self.wake_model_name.lower() in {"whisper", "faster-whisper", "transcribe"} else "openwakeword"
        self.passive_window_seconds = _env_float("LEVI_PASSIVE_WAKE_WINDOW", 2.2, 1.0, 4.0)
        self.passive_interval_seconds = _env_float("LEVI_PASSIVE_WAKE_INTERVAL", 0.8, 0.4, 2.0)

        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._wake_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._command_thread: Optional[threading.Thread] = None
        self._stream = None
        self._wake_model = None
        self._whisper_model = None
        self._command_buffer = deque(maxlen=max(1, int(self.max_command_seconds / self.block_seconds)))
        self._mode = "stopped"
        self._last_error = None
        self._last_wake_at = 0.0
        self._last_command_at = 0.0
        self._interrupt_count = 0
        self._processing = False
        self._passive_buffer = deque(maxlen=max(1, int(self.sample_rate * self.passive_window_seconds / max(self.block_seconds * self.sample_rate, 1))))
        self._passive_samples = 0
        self._passive_last_infer = 0.0
        self._passive_infer_active = False

    @property
    def available(self) -> bool:
        required = np is not None and sd is not None and WhisperModel is not None
        if self.wake_mode == "whisper":
            return required
        return required and WakeWordModel is not None

    def _missing_dependencies(self) -> list[str]:
        missing = []
        if np is None:
            missing.append("numpy")
        if sd is None:
            missing.append("sounddevice")
        if WhisperModel is None:
            missing.append("faster-whisper")
        if self.wake_mode != "whisper" and WakeWordModel is None:
            missing.append("openwakeword")
        return missing

    def status(self) -> dict:
        with self._lock:
            return {
                "enabled": self._mode not in {"stopped", "unavailable", "error"},
                "available": self.available,
                "running": self._thread is not None and self._thread.is_alive(),
                "mode": self._mode,
                "wake_phrase": self.wake_phrase,
                "wake_model": self.wake_model_name,
                "wake_mode": self.wake_mode,
                "whisper_model": self.whisper_model_name,
                "sample_rate": self.sample_rate,
                "buffer_seconds": round(self.max_command_seconds, 2),
                "interrupt_while_speaking": self.interrupt_while_speaking,
                "last_error": self._last_error,
                "last_wake_at": self._last_wake_at or None,
                "last_command_at": self._last_command_at or None,
                "missing_dependencies": self._missing_dependencies(),
                "wake_model_path": self._resolve_wake_model_path(),
                "model_ready": self._model_ready(),
            }

    def start(self) -> bool:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return True
            self._last_error = None
            if not self.available:
                self._mode = "unavailable"
                self._last_error = "Install optional audio packages: " + ", ".join(self._missing_dependencies())
                _emit("wake_state_changed", self.status())
                return False
            self._stop_event.clear()
            self._mode = "starting"
            self._thread = threading.Thread(target=self._run, name="LEVI-WakeListener", daemon=True)
            self._thread.start()
        _emit("wake_state_changed", self.status())
        return True

    def stop(self) -> None:
        self._stop_event.set()
        self._wake_event.set()
        stream = None
        with self._lock:
            stream = self._stream
            self._mode = "stopping"
        if stream is not None:
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.5)
        command_thread = self._command_thread
        if command_thread is not None and command_thread is not threading.current_thread():
            command_thread.join(timeout=0.3)
        with self._lock:
            self._thread = None
            self._command_thread = None
            self._stream = None
            self._mode = "stopped"
            self._processing = False
            self._command_buffer.clear()
            self._passive_buffer.clear()
            self._passive_samples = 0
        _emit("wake_state_changed", self.status())

    def restart(self) -> bool:
        self.stop()
        return self.start()

    def _resolve_wake_model_path(self) -> Optional[str]:
        """Resolve one model only; never ask openWakeWord to load every model."""
        configured = Path(self.wake_model_name).expanduser()
        if configured.is_file():
            return str(configured)
        if WakeWordModel is None:
            return None
        try:
            import openwakeword
            model_dir = Path(openwakeword.__file__).resolve().parent / "resources" / "models"
        except Exception:
            return None
        name = configured.name
        suffixes = ["", ".onnx", ".tflite", "_v0.1.onnx", "_v0.1.tflite"]
        candidates = []
        for suffix in suffixes:
            candidate = model_dir / (name if suffix == "" else f"{name}{suffix}")
            candidates.append(candidate)
        if not name.endswith((".onnx", ".tflite")):
            candidates.extend(sorted(model_dir.glob(f"{name}_v*.onnx")))
            candidates.extend(sorted(model_dir.glob(f"{name}_v*.tflite")))
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        return None

    def _load_wake_model(self):
        if self._wake_model is None:
            model_path = self._resolve_wake_model_path()
            if not model_path:
                raise FileNotFoundError(
                    f"Wake model '{self.wake_model_name}' is not installed. "
                    "Set LEVI_WAKE_MODEL=whisper to detect the exact LEVI phrase without an ONNX wake model."
                )
            self._wake_model = WakeWordModel(
                wakeword_models=[model_path],
                inference_framework="onnx",
            )
        return self._wake_model

    def _load_whisper_model(self):
        if self._whisper_model is None:
            self._whisper_model = WhisperModel(
                self.whisper_model_name,
                device=self.whisper_device,
                compute_type=self.whisper_compute_type,
            )
        return self._whisper_model

    def _run(self) -> None:
        try:
            if self.wake_mode == "whisper":
                self._load_whisper_model()
            else:
                self._load_wake_model()
            block_size = max(1, int(self.sample_rate * self.block_seconds))
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=block_size,
                device=self.device,
                callback=self._audio_callback,
            ) as stream:
                with self._lock:
                    self._stream = stream
                    self._mode = "listening"
                _emit("wake_state_changed", self.status())
                while not self._stop_event.wait(0.1):
                    self._check_command_timeout()
        except Exception as exc:
            with self._lock:
                self._mode = "error"
                self._last_error = f"{type(exc).__name__}: {exc}"
                self._stream = None
            _emit("wake_error", {"error": self._last_error})
            _emit("wake_state_changed", self.status())

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if self._stop_event.is_set() or np is None:
            return
        try:
            audio = np.asarray(indata[:, 0], dtype=np.int16).copy()
            if status:
                _emit("wake_audio_warning", {"warning": str(status)})
            self._handle_audio(audio)
        except Exception as exc:
            _emit("wake_audio_error", {"error": f"{type(exc).__name__}: {exc}"})

    def _handle_audio(self, audio) -> None:
        if audio.size == 0:
            return
        audio_float = audio.astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(np.square(audio_float))))

        # Speaking interruption is deliberately gated by a sustained voice
        # signal, preventing one noisy microphone block from stopping TTS.
        if self.interrupt_while_speaking and self._is_speaking():
            if rms >= self.voice_threshold:
                self._interrupt_count += 1
            else:
                self._interrupt_count = 0
            if self._interrupt_count >= self.interrupt_blocks:
                self._interrupt_count = 0
                self._stop_tts_for_interruption()
                self._activate_command_capture("interrupted")

        if self.wake_mode == "whisper":
            if self._mode == "listening":
                self._queue_passive_wake_audio(audio_float)
        else:
            try:
                scores = self._load_wake_model().predict(audio)
                configured_score = scores.get(self.wake_model_name)
                model_path = self._resolve_wake_model_path()
                if configured_score is None and model_path:
                    model_key = Path(model_path).stem
                    configured_score = scores.get(model_key)
                score = float(configured_score) if configured_score is not None else 0.0
            except Exception as exc:
                self._set_error(f"Wake model error: {type(exc).__name__}: {exc}")
                return

            if self._mode == "listening" and score >= self.wake_threshold:
                now = time.monotonic()
                if now - self._last_wake_at >= 1.0:
                    self._last_wake_at = now
                    self._stop_tts_for_interruption()
                    self._activate_command_capture("wake_word", score=round(score, 3))

        if self._mode == "capturing":
            self._command_buffer.append(audio_float)
            if rms < self.voice_threshold:
                if not self._wake_event.is_set():
                    self._wake_event.set()
            else:
                self._wake_event.clear()

    def _is_whisper_wake_mode(self) -> bool:
        return self.wake_mode == "whisper"

    def _model_ready(self) -> bool:
        if self._is_whisper_wake_mode():
            return self.available and WhisperModel is not None
        return self._resolve_wake_model_path() is not None

    def _queue_passive_wake_audio(self, audio_float) -> None:
        self._passive_buffer.append(audio_float.copy())
        self._passive_samples += len(audio_float)
        max_samples = int(self.sample_rate * self.passive_window_seconds)
        while self._passive_samples > max_samples and self._passive_buffer:
            self._passive_samples -= len(self._passive_buffer.popleft())
        now = time.monotonic()
        if self._passive_samples < int(self.sample_rate * 0.8):
            return
        if now - self._passive_last_infer < self.passive_interval_seconds:
            return
        if self._passive_infer_active:
            return
        self._passive_last_infer = now
        self._passive_infer_active = True
        audio = np.concatenate(list(self._passive_buffer)).astype(np.float32)
        threading.Thread(target=self._detect_whisper_wake, args=(audio,), name="LEVI-WhisperWake", daemon=True).start()

    def _detect_whisper_wake(self, audio) -> None:
        try:
            model = self._load_whisper_model()
            segments, _info = model.transcribe(
                audio,
                language=os.getenv("LEVI_WHISPER_LANGUAGE", "en"),
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            normalized = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
            wake = re.escape(self.wake_phrase.strip().lower())
            if re.search(rf"\b{wake}\b", normalized):
                now = time.monotonic()
                if now - self._last_wake_at >= 1.0 and self._mode == "listening":
                    self._last_wake_at = now
                    self._stop_tts_for_interruption()
                    self._activate_command_capture("whisper_wake")
        except Exception as exc:
            self._set_error(f"Whisper wake error: {type(exc).__name__}: {exc}")
        finally:
            self._passive_infer_active = False

    def _activate_command_capture(self, trigger: str, score: Optional[float] = None) -> None:
        with self._lock:
            if self._processing or self._mode == "capturing":
                return
            self._mode = "capturing"
            self._command_buffer.clear()
            self._wake_event.clear()
        payload = {"trigger": trigger, "wake_phrase": self.wake_phrase}
        if score is not None:
            payload["score"] = score
        _emit("wake_detected", payload)
        _emit("wake_state_changed", self.status())
        threading.Thread(target=self._capture_command, name="LEVI-CommandCapture", daemon=True).start()

    def _capture_command(self) -> None:
        started = time.monotonic()
        speech_started = False
        silence_started = None
        try:
            while not self._stop_event.is_set() and time.monotonic() - started < self.command_timeout:
                time.sleep(0.05)
                with self._lock:
                    chunks = list(self._command_buffer)
                if not chunks:
                    continue
                audio = np.concatenate(chunks)
                rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
                if rms >= self.voice_threshold:
                    speech_started = True
                    silence_started = None
                elif speech_started:
                    silence_started = silence_started or time.monotonic()
                    if time.monotonic() - silence_started >= self.silence_timeout:
                        break
                if time.monotonic() - started >= self.max_command_seconds:
                    break
            with self._lock:
                chunks = list(self._command_buffer)
            if not chunks:
                return
            audio = np.concatenate(chunks).astype(np.float32)
            if len(audio) / self.sample_rate < self.min_command_seconds:
                _emit("wake_transcription_skipped", {"reason": "command_too_short"})
                return
            _emit("wake_transcription_started", {"duration_seconds": round(len(audio) / self.sample_rate, 2)})
            model = self._load_whisper_model()
            segments, _info = model.transcribe(
                audio,
                language=os.getenv("LEVI_WHISPER_LANGUAGE", "en"),
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
            if text:
                with self._lock:
                    self._processing = True
                    self._last_command_at = time.monotonic()
                _emit("wake_transcription_completed", {"text": text})
                _emit("wake_state_changed", self.status())
                if self.on_command is not None:
                    threading.Thread(target=self._dispatch_command, args=(text,), name="LEVI-WakeCommand", daemon=True).start()
            else:
                _emit("wake_transcription_skipped", {"reason": "empty_transcription"})
        except Exception as exc:
            self._set_error(f"Transcription error: {type(exc).__name__}: {exc}")
        finally:
            with self._lock:
                self._command_buffer.clear()
                if not self._stop_event.is_set() and self._mode not in {"error", "unavailable"}:
                    self._mode = "listening"
            _emit("wake_state_changed", self.status())

    def _dispatch_command(self, text: str) -> None:
        try:
            self.on_command(text)
        except Exception as exc:
            _emit("wake_command_error", {"error": f"{type(exc).__name__}: {exc}"})
        finally:
            with self._lock:
                self._processing = False
            _emit("wake_state_changed", self.status())

    def _check_command_timeout(self) -> None:
        # The capture thread owns transcription timing. This hook intentionally
        # remains small so the audio loop can never block on model inference.
        return

    def _is_speaking(self) -> bool:
        try:
            from voice import is_speaking
            return bool(is_speaking())
        except Exception:
            return False

    def _stop_tts_for_interruption(self) -> None:
        try:
            from voice import stop_speaking
            stop_speaking()
            _emit("voice_interrupted", {"reason": "microphone_voice_activity"})
        except Exception as exc:
            _emit("wake_audio_error", {"error": f"TTS interruption failed: {exc}"})

    def _set_error(self, error: str) -> None:
        with self._lock:
            self._last_error = error
            self._mode = "error"
        _emit("wake_error", {"error": error})
        _emit("wake_state_changed", self.status())


wake_listener = WakeListener()

__all__ = ["WakeListener", "wake_listener"]
