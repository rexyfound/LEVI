# LEVI Local Wake Voice

LEVI’s optional local voice input uses a two-stage pipeline:

1. `openWakeWord` watches short microphone blocks for the configured wake model.
2. After activation, `faster-whisper` transcribes a bounded command buffer and sends the text to the existing assistant service.

The listener is daemon-threaded and does not block FastAPI or the PyQt event loop. If the optional packages or local models are unavailable, LEVI still starts and typed/manual input remains available.

## Windows setup

From the LEVI project directory:

```bat
python -m pip install -r requirements.txt
```

The first use of the selected Whisper model may download model files. For a fully offline deployment, download the model once while connected and point `LEVI_WHISPER_MODEL` to the local model directory. openWakeWord model assets must also be downloaded once; LEVI now loads only the configured model instead of trying to load every package model.

From `D:\\Projects\\LEVI`, run:

```bat
.venv\\Scripts\\python.exe -c "from openwakeword.utils import download_models; download_models()"
```

Then keep this configuration:

```dotenv
LEVI_WAKE_MODEL=hey_jarvis
```

Set these values in the local `.env` file:

```dotenv
LEVI_WAKE_PHRASE=LEVI
LEVI_WAKE_MODEL=hey_jarvis
LEVI_WAKE_THRESHOLD=0.55
LEVI_WHISPER_MODEL=small.en
LEVI_WHISPER_DEVICE=cpu
LEVI_WHISPER_COMPUTE_TYPE=int8
LEVI_WHISPER_LANGUAGE=en
```

`openWakeWord` requires a compatible wake model. The default package models are not necessarily trained for the literal word `LEVI`. For reliable activation on the name LEVI, supply a custom model path through `LEVI_WAKE_MODEL`, for example:

```dotenv
LEVI_WAKE_MODEL=D:\Projects\LEVI\models\levi.onnx
```

## Buffering and interruption

The microphone is opened at 16 kHz mono with short blocks controlled by `LEVI_AUDIO_BLOCK_SECONDS`. Captured command audio is kept in a bounded deque whose maximum duration is `LEVI_MAX_COMMAND_SECONDS`; it cannot grow without limit. The command closes when speech has stopped for `LEVI_SILENCE_TIMEOUT` seconds or when `LEVI_COMMAND_TIMEOUT` is reached.

When LEVI is speaking, the listener calculates the RMS level of consecutive microphone blocks. If the level exceeds `LEVI_VOICE_THRESHOLD` for `LEVI_INTERRUPT_BLOCKS` blocks, the TTS manager is stopped immediately, the current playback file is released, and the listener changes to command-capture mode. This avoids interrupting speech on a single noise spike while still allowing the user to cut LEVI off naturally.

Tune these values for the microphone and room:

```dotenv
LEVI_VOICE_THRESHOLD=0.018
LEVI_INTERRUPT_BLOCKS=3
LEVI_SILENCE_TIMEOUT=1.15
LEVI_MAX_COMMAND_SECONDS=15
```

The microphone stream is closed on FastAPI shutdown and in the native PyQt window’s `closeEvent`. The API exposes operational controls at:

```text
GET  /wake/status
POST /wake/start
POST /wake/stop
POST /wake/restart
```

If both the PyQt application and the Electron/FastAPI desktop shell are running at the same time, enable the wake listener in only one process to avoid two processes competing for the microphone. The normal LEVI desktop flow should run one shell at a time.
