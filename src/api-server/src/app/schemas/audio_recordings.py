from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class AudioRecordingStartRequest(BaseModel):
    output_file: Path | None = None
    device: str | None = None
    duration: float | None = Field(default=None, gt=0)
    sample_rate: int = Field(default=16000, gt=0)
    channels: int = Field(default=1, ge=1, le=2)
    output_format: str = Field(default="wav")
    verbose: bool = False


class AudioRecordingStartResponse(BaseModel):
    session_id: str | None = None
    output_file: Path
    state: str


class AudioRecordingStopResponse(BaseModel):
    session_id: str
    output_file: Path
    state: str
