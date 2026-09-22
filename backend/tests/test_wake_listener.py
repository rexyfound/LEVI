import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import voice.wake_listener as wake_module
from voice.wake_listener import WakeListener


def test_wake_status_is_safe_without_optional_audio_stack(monkeypatch):
    monkeypatch.setattr(wake_module, "sd", None)
    monkeypatch.setattr(wake_module, "WakeWordModel", None)
    monkeypatch.setattr(wake_module, "WhisperModel", None)

    listener = WakeListener()
    assert listener.start() is False
    status = listener.status()

    assert status["running"] is False
    assert status["mode"] == "unavailable"
    assert "sounddevice" in status["missing_dependencies"]
    assert "openwakeword" in status["missing_dependencies"]
    assert "faster-whisper" in status["missing_dependencies"]


def test_wake_listener_stop_is_idempotent():
    listener = WakeListener()
    listener.stop()
    listener.stop()
    assert listener.status()["mode"] == "stopped"
