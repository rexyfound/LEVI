import os
import time
import ctypes
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger("LEVI.AudioPlayer")


class WindowsMCIAudioPlayer:
    """
    Hardware audio playback engine for Windows using Media Control Interface (winmm.dll).
    Supports MP3, WAV, and standard audio formats without third-party binary dependencies.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._is_playing = False
        self._current_alias: Optional[str] = None
        self._current_file: Optional[str] = None
        self._stop_event = threading.Event()
        self._play_thread: Optional[threading.Thread] = None

        try:
            self._winmm = ctypes.windll.winmm
        except Exception as e:
            logger.warning(f"winmm.dll could not be loaded: {e}")
            self._winmm = None

    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing

    def play(
        self,
        audio_file_path: str,
        on_started: Optional[Callable[[], None]] = None,
        on_finished: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> bool:
        """
        Start non-blocking playback of the given audio file on the default Windows audio device.
        If another track is currently playing, it will be safely stopped before starting the new one.
        """
        self.stop()

        if not os.path.exists(audio_file_path):
            if on_error:
                on_error("Audio file does not exist.")
            return False

        if self._winmm is None:
            if on_error:
                on_error("Windows Multimedia System (winmm.dll) is unavailable.")
            return False

        alias = f"levi_voice_{int(time.time() * 1000)}"
        self._stop_event.clear()

        def _worker():
            with self._lock:
                self._is_playing = True
                self._current_alias = alias
                self._current_file = audio_file_path

            try:
                # Open audio file via MCI
                self._send_mci(f"close {alias}")
                open_cmd = f'open "{audio_file_path}" type mpegvideo alias {alias}'
                res = self._send_mci(open_cmd)
                if res != 0:
                    # Try generic open without type if mpegvideo fails
                    res = self._send_mci(f'open "{audio_file_path}" alias {alias}')
                    if res != 0:
                        raise RuntimeError(f"MCI open failed with code {res}")

                # Start playback
                play_res = self._send_mci(f"play {alias}")
                if play_res != 0:
                    raise RuntimeError(f"MCI play failed with code {play_res}")

                if on_started:
                    try:
                        on_started()
                    except Exception as ex:
                        logger.error(f"Error in on_started callback: {ex}")

                # Poll playback mode until completed or stopped
                buf = ctypes.create_unicode_buffer(128)
                while not self._stop_event.is_set():
                    time.sleep(0.08)
                    self._winmm.mciSendStringW(f"status {alias} mode", buf, 128, 0)
                    mode = buf.value.lower()
                    if mode in ["stopped", ""]:
                        break

            except Exception as e:
                logger.error(f"Playback error for {audio_file_path}: {e}")
                if on_error and not self._stop_event.is_set():
                    try:
                        on_error(str(e))
                    except Exception:
                        pass
            finally:
                # Cleanup MCI device and file
                self._send_mci(f"stop {alias}")
                self._send_mci(f"close {alias}")

                with self._lock:
                    self._is_playing = False
                    self._current_alias = None
                    self._current_file = None

                # Clean up temporary audio file safely
                self._safe_delete_file(audio_file_path)

                if on_finished and not self._stop_event.is_set():
                    try:
                        on_finished()
                    except Exception as ex:
                        logger.error(f"Error in on_finished callback: {ex}")

        self._play_thread = threading.Thread(target=_worker, name="LEVI_MCI_AudioPlayer", daemon=True)
        self._play_thread.start()
        return True

    def stop(self) -> None:
        """
        Immediately halts active playback, releases MCI handles, and cleans up resources.
        """
        self._stop_event.set()

        with self._lock:
            if self._current_alias and self._winmm:
                self._send_mci(f"stop {self._current_alias}")
                self._send_mci(f"close {self._current_alias}")
                self._current_alias = None

            temp_file = self._current_file
            self._current_file = None
            self._is_playing = False

        if temp_file:
            self._safe_delete_file(temp_file)

        if self._play_thread and self._play_thread.is_alive() and threading.current_thread() != self._play_thread:
            self._play_thread.join(timeout=0.3)

    def _send_mci(self, cmd: str) -> int:
        if not self._winmm:
            return -1
        return self._winmm.mciSendStringW(cmd, None, 0, 0)

    def _safe_delete_file(self, file_path: str) -> None:
        if not file_path:
            return
        # Small delay to ensure file handle release on Windows
        for _ in range(3):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                break
            except Exception:
                time.sleep(0.05)
