from dataclasses import dataclass
from pathlib import Path


@dataclass
class RecordingResult:
    meeting_dir: Path
    audio_file: Path
    metadata_file: Path
    timestamp: str
