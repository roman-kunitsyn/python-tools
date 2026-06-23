import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VoiceNoteSettings:
    mode: str = "cli"
    audio_output_folder: Path | None = None
    keep_audio: bool = False
    text_output_file: Path | None = None
    append_timestamp: bool = False
    language: str = "auto"
    model: str = "base"
    verbose: bool = False

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
            model=payload.get("model", "base"),
            verbose=bool(payload.get("verbose", False)),
        )


def _optional_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)
