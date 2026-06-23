import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_VOICE_NOTES_DIR = Path("logs") / "voice_notes"
TIMESTAMP_FORMAT = "%Y_%m_%d-%H_%M_%S"
DEFAULT_AUDIO_DEVICE = "built-in microphone"
DEFAULT_EDITOR = "code"
DEFAULT_MAX_RECORDING_SECONDS = 90


@dataclass(frozen=True)
class VoiceNoteSettings:
    mode: str = "cli"
    audio_output_folder: Path | None = None
    keep_audio: bool = False
    text_output_file: Path | None = None
    json_output_file: Path | None = None
    append_timestamp: bool = False
    language: str = "auto"
    model: str = "small"
    verbose: bool = False
    session_dir: Path | None = None
    audio_file: Path | None = None
    log_file: Path | None = None
    audio_device: str | None = DEFAULT_AUDIO_DEVICE
    editor: str = DEFAULT_EDITOR
    max_recording_seconds: int = DEFAULT_MAX_RECORDING_SECONDS

    @classmethod
    def from_file(cls, config_file: Path) -> "VoiceNoteSettings":
        payload = json.loads(config_file.read_text())
        return cls(
            mode=payload.get("mode", "cli"),
            audio_output_folder=_optional_path(payload.get("audio_output_folder")),
            keep_audio=bool(payload.get("keep_audio", False)),
            text_output_file=_optional_path(payload.get("text_output_file")),
            json_output_file=_optional_path(payload.get("json_output_file")),
            append_timestamp=bool(payload.get("append_timestamp", False)),
            language=payload.get("language", "auto"),
            model=payload.get("model", "small"),
            verbose=bool(payload.get("verbose", False)),
            session_dir=_optional_path(payload.get("session_dir")),
            audio_file=_optional_path(payload.get("audio_file")),
            log_file=_optional_path(payload.get("log_file")),
            audio_device=payload.get("audio_device", DEFAULT_AUDIO_DEVICE),
            editor=payload.get("editor", DEFAULT_EDITOR),
            max_recording_seconds=int(
                payload.get("max_recording_seconds", DEFAULT_MAX_RECORDING_SECONDS)
            ),
        )

    def with_default_storage(
        self,
        timestamp: str | None = None,
        base_dir: Path = DEFAULT_VOICE_NOTES_DIR,
    ) -> "VoiceNoteSettings":
        timestamp = timestamp or build_timestamp()
        session_dir = self.session_dir or base_dir / f"voice_note_{timestamp}"
        audio_output_folder = self.audio_output_folder or session_dir / "audio"
        text_output_file = self.text_output_file or session_dir / "transcribe.txt"
        json_output_file = self.json_output_file or session_dir / "transcribe.json"
        log_file = self.log_file or session_dir / "log.txt"

        return VoiceNoteSettings(
            mode=self.mode,
            audio_output_folder=audio_output_folder,
            keep_audio=True if self.audio_file is None else self.keep_audio,
            text_output_file=text_output_file,
            json_output_file=json_output_file,
            append_timestamp=self.append_timestamp,
            language=self.language,
            model=self.model,
            verbose=self.verbose,
            session_dir=session_dir,
            audio_file=self.audio_file,
            log_file=log_file,
            audio_device=self.audio_device,
            editor=self.editor,
            max_recording_seconds=self.max_recording_seconds,
        )

    def validate(self) -> None:
        validate_max_recording_seconds(self.max_recording_seconds)


def validate_max_recording_seconds(max_recording_seconds: int) -> None:
    if max_recording_seconds <= 0:
        raise ValueError("max recording seconds must be greater than zero")
    if max_recording_seconds > DEFAULT_MAX_RECORDING_SECONDS:
        raise ValueError(
            f"max recording seconds must be less than or equal to {DEFAULT_MAX_RECORDING_SECONDS}"
        )


def build_timestamp() -> str:
    return datetime.now().strftime(TIMESTAMP_FORMAT)


def _optional_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)
