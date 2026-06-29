from __future__ import annotations

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import FeatureNotImplementedError
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import VoiceResponse


def generate_voice(
    request: VoiceRequest,
    config: VoiceGeneratorConfig,
) -> VoiceResponse:
    raise FeatureNotImplementedError(
        "voice generation backends are not implemented yet"
    )
