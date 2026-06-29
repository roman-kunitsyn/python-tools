from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from voice_generator.config import VoiceGeneratorConfig


class VoiceGeneratorConfigTests(TestCase):
    def test_from_file_parses_simple_mapping(self) -> None:
        with TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "voice-generator.yaml"
            config_file.write_text(
                "\n".join(
                    [
                        "default_provider: orpheus",
                        "default_voice: tara",
                        "cache_directory: /tmp/voice-cache",
                        "models_directory: /tmp/voice-models",
                        "ffmpeg_path: /opt/homebrew/bin/ffmpeg",
                    ]
                ),
                encoding="utf-8",
            )

            config = VoiceGeneratorConfig.from_file(config_file)

            self.assertEqual(config.default_provider, "orpheus")
            self.assertEqual(config.default_voice, "tara")
            self.assertEqual(config.cache_directory, Path("/tmp/voice-cache"))
            self.assertEqual(config.models_directory, Path("/tmp/voice-models"))
            self.assertEqual(config.ffmpeg_path, Path("/opt/homebrew/bin/ffmpeg"))
