import os
import uuid
import time
import asyncio
import logging
import threading
from typing import Optional, Dict, Any
try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# Ensure .env is loaded from workspace root
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)
else:
    load_dotenv()

from event_bus import event_bus
from voice.states import VoiceState
from voice.base_provider import BaseTTSProvider
from voice.providers.edge_tts_provider import EdgeTTSProvider
from voice.providers.openai_tts_provider import OpenAITTSProvider
from voice.providers.elevenlabs_provider import ElevenLabsTTSProvider
from voice.providers.kokoro_provider import KokoroTTSProvider
from voice.audio_player import WindowsMCIAudioPlayer
from voice.text_shortener import prepare_spoken_text

logger = logging.getLogger("LEVI.VoiceManager")


class VoiceManager:
    """
    Central, thread-safe, non-blocking Voice Manager for LEVI.
    Handles synthesis, audio playback, queue/cancellation concurrency policy, and event bus emissions.
    """

    def __init__(
        self,
        provider: Optional[BaseTTSProvider] = None,
        audio_player: Optional[Any] = None,
        cache_dir: Optional[str] = None,
    ):
        self._lock = threading.RLock()
        self._state: VoiceState = VoiceState.IDLE
        self._current_request_id: Optional[str] = None
        self._active_task_id: Optional[str] = None
        self._is_enabled = os.getenv("TTS_ENABLED", "true").lower() in ["1", "true", "yes"]

        # Setup Cache Directory
        self._cache_dir = cache_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".voice_cache")
        os.makedirs(self._cache_dir, exist_ok=True)

        # Provider Selection
        self._provider = provider or self._init_default_provider()
        self._player = audio_player or WindowsMCIAudioPlayer()

        # Dedicated background async loop thread for synthesis
        self._async_loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_async_loop, name="LEVI_Voice_AsyncLoop", daemon=True)
        self._loop_thread.start()

    def _init_default_provider(self) -> BaseTTSProvider:
        provider_name = os.getenv("TTS_PROVIDER", "edge").lower()

        if provider_name == "elevenlabs":
            p = ElevenLabsTTSProvider()
            if p.is_available():
                return p
            logger.warning("ElevenLabs TTS provider requested but ELEVENLABS_API_KEY is missing. Falling back to Edge TTS.")

        if provider_name == "openai":
            p = OpenAITTSProvider()
            if p.is_available():
                return p
            logger.warning("OpenAI TTS provider requested but not available. Falling back to Edge TTS.")

        if provider_name == "kokoro":
            p = KokoroTTSProvider()
            if p.is_available():
                return p
            logger.warning("Kokoro TTS provider requested but its isolated runtime is not installed. Falling back to Edge TTS.")

        return EdgeTTSProvider()

    def _run_async_loop(self):
        asyncio.set_event_loop(self._async_loop)
        self._async_loop.run_forever()

    def get_state(self) -> VoiceState:
        with self._lock:
            return self._state

    def is_speaking(self) -> bool:
        with self._lock:
            return self._state in [VoiceState.PREPARING, VoiceState.SPEAKING]

    def _set_state(self, new_state: VoiceState, request_id: Optional[str] = None):
        with self._lock:
            self._state = new_state
            req_id = request_id or self._current_request_id

        # Emit versioned state change event
        try:
            event_bus.emit_sync(
                "voice_state_changed",
                {
                    "state": new_state.value,
                    "request_id": req_id,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit voice_state_changed event: {e}")

    def _emit_error(self, error_message: str, request_id: Optional[str] = None):
        with self._lock:
            self._state = VoiceState.ERROR
            req_id = request_id or self._current_request_id

        try:
            event_bus.emit_sync(
                "voice_error",
                {
                    "error": error_message,
                    "request_id": req_id,
                },
            )
        except Exception as e:
            logger.error(f"Failed to emit voice_error event: {e}")

        # Transition back to IDLE after error
        self._set_state(VoiceState.IDLE, request_id=req_id)

    def speak(
        self,
        text: str,
        *,
        spoken_text: Optional[str] = None,
        request_id: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> Optional[str]:
        """
        Non-blocking TTS dispatch.
        Cancels any ongoing speech and prepares/plays the new utterance in the background.
        """
        if not self._is_enabled:
            return None

        if not text or not text.strip():
            return None

        clean_spoken_text = spoken_text or prepare_spoken_text(text)
        if not clean_spoken_text:
            return None

        req_id = request_id or str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        # Concurrency Policy: Stop current speech and claim latest task ID
        self.stop_speaking()

        with self._lock:
            self._current_request_id = req_id
            self._active_task_id = task_id

        # Publish PREPARING before queueing synthesis so the UI reacts in the
        # same turn as the text response, without pretending audio is playing.
        self._set_state(VoiceState.PREPARING, request_id=req_id)

        # Dispatch async synthesis & playback
        asyncio.run_coroutine_threadsafe(
            self._process_utterance(clean_spoken_text, req_id, task_id, voice),
            self._async_loop,
        )

        return req_id

    async def _process_utterance(self, text: str, req_id: str, task_id: str, voice: Optional[str]):
        # Verify task is still the latest requested
        with self._lock:
            if self._active_task_id != task_id:
                return

        extension = getattr(self._provider, "output_extension", "mp3")
        output_file = os.path.join(self._cache_dir, f"speech_{task_id}.{extension}")

        try:
            # 1. Synthesize audio
            await self._provider.synthesize(text, output_file, voice=voice)

            # Check again if cancelled during synthesis
            with self._lock:
                if self._active_task_id != task_id:
                    self._safe_remove(output_file)
                    return

            # 2. Play audio via audio player
            def on_started():
                with self._lock:
                    if self._active_task_id == task_id:
                        self._set_state(VoiceState.SPEAKING, request_id=req_id)

            def on_finished():
                with self._lock:
                    if self._active_task_id == task_id:
                        self._set_state(VoiceState.IDLE, request_id=req_id)

            def on_error(err: str):
                with self._lock:
                    if self._active_task_id == task_id:
                        self._emit_error(f"Voice playback error: {err}", request_id=req_id)

            played = self._player.play(
                output_file,
                on_started=on_started,
                on_finished=on_finished,
                on_error=on_error,
            )

            if not played:
                self._emit_error("Audio playback initialization failed.", request_id=req_id)

        except asyncio.CancelledError:
            self._safe_remove(output_file)
            self._set_state(VoiceState.IDLE, request_id=req_id)
        except Exception as e:
            logger.error(f"TTS synthesis/dispatch failed for request {req_id}: {e}")
            self._safe_remove(output_file)
            self._emit_error("Speech synthesis failed.", request_id=req_id)

    def stop_speaking(self) -> None:
        """
        Immediately stops ongoing audio playback and cancels pending synthesis. Safe and idempotent.
        """
        with self._lock:
            prev_req_id = self._current_request_id
            self._active_task_id = None
            if self._state in [VoiceState.PREPARING, VoiceState.SPEAKING]:
                self._state = VoiceState.STOPPING

        self._player.stop()

        with self._lock:
            self._state = VoiceState.IDLE

        try:
            event_bus.emit_sync(
                "voice_state_changed",
                {
                    "state": VoiceState.IDLE.value,
                    "request_id": prev_req_id,
                },
            )
        except Exception:
            pass

    def _safe_remove(self, path: str):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    def cleanup(self):
        self.stop_speaking()
        try:
            self._provider.cleanup()
        except Exception:
            pass
        if self._async_loop and self._async_loop.is_running():
            async def cancel_pending_tasks():
                current_task = asyncio.current_task()
                pending = [
                    task for task in asyncio.all_tasks()
                    if task is not current_task and not task.done()
                ]
                for task in pending:
                    task.cancel()
                if pending:
                    await asyncio.gather(*pending, return_exceptions=True)

            try:
                future = asyncio.run_coroutine_threadsafe(cancel_pending_tasks(), self._async_loop)
                future.result(timeout=0.5)
            except Exception:
                pass
            self._async_loop.call_soon_threadsafe(self._async_loop.stop)
            if self._loop_thread.is_alive():
                self._loop_thread.join(timeout=0.5)
