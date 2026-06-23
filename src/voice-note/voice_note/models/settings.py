import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_VOICE_NOTES_DIR = Path("logs") / "voice_notes"
TIMESTAMP_FORMAT = "%Y_%m_%d-%H_%M_%S"


@dataclass(frozen=True)
class VoiceNoteSettings:
    mode: str = "cli"
    audio_output_folder: Path | None = None
    keep_audio: bool = False
    text_output_file: Path | None = None
    append_timestamp: bool = False
    language: str = "auto"
    model: str = "small"
    verbose: bool = False
    session_dir: Path | None = None
    audio_file: Path | None = None

    @classmethod
    def from_file(cls, config_file: Path) -> "VoiceNoteSettings":
        payload = json.loads(config_file.read_text())
        return cls(
            mode=payload.get("mode", "cli"),
            audio_output_folder=_optional_path(payload.get("audio_output_folder")),
            keep_audio=bool(payload.get("keep_audio", False)),
            text_output_file=_optional_path(payload.get("text_output_file")),
            append_timestamp=bool(payload.get("append_timestamp", False)),
            language=payload.get("language", "auto"),
            model=payload.get("model", "small"),
            verbose=bool(payload.get("verbose", False)),
            session_dir=_optional_path(payload.get("session_dir")),
            audio_file=_optional_path(payload.get("audio_file")),
        )

    def with_default_storage(
        self,
        timestamp: str | None = None,
        base_dir: Path = DEFAULT_VOICE_NOTES_DIR,
    ) -> "VoiceNoteSettings":
        timestamp = timestamp or build_timestamp()
        session_dir = self.session_dir or base_dir / f"voice_note_{timestamp}"
        audio_output_folder = self.audio_output_folder or session_dir / "audio"
        audio_file = self.audio_file or audio_output_folder / f"audio_{timestamp}.wav"
        text_output_file = self.text_output_file or session_dir / "transcribe.txt"

        return VoiceNoteSettings(
            mode=self.mode,
            audio_output_folder=audio_output_folder,
            keep_audio=True if self.audio_file is None else self.keep_audio,
            text_output_file=text_output_file,
            append_timestamp=self.append_timestamp,
            language=self.language,
            model=self.model,
            verbose=self.verbose,
            session_dir=session_dir,
            audio_file=audio_file,
        )


def build_timestamp() -> str:
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def _optional_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)
