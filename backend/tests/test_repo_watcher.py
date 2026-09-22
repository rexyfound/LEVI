import os
import time
from pathlib import Path

from services.repo_watcher import _changes_between, snapshot_repository


def test_snapshot_ignores_generated_and_dependency_directories(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv" / "Lib").mkdir(parents=True)
    (tmp_path / "dist").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('ok')", encoding="utf-8")
    (tmp_path / ".venv" / "Lib" / "installed.py").write_text("ignored", encoding="utf-8")
    (tmp_path / "dist" / "bundle.js").write_text("ignored", encoding="utf-8")

    snapshot = snapshot_repository(tmp_path)

    assert "src/main.py" in snapshot
    assert ".venv/Lib/installed.py" not in snapshot
    assert "dist/bundle.js" not in snapshot


def test_changes_are_classified_and_sorted(tmp_path: Path):
    (tmp_path / "same.txt").write_text("one", encoding="utf-8")
    (tmp_path / "removed.txt").write_text("remove", encoding="utf-8")
    previous = snapshot_repository(tmp_path)

    same_file = tmp_path / "same.txt"
    same_file.write_text("two", encoding="utf-8")
    forced_ns = time.time_ns() + 2_000_000_000
    os.utime(same_file, ns=(forced_ns, forced_ns))
    (tmp_path / "removed.txt").unlink()
    (tmp_path / "added.txt").write_text("new", encoding="utf-8")
    current = snapshot_repository(tmp_path)

    assert _changes_between(previous, current) == [
        {"path": "added.txt", "change": "added"},
        {"path": "removed.txt", "change": "deleted"},
        {"path": "same.txt", "change": "modified"},
    ]
