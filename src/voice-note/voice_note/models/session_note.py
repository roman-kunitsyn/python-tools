from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class SessionNote:
    note_id: str
    text: str
    created_at: datetime
    audio_file: Path | None = None
