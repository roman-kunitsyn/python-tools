from __future__ import annotations

from typing import Protocol, runtime_checkable

from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import AudioResult


@runtime_checkable
class OrpheusRuntime(Protocol):
    id: str
    name: str

    def validate(self) -> None:
        ...

    def synthesize(self, request: VoiceRequest) -> AudioResult:
        ...
