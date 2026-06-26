from __future__ import annotations

import sys
from pathlib import Path


def ensure_workspace_paths() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    tool_roots = [
        repo_root / "src" / "audio-record",
        repo_root / "src" / "voice-note",
    ]

    for tool_root in tool_roots:
        tool_path = str(tool_root)
        if tool_path not in sys.path:
            sys.path.insert(0, tool_path)
