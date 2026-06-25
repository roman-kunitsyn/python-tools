from __future__ import annotations

import sys
from pathlib import Path


def ensure_voice_note_path() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    voice_note_path = repo_root / "src" / "voice-note"
    path_text = str(voice_note_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)
