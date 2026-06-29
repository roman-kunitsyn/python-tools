from __future__ import annotations

import shutil
from pathlib import Path

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import ProviderUnavailableError, VoiceGeneratorError
from voice_generator.models.voice import ProviderInfo, VoiceInfo
from voice_generator.providers.macos_say import MacOSSayProvider
from voice_generator.providers.orpheus import OrpheusProvider


class ProviderRegistry:
    def __init__(self, config: VoiceGeneratorConfig | None = None) -> None:
        self._config = config or VoiceGeneratorConfig()

    def list_providers(self) -> list[ProviderInfo]:
        return [
            ProviderInfo(
                id="macos",
                name="macOS Say",
                status="ready" if shutil.which("say") is not None else "missing-say",
            ),
            ProviderInfo(
                id="orpheus",
                name="Orpheus",
                status=self._orpheus_status(),
            ),
            ProviderInfo(id="kokoro", name="Kokoro", status="planned"),
            ProviderInfo(id="piper", name="Piper", status="planned"),
            ProviderInfo(
                id="elevenlabs",
                name="ElevenLabs",
                status="planned",
                supports_streaming=True,
            ),
        ]

    def get_provider(self, provider_id: str):
        if provider_id == "macos":
            return MacOSSayProvider(self._config)
        if provider_id == "orpheus":
            return OrpheusProvider(self._config)
        raise ProviderUnavailableError(f"provider backend '{provider_id}' is not implemented yet")

    def list_voices(self, provider_id: str | None = None) -> list[VoiceInfo]:
        if provider_id is None:
            voices: list[VoiceInfo] = []
            for candidate in ("macos", "orpheus"):
                try:
                    voices.extend(self.get_provider(candidate).list_voices())
                except VoiceGeneratorError:
                    continue
            return voices
        return self.get_provider(provider_id).list_voices()

    def _orpheus_status(self) -> str:
        if self._config.orpheus_command is None:
            return "needs-config"
        if self._config.orpheus_model_path is None:
            return "missing-model"
        if not self._config.orpheus_model_path.exists():
            return "missing-model"
        command = self._config.orpheus_command
        if shutil.which(command) is None and not Path(command).exists():
            return "missing-runtime"
        return "ready"
