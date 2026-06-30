from __future__ import annotations

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import ProviderUnavailableError
from voice_generator.runtimes.base import OrpheusRuntime
from voice_generator.runtimes.llama_cpp import LlamaCppRuntime
from voice_generator.runtimes.official_python import OfficialPythonRuntime


class OrpheusRuntimeRegistry:
    def __init__(self, config: VoiceGeneratorConfig) -> None:
        self._config = config

    def list_runtime_ids(self) -> list[str]:
        return ["llama-cpp", "official-python"]

    def get_runtime(self, runtime_id: str | None = None) -> OrpheusRuntime:
        runtime_name = runtime_id or self._config.orpheus_runtime
        if runtime_name is None:
            raise ProviderUnavailableError("orpheus_runtime is required")
        if runtime_name == "llama-cpp":
            return LlamaCppRuntime(self._config)
        if runtime_name == "official-python":
            return OfficialPythonRuntime(self._config)
        raise ProviderUnavailableError(f"orpheus runtime '{runtime_name}' is not implemented yet")
