from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class MeetingRecordingStartRequest(BaseModel):
    meetings_dir: Path | None = None
    stamp: str = ""
    device_name: str = "Aggregate Device"
    timestamp: str | None = None
    verbose: bool = False


class MeetingRecordingStartResponse(BaseModel):
    session_id: str
    meeting_dir: Path
    audio_file: Path
    metadata_file: Path
    timestamp: str
    state: str


class MeetingRecordingStopResponse(BaseModel):
    session_id: str
    meeting_dir: Path
    audio_file: Path
    metadata_file: Path
    timestamp: str
    state: str
