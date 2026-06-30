from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AudioResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    voice: str | None = None
    duration: float | None = None
    sample_rate: int | None = None
    output_file: Path | None = None
    generation_time: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


VoiceResponse = AudioResult
