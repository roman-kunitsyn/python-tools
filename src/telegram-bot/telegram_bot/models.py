from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioSource:
    kind: str
    file_id: str
    filename: str
    label: str


@dataclass(frozen=True)
class TranscriptionResult:
    source: AudioSource
    local_file: Path
    transcript: str
    active_voice_note_session: bool
