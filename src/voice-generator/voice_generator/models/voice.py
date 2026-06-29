from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProviderInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    status: str = "planned"
    installed: bool = False
    supports_streaming: bool = False
    supports_ssml: bool = False


class VoiceInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    voice_id: str
    name: str
    language: str | None = None
    gender: str | None = None
    tags: list[str] = Field(default_factory=list)
    installed: bool = False
