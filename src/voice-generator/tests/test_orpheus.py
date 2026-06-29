from __future__ import annotations

import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.models.request import VoiceRequest
from voice_generator.providers.orpheus import OrpheusProvider


class OrpheusProviderTests(TestCase):
    def test_list_voices_parses_json_catalog(self) -> None:
        with TemporaryDirectory() as tmpdir:
            catalog = Path(tmpdir) / "voices.json"
            catalog.write_text(
                json.dumps(
                    [
                        {
                            "voice_id": "tara",
                            "name": "Tara",
                            "language": "en",
                            "gender": "female",
                            "tags": ["warm"],
                        }
                    ]
                ),
                encoding="utf-8",
            )
            model_path = Path(tmpdir) / "model.gguf"
            model_path.write_text("model", encoding="utf-8")
            config = VoiceGeneratorConfig(
                orpheus_command="orpheus-runner",
                orpheus_model_path=model_path,
                orpheus_voice_catalog=catalog,
            )
            provider = OrpheusProvider(config)

            voices = provider.list_voices()

            self.assertEqual(len(voices), 1)
            self.assertEqual(voices[0].voice_id, "tara")
            self.assertEqual(voices[0].tags, ["warm"])

    def test_generate_builds_command_and_writes_output(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model.gguf"
            model_path.write_text("model", encoding="utf-8")
            output_path = tmpdir_path / "result.wav"
            config = VoiceGeneratorConfig(
                orpheus_command="orpheus-runner",
                orpheus_model_path=model_path,
                orpheus_command_template=(
                    "{command} --model {model} --voice {voice} --text {text} --output {output}"
                ),
            )
            provider = OrpheusProvider(config)

            def fake_run(command, check, capture_output, text):
                self.assertIn("orpheus-runner", command[0])
                output_index = command.index("--output") + 1
                Path(command[output_index]).write_bytes(b"WAV")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with patch("voice_generator.providers.orpheus.shutil.which", return_value="/usr/bin/orpheus-runner"), patch(
                "voice_generator.providers.orpheus.subprocess.run",
                side_effect=fake_run,
            ):
                response = provider.generate(
                    VoiceRequest(
                        provider="orpheus",
                        voice="tara",
                        text="Hello from Orpheus",
                        output_path=output_path,
                        format="wav",
                    )
                )

            self.assertTrue(response.output_file.exists())
            self.assertEqual(response.output_file, output_path)
            self.assertEqual(response.metadata["engine"], "orpheus")
