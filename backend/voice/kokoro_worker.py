"""Line-delimited JSON worker for the isolated Kokoro runtime."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from contextlib import redirect_stdout


def emit(payload: dict) -> None:
    print(json.dumps(payload), flush=True)


def main() -> int:
    try:
        import soundfile as sf
        import torch
        from kokoro import KPipeline

        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Kokoro selects the compatible inference device internally. Passing
        # `device` only when the installed release supports it keeps the worker
        # compatible across supported Kokoro releases.
        # stdout is reserved for this worker's JSON protocol. Kokoro can emit
        # informational startup messages there, so redirect them to stderr.
        kwargs = {
            "lang_code": os.getenv("KOKORO_LANG", "a"),
            "repo_id": os.getenv("KOKORO_REPO_ID", "hexgrad/Kokoro-82M"),
        }
        with redirect_stdout(sys.stderr):
            try:
                pipeline = KPipeline(**kwargs, device=device)
            except TypeError:
                pipeline = KPipeline(**kwargs)
        emit({"status": "ready", "device": device})
    except Exception as exc:
        emit({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
        return 1

    for raw_line in sys.stdin:
        try:
            request = json.loads(raw_line)
            output_file = Path(request["output_file"])
            output_file.parent.mkdir(parents=True, exist_ok=True)
            chunks = list(pipeline(
                request["text"],
                voice=request.get("voice") or "af_heart",
                speed=float(request.get("speed") or 1.0),
            ))
            if not chunks:
                raise RuntimeError("Kokoro generated no audio.")
            # The model can segment longer speech. Concatenating the generated
            # waveforms keeps playback as one natural utterance.
            import numpy as np
            audio = np.concatenate([chunk[2] for chunk in chunks])
            sf.write(str(output_file), audio, 24000)
            emit({"status": "ok", "path": str(output_file)})
        except Exception as exc:
            emit({"status": "error", "error": f"{type(exc).__name__}: {exc}"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
