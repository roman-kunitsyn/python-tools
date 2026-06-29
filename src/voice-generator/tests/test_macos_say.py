from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.models.request import VoiceRequest
from voice_generator.providers.macos_say import MacOSSayProvider


class MacOSSayProviderTests(TestCase):
    def test_list_voices_parses_say_output(self) -> None:
        config = VoiceGeneratorConfig()
        provider = MacOSSayProvider(config)

        completed = subprocess.CompletedProcess(
            args=["say", "-v", "?"],
            returncode=0,
            stdout="Alice               it_IT    # Ciao! Mi chiamo Alice.\n",
            stderr="",
        )

        with patch("voice_generator.providers.macos_say.shutil.which", return_value="/usr/bin/say"), patch(
            "voice_generator.providers.macos_say.subprocess.run",
            return_value=completed,
        ):
            voices = provider.list_voices()

        self.assertEqual(len(voices), 1)
        self.assertEqual(voices[0].voice_id, "Alice")
        self.assertEqual(voices[0].language, "it_IT")

    def test_generate_writes_wav_output_by_default(self) -> None:
        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "sample.wav"
            config = VoiceGeneratorConfig()
            provider = MacOSSayProvider(config)

            def fake_run(command, check, capture_output, text):
                self.assertEqual(command[0], "say")
                self.assertIn("-o", command)
                output_index = command.index("-o") + 1
                Path(command[output_index]).write_bytes(b"AIFF")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            def fake_convert_audio_with_ffmpeg(input_path, output_path, format, ffmpeg_path):
                output_path.write_bytes(b"WAV")

            with patch("voice_generator.providers.macos_say.shutil.which", return_value="/usr/bin/say"), patch(
                "voice_generator.providers.macos_say.subprocess.run",
                side_effect=fake_run,
            ), patch(
                "voice_generator.providers.macos_say.convert_audio_with_ffmpeg",
                side_effect=fake_convert_audio_with_ffmpeg,
            ):
                response = provider.generate(
                    VoiceRequest(
                        provider="macos",
                        voice="Alice",
                        text="Hello world",
                        output_path=output_path,
                    )
                )

            self.assertTrue(response.output_file.exists())
            self.assertEqual(response.output_file, output_path)
            self.assertEqual(response.output_file.suffix, ".wav")
            self.assertEqual(response.metadata["engine"], "say")
