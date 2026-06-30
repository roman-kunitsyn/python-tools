from __future__ import annotations

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.decoders.snac import SnacDecoder
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import AudioResult
from voice_generator.runtimes.llama_cpp import LlamaCppRuntime


class OfficialPythonRuntime(LlamaCppRuntime):
    id = "official-python"
    name = "official Python runtime"

    def __init__(self, config: VoiceGeneratorConfig, decoder: SnacDecoder | None = None) -> None:
        super().__init__(config, decoder=decoder)

    def synthesize(self, request: VoiceRequest) -> AudioResult:
        return super().synthesize(request)
