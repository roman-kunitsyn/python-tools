from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.services.registry import ProviderRegistry


class ProviderRegistryTests(TestCase):
    def test_list_providers_returns_planned_catalog(self) -> None:
        registry = ProviderRegistry()

        provider_ids = [provider.id for provider in registry.list_providers()]

        self.assertEqual(
            provider_ids,
            ["macos", "orpheus", "kokoro", "piper", "elevenlabs"],
        )

    def test_orpheus_status_reflects_configured_runtime(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "orpheus.gguf"
            model_path.write_text("model", encoding="utf-8")
            executable = tmpdir_path / "llama-cli"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            config = VoiceGeneratorConfig(
                orpheus_runtime="llama-cpp",
                orpheus_model=model_path,
                orpheus_executable=str(executable),
                orpheus_decoder="snac",
            )
            registry = ProviderRegistry(config)

            statuses = {provider.id: provider.status for provider in registry.list_providers()}

            self.assertEqual(statuses["orpheus"], "ready")

    def test_orpheus_status_reflects_missing_executable(self) -> None:
        with TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "orpheus.gguf"
            model_path.write_text("model", encoding="utf-8")
            config = VoiceGeneratorConfig(
                orpheus_runtime="llama-cpp",
                orpheus_model=model_path,
                orpheus_executable="/tmp/missing-llama-cli",
                orpheus_decoder="snac",
            )
            registry = ProviderRegistry(config)

            statuses = {provider.id: provider.status for provider in registry.list_providers()}

            self.assertEqual(statuses["orpheus"], "missing-executable")
