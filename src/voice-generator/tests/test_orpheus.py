from __future__ import annotations

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.models.request import VoiceRequest
from voice_generator.providers.orpheus import OrpheusProvider
from voice_generator.runtimes.registry import OrpheusRuntimeRegistry


class OrpheusProviderTests(TestCase):
    def test_runtime_registry_selects_llama_cpp(self) -> None:
        config = VoiceGeneratorConfig(orpheus_runtime="llama-cpp")
        runtime = OrpheusRuntimeRegistry(config).get_runtime()

        self.assertEqual(runtime.id, "llama-cpp")

    def test_runtime_registry_selects_official_python(self) -> None:
        config = VoiceGeneratorConfig(orpheus_runtime="official-python")
        runtime = OrpheusRuntimeRegistry(config).get_runtime()

        self.assertEqual(runtime.id, "official-python")

    def test_generate_builds_audio_output_from_runtime_tokens(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model.gguf"
            model_path.write_text("model", encoding="utf-8")
            executable = tmpdir_path / "llama-cli"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            output_path = tmpdir_path / "result.wav"
            config = VoiceGeneratorConfig(
                orpheus_runtime="llama-cpp",
                orpheus_model=model_path,
                orpheus_executable=str(executable),
                orpheus_decoder="snac",
                default_voice="tara",
            )
            provider = OrpheusProvider(config)

            def fake_run(command, check, capture_output, text):
                self.assertEqual(command[0], str(executable))
                self.assertIn("--prompt", command)
                self.assertIn("--special", command)
                prompt = command[command.index("--prompt") + 1]
                self.assertIn("<|begin_of_text|>", prompt)
                self.assertIn("<|start_header_id|>assistant<|end_header_id|>", prompt)
                self.assertIn("<custom_token_0>", prompt)
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="<custom_token_1><custom_token_2><custom_token_3><custom_token_4>",
                    stderr="",
                )

            with patch("voice_generator.runtimes.llama_cpp.subprocess.run", side_effect=fake_run), patch(
                "voice_generator.decoders.snac._load_snac_model"
            ) as load_model, patch("voice_generator.decoders.snac._reconstruct_codebooks") as reconstruct:
                load_model.return_value.decode.return_value = [0.0, 0.1, -0.1, 0.0]
                reconstruct.return_value = [[1, 2], [3], [4], [5]]
                response = provider.synthesize(
                    VoiceRequest(
                        provider="orpheus",
                        voice="tara",
                        text="Hello Roman",
                        output_path=output_path,
                        format="wav",
                    )
                )

            self.assertTrue(response.output_file.exists())
            self.assertEqual(response.output_file, output_path)
            self.assertEqual(response.metadata["runtime"], "llama-cpp")
            self.assertEqual(response.metadata["decoder"], "snac")
            self.assertEqual(
                response.metadata["audio_tokens"],
                [
                    "<custom_token_1>",
                    "<custom_token_2>",
                    "<custom_token_3>",
                    "<custom_token_4>",
                ],
            )
            self.assertEqual(response.metadata["audio_token_count"], 4)

    def test_generate_accepts_tokens_from_stderr(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model.gguf"
            model_path.write_text("model", encoding="utf-8")
            executable = tmpdir_path / "llama-cli"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            output_path = tmpdir_path / "result.wav"
            config = VoiceGeneratorConfig(
                orpheus_runtime="llama-cpp",
                orpheus_model=model_path,
                orpheus_executable=str(executable),
                orpheus_decoder="snac",
            )
            provider = OrpheusProvider(config)

            def fake_run(command, check, capture_output, text):
                return subprocess.CompletedProcess(
                    command,
                    0,
                    stdout="",
                    stderr="<custom_token_1><custom_token_2><custom_token_3><custom_token_4>",
                )

            with patch("voice_generator.runtimes.llama_cpp.subprocess.run", side_effect=fake_run), patch(
                "voice_generator.decoders.snac._load_snac_model"
            ) as load_model, patch("voice_generator.decoders.snac._reconstruct_codebooks") as reconstruct:
                load_model.return_value.decode.return_value = [0.0, 0.1, -0.1, 0.0]
                reconstruct.return_value = [[1, 2], [3], [4], [5]]
                response = provider.synthesize(
                    VoiceRequest(
                        provider="orpheus",
                        voice="tara",
                        text="Hello Roman",
                        output_path=output_path,
                        format="wav",
                    )
                )

            self.assertTrue(response.output_file.exists())
            self.assertEqual(response.output_file, output_path)

    def test_generate_supports_generate_alias(self) -> None:
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            model_path = tmpdir_path / "model.gguf"
            model_path.write_text("model", encoding="utf-8")
            executable = tmpdir_path / "llama-cli"
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            executable.chmod(0o755)
            output_path = tmpdir_path / "result.wav"
            config = VoiceGeneratorConfig(
                orpheus_runtime="llama-cpp",
                orpheus_model=model_path,
                orpheus_executable=str(executable),
                orpheus_decoder="snac",
            )
            provider = OrpheusProvider(config)

            with patch("voice_generator.runtimes.llama_cpp.subprocess.run") as run_mock, patch(
                "voice_generator.decoders.snac._load_snac_model"
            ) as load_model, patch("voice_generator.decoders.snac._reconstruct_codebooks") as reconstruct:
                run_mock.return_value = subprocess.CompletedProcess(
                    ["llama-cli"],
                    0,
                    stdout="<custom_token_1><custom_token_2><custom_token_3><custom_token_4>",
                    stderr="",
                )
                load_model.return_value.decode.return_value = [0.0, 0.1, -0.1, 0.0]
                reconstruct.return_value = [[1, 2], [3], [4], [5]]
                response = provider.generate(
                    VoiceRequest(
                        provider="orpheus",
                        voice="tara",
                        text="Hello Roman",
                        output_path=output_path,
                        format="wav",
                    )
                )

            self.assertTrue(response.output_file.exists())
