from __future__ import annotations

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import ValidationError
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import VoiceResponse
from voice_generator.services.registry import ProviderRegistry


def generate_voice(
    request: VoiceRequest,
    config: VoiceGeneratorConfig,
) -> VoiceResponse:
    provider_id = request.provider or config.default_provider
    if provider_id is None:
        raise ValidationError("provider is required")
    provider = ProviderRegistry(config).get_provider(provider_id)
    return provider.generate(request)
