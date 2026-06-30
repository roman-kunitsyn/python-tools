from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class AudioDecoder(Protocol):
    id: str
    name: str

    def decode(self, payload: str, output_path: Path, *, format: str) -> Path:
        ...
