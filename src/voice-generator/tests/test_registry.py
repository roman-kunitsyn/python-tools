from __future__ import annotations

from unittest import TestCase
from pathlib import Path
from tempfile import TemporaryDirectory

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
            model_path = Path(tmpdir) / "orpheus.gguf"
            model_path.write_text("model", encoding="utf-8")
            config = VoiceGeneratorConfig(
                orpheus_command="/tmp/orpheus-runner",
                orpheus_model_path=model_path,
            )
            registry = ProviderRegistry(config)

            statuses = {provider.id: provider.status for provider in registry.list_providers()}

            self.assertEqual(statuses["orpheus"], "missing-runtime")

    def test_orpheus_status_reflects_audio_pipeline_runtime(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = Path(tmpdir) / "orpheus.gguf"
            model_path.write_text("model", encoding="utf-8")
            text_command = tmpdir_path / "orpheus-runner"
            text_command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            text_command.chmod(0o755)
            config = VoiceGeneratorConfig(
                orpheus_command=str(text_command),
                orpheus_model_path=model_path,
                orpheus_audio_command="/tmp/audio-runner",
            )
            registry = ProviderRegistry(config)

            statuses = {provider.id: provider.status for provider in registry.list_providers()}

            self.assertEqual(statuses["orpheus"], "missing-audio-runtime")
