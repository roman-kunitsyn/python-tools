from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class VoiceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    input_path: Path | None = None
    voice: str | None = None
    language: str | None = None
    provider: str | None = None
    emotion: str | None = None
    speed: float | None = None
    pitch: float | None = None
    temperature: float | None = None
    seed: int | None = None
    stream: bool = False
    output_path: Path | None = None
    format: str = Field(default="wav")
    sample_rate: int | None = None
    normalize_audio: bool = False
    metadata: dict[str, str] = Field(default_factory=dict)
