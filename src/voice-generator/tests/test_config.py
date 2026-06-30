from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from voice_generator.config import VoiceGeneratorConfig, apply_environment_overrides


class VoiceGeneratorConfigTests(TestCase):
    def test_from_file_parses_nested_orpheus_section(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "voice-generator.yaml"
            config_file.write_text(
                "\n".join(
                    [
                        "default_provider: orpheus",
                        "orpheus:",
                        "  runtime: llama-cpp",
                        "  model: /tmp/models/orpheus.gguf",
                        "  executable: /opt/homebrew/bin/llama-cli",
                        "  decoder: snac",
                        "  default_voice: tara",
                    ]
                ),
                encoding="utf-8",
            )

            config = VoiceGeneratorConfig.from_file(config_file)

            self.assertEqual(config.default_provider, "orpheus")
            self.assertEqual(config.default_voice, "tara")
            self.assertEqual(config.orpheus_runtime, "llama-cpp")
            self.assertEqual(config.orpheus_model, Path("/tmp/models/orpheus.gguf"))
            self.assertEqual(config.orpheus_executable, "/opt/homebrew/bin/llama-cli")
            self.assertEqual(config.orpheus_decoder, "snac")

    def test_environment_overrides_apply(self) -> None:
        config = VoiceGeneratorConfig()

        with patch.dict(
            "os.environ",
            {
                "VOICE_GENERATOR_ORPHEUS_RUNTIME": "llama-cpp",
                "VOICE_GENERATOR_ORPHEUS_MODEL": "/tmp/orpheus.gguf",
                "VOICE_GENERATOR_ORPHEUS_EXECUTABLE": "llama-cli",
                "VOICE_GENERATOR_ORPHEUS_DECODER": "snac",
            },
            clear=False,
        ):
            overridden = apply_environment_overrides(config)

        self.assertEqual(overridden.orpheus_runtime, "llama-cpp")
        self.assertEqual(overridden.orpheus_model, Path("/tmp/orpheus.gguf"))
        self.assertEqual(overridden.orpheus_executable, "llama-cli")
        self.assertEqual(overridden.orpheus_decoder, "snac")
