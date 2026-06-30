from __future__ import annotations

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import ValidationError
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import AudioResult
from voice_generator.services.registry import ProviderRegistry


def generate_voice(
    request: VoiceRequest,
    config: VoiceGeneratorConfig,
) -> AudioResult:
    provider_id = request.provider or config.default_provider
    if provider_id is None:
        raise ValidationError("provider is required")
    provider = ProviderRegistry(config).get_provider(provider_id)
    if hasattr(provider, "synthesize"):
        return provider.synthesize(request)
    return provider.generate(request)
