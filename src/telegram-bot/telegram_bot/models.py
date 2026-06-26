from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
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


@dataclass
class VoiceNoteEntry:
    index: int
    source_file: Path
    wav_file: Path
    transcript_file: Path
    transcript: str
    duration_seconds: float | None = None
    detected_language: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class VoiceNoteSession:
    session_id: str
    chat_id: int
    user_id: int
    session_dir: Path
    audio_dir: Path
    transcript_file: Path
    metadata_file: Path
    created_at: datetime = field(default_factory=datetime.now)
    entries: list[VoiceNoteEntry] = field(default_factory=list)
    completed_at: datetime | None = None
