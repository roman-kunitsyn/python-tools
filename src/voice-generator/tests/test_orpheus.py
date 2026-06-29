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

    def test_generate_supports_text_then_audio_pipeline(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model.gguf"
            model_path.write_text("model", encoding="utf-8")
            output_path = tmpdir_path / "result.wav"
            text_command = tmpdir_path / "llama-cli"
            text_command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            text_command.chmod(0o755)
            audio_command = tmpdir_path / "audio-runner"
            audio_command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            audio_command.chmod(0o755)
            config = VoiceGeneratorConfig(
                orpheus_command=text_command,
                orpheus_model_path=model_path,
                orpheus_audio_command=audio_command,
                orpheus_text_command_template=(
                    "{command} --model {model} --prompt {text} --simple-io --single-turn "
                    "--no-display-prompt --log-disable"
                ),
                orpheus_audio_command_template=(
                    "{command} --voice {voice} --text {generated_text} --output {output}"
                ),
            )
            provider = OrpheusProvider(config)
            calls: list[list[str]] = []

            def fake_run(command, check, capture_output, text):
                calls.append(command)
                if len(calls) == 1:
                    self.assertIn("--prompt", command)
                    self.assertNotIn("--voice", command)
                    return subprocess.CompletedProcess(command, 0, stdout="Hello Roman", stderr="")
                output_index = command.index("--output") + 1
                Path(command[output_index]).write_bytes(b"WAV")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

            with patch("voice_generator.providers.orpheus.subprocess.run", side_effect=fake_run), patch(
                "voice_generator.providers.orpheus.shutil.which",
                side_effect=lambda value: str(value) if value in {str(text_command), str(audio_command)} else None,
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

            self.assertEqual(len(calls), 2)
            self.assertTrue(response.output_file.exists())
            self.assertEqual(response.metadata["mode"], "text-audio")
            self.assertEqual(response.output_file, output_path)
