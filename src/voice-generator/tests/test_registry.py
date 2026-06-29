from __future__ import annotations

from unittest import TestCase

from voice_generator.services.registry import ProviderRegistry


class ProviderRegistryTests(TestCase):
    def test_list_providers_returns_planned_catalog(self) -> None:
        registry = ProviderRegistry()

        provider_ids = [provider.id for provider in registry.list_providers()]

        self.assertEqual(
            provider_ids,
            ["macos", "kokoro", "piper", "orpheus", "elevenlabs"],
        )
