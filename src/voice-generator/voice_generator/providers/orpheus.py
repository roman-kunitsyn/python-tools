from __future__ import annotations

import json
from typing import Any

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import MissingModelError, ProviderUnavailableError, ValidationError
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import AudioResult
from voice_generator.models.voice import VoiceInfo
from voice_generator.runtimes.registry import OrpheusRuntimeRegistry


class OrpheusProvider:
    id = "orpheus"
    name = "Orpheus"

    def __init__(self, config: VoiceGeneratorConfig) -> None:
        self._config = config
        self._runtime_registry = OrpheusRuntimeRegistry(config)

    def list_voices(self) -> list[VoiceInfo]:
        catalog = self._load_voice_catalog()
        if catalog is not None:
            return catalog
        default_voice = self._config.default_voice
        if default_voice is None:
            return []
        return [
            VoiceInfo(
                provider=self.id,
                voice_id=default_voice,
                name=default_voice,
                language=None,
                gender=None,
                tags=["orpheus"],
                installed=False,
            )
        ]

    def supports_streaming(self) -> bool:
        return False

    def supports_ssml(self) -> bool:
        return False

    def validate(self) -> None:
        if self._config.orpheus_runtime is None:
            raise ProviderUnavailableError("orpheus_runtime is required")
        runtime = self._runtime_registry.get_runtime(self._config.orpheus_runtime)
        runtime.validate()
        if self._config.orpheus_model is None:
            raise MissingModelError("orpheus_model is required")
        if not self._config.orpheus_model.exists():
            raise MissingModelError(f"orpheus model not found: {self._config.orpheus_model}")
        if self._config.orpheus_voice_catalog is not None and not self._config.orpheus_voice_catalog.exists():
            raise ValidationError(
                f"orpheus voice catalog not found: {self._config.orpheus_voice_catalog}"
            )

    def synthesize(self, request: VoiceRequest) -> AudioResult:
        runtime = self._runtime_registry.get_runtime(self._config.orpheus_runtime)
        return runtime.synthesize(request)

    def generate(self, request: VoiceRequest) -> AudioResult:
        return self.synthesize(request)

    def _load_voice_catalog(self) -> list[VoiceInfo] | None:
        if self._config.orpheus_voice_catalog is None:
            return None
        payload = self._config.orpheus_voice_catalog.read_text(encoding="utf-8").strip()
        if not payload:
            return []
        if payload.startswith("["):
            data = json.loads(payload)
            return [_voice_from_json(item) for item in data]
        voices: list[VoiceInfo] = []
        for line in payload.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            voices.append(
                VoiceInfo(
                    provider=self.id,
                    voice_id=line,
                    name=line,
                    language=None,
                    gender=None,
                    tags=["orpheus"],
                    installed=True,
                )
            )
        return voices


def _voice_from_json(payload: object) -> VoiceInfo:
    if not isinstance(payload, dict):
        name = str(payload)
        return VoiceInfo(
            provider="orpheus",
            voice_id=name,
            name=name,
            language=None,
            gender=None,
            tags=["orpheus"],
            installed=True,
        )
    voice_id = str(payload.get("voice_id") or payload.get("id") or payload.get("name") or "")
    if not voice_id:
        raise ValidationError("orpheus voice catalog entry is missing a voice id")
    tags = payload.get("tags")
    if isinstance(tags, list):
        normalized_tags = [str(tag) for tag in tags]
    else:
        normalized_tags = ["orpheus"]
    return VoiceInfo(
        provider="orpheus",
        voice_id=voice_id,
        name=str(payload.get("name") or voice_id),
        language=(str(payload["language"]) if payload.get("language") is not None else None),
        gender=(str(payload["gender"]) if payload.get("gender") is not None else None),
        tags=normalized_tags,
        installed=bool(payload.get("installed", True)),
    )
