from __future__ import annotations

from typing import Protocol, runtime_checkable

from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import VoiceResponse
from voice_generator.models.voice import VoiceInfo


@runtime_checkable
class VoiceProvider(Protocol):
    id: str
    name: str

    def list_voices(self) -> list[VoiceInfo]:
        ...

    def supports_streaming(self) -> bool:
        ...

    def supports_ssml(self) -> bool:
        ...

    def generate(self, request: VoiceRequest) -> VoiceResponse:
        ...

    def validate(self) -> None:
        ...
