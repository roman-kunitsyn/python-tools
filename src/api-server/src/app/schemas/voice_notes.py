from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class VoiceNoteStartRequest(BaseModel):
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
    audio_device: str = "built-in microphone"
    max_recording_seconds: int = Field(default=90, gt=0, le=300)


class VoiceNoteStartResponse(BaseModel):
    session_id: str
    session_dir: Path
    audio_file: Path
    text_output_file: Path | None
    json_output_file: Path | None
    log_file: Path | None
    state: str


class VoiceNoteStopResponse(BaseModel):
    session_id: str
    session_dir: Path
    audio_file: Path
    text: str
    text_output_file: Path | None
    json_output_file: Path | None
    state: str
