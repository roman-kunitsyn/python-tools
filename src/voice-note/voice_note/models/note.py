from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class VoiceNote:
    text: str
    created_at: datetime
    audio_file: Path
