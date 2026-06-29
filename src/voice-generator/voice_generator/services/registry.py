from __future__ import annotations

from voice_generator.errors import ProviderUnavailableError
from voice_generator.models.voice import ProviderInfo, VoiceInfo


class ProviderRegistry:
    _providers: tuple[ProviderInfo, ...] = (
        ProviderInfo(id="macos", name="macOS Say"),
        ProviderInfo(id="kokoro", name="Kokoro"),
        ProviderInfo(id="piper", name="Piper"),
        ProviderInfo(id="orpheus", name="Orpheus"),
        ProviderInfo(id="elevenlabs", name="ElevenLabs", supports_streaming=True),
    )

    def list_providers(self) -> list[ProviderInfo]:
        return list(self._providers)

    def get_provider(self, provider_id: str):
        raise ProviderUnavailableError(
            f"provider backend '{provider_id}' is not implemented yet"
        )

    def list_voices(self, provider_id: str | None = None) -> list[VoiceInfo]:
        if provider_id is None:
            return []
        if not any(provider.id == provider_id for provider in self._providers):
            raise ProviderUnavailableError(f"unknown provider '{provider_id}'")
        return []
