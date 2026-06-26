from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class TranscriptionRequest(BaseModel):
    audio_file: Path
    output_file: Path | None = None
    output_format: str = Field(default="txt")
    model_file: Path | None = None
    language: str = "auto"
    verbose: bool = False


class TranscriptionResponse(BaseModel):
    audio_file: Path
    output_file: Path
    output_format: str
    state: str
