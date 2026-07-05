from dataclasses import dataclass
import re
from pathlib import Path


SESSION_TIMESTAMP_PATTERN = r"\d{4}_\d{2}_\d{2}-\d{2}_\d{2}_\d{2}"
DEFAULT_SESSION_TITLE = "voice_note"


@dataclass(frozen=True)
class VoiceNoteSession:
    title: str
    slug: str
    timestamp: str
    session_dir: Path

    @property
    def folder_name(self) -> str:
        return f"{self.slug}_{self.timestamp}"

    @property
    def audio_dir(self) -> Path:
        return self.session_dir / "audio"

    @property
    def transcript_file(self) -> Path:
        return self.session_dir / "transcribe.txt"

    @property
    def transcript_json_file(self) -> Path:
        return self.notes_file

    @property
    def notes_file(self) -> Path:
        return self.session_dir / "notes.json"

    @property
    def assistant_file(self) -> Path:
        return self.session_dir / "assistant.json"

    @property
    def assistant_transcript_file(self) -> Path:
        return self.session_dir / "assistant.txt"

    @property
    def log_file(self) -> Path:
        return self.session_dir / "log.txt"

    @property
    def metadata_file(self) -> Path:
        return self.session_dir / "session.json"


def slugify_session_title(title: str | None) -> str:
    normalized = (title or "").strip().lower()
    if not normalized:
        return DEFAULT_SESSION_TITLE

    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or DEFAULT_SESSION_TITLE


def build_session_folder_name(title: str | None, timestamp: str) -> str:
    return f"{slugify_session_title(title)}_{timestamp}"


def parse_session_folder_name(folder_name: str) -> tuple[str, str] | None:
    match = re.match(
        rf"^(?P<slug>.+)_(?P<timestamp>{SESSION_TIMESTAMP_PATTERN})$",
        folder_name,
    )
    if match is None:
        return None

    return match.group("slug"), match.group("timestamp")
