from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.decoders.snac import SnacDecoder
from voice_generator.errors import AudioGenerationError, MissingModelError, ProviderUnavailableError
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import AudioResult
from voice_generator.utils.audio import (
    ensure_output_path,
    normalize_output_format,
    output_format_from_path,
    resolve_output_path,
)
from voice_generator.utils.files import read_text
from voice_generator.utils.text import normalize_whitespace


CUSTOM_TOKEN_PATTERN = re.compile(r"<custom_token_(\d+)>")


class LlamaCppRuntime:
    id = "llama-cpp"
    name = "llama.cpp"

    def __init__(self, config: VoiceGeneratorConfig, decoder: SnacDecoder | None = None) -> None:
        self._config = config
        self._decoder = decoder or SnacDecoder()

    def validate(self) -> None:
        executable = self._resolve_executable()
        if executable is None:
            raise ProviderUnavailableError(
                "orpheus executable is not configured; set orpheus_executable"
            )
        if self._resolve_command_path(executable) is None:
            raise ProviderUnavailableError(f"orpheus executable not found: {executable}")
        if self._config.orpheus_model is None:
            raise MissingModelError("orpheus_model is required")
        if not self._config.orpheus_model.exists():
            raise MissingModelError(f"orpheus model not found: {self._config.orpheus_model}")

    def synthesize(self, request: VoiceRequest) -> AudioResult:
        self.validate()
        text = _resolve_text(request)
        voice = request.voice or self._config.default_voice or "default"
        output_format = output_format_from_path(request.output_path) or normalize_output_format(
            request.format
        )
        output_path = resolve_output_path(
            request.output_path,
            provider="orpheus",
            voice=voice,
            output_format=output_format,
        )
        ensure_output_path(output_path)

        prompt = self._build_prompt(text=text, voice=voice, request=request)
        command = self._build_command(prompt)

        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="voice-generator-orpheus-") as tempdir:
            tempdir_path = Path(tempdir)
            temp_audio = tempdir_path / "output.wav"
            try:
                completed = subprocess.run(command, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as error:
                raise AudioGenerationError(
                    f"orpheus runtime failed: {error.stderr or error.stdout or error}"
                ) from error

            payload = _collect_runtime_payload(completed)
            tokens = _extract_custom_tokens(payload)
            if not tokens:
                raise AudioGenerationError(
                    "orpheus runtime completed without producing audio tokens; "
                    "check that the selected runtime and model are Orpheus-compatible"
                )

            self._decoder.decode_tokens(tokens, temp_audio, format="wav")
            if output_format == "wav":
                output_path.write_bytes(temp_audio.read_bytes())
            else:
                from voice_generator.utils.audio import convert_audio_with_ffmpeg

                convert_audio_with_ffmpeg(
                    temp_audio,
                    output_path,
                    format=output_format,
                    ffmpeg_path=self._config.ffmpeg_path,
                )

        generation_time = time.perf_counter() - start
        return AudioResult(
            provider="orpheus",
            voice=voice,
            duration=None,
            sample_rate=None,
            output_file=output_path,
            generation_time=generation_time,
            metadata={
                "runtime": self.id,
                "executable": self._resolve_executable(),
                "decoder": self._decoder.id,
                "audio_tokens": [f"<custom_token_{token}>" for token in tokens],
                "audio_token_count": len(tokens),
            },
        )

    def _build_prompt(self, *, text: str, voice: str, request: VoiceRequest) -> str:
        instruction = "\n".join(
            [
                "You are Orpheus, a text-to-speech model.",
                "Output only <custom_token_xxxxx> audio tokens.",
                "Do not output English words, explanations, or punctuation outside tokens.",
                f"Target voice: {voice}.",
            ]
        )
        generation_prefix = "<custom_token_0>"
        user_message = normalize_whitespace(text)
        if request.emotion:
            user_message = f"{user_message}\nEmotion: {request.emotion}"
        if request.speed is not None:
            user_message = f"{user_message}\nSpeed: {request.speed}"
        if request.temperature is not None:
            user_message = f"{user_message}\nTemperature: {request.temperature}"
        if request.seed is not None:
            user_message = f"{user_message}\nSeed: {request.seed}"
        return "\n".join(
            [
                "<|begin_of_text|>",
                "<|start_header_id|>system<|end_header_id|>",
                instruction,
                "<|eot_id|>",
                "<|start_header_id|>user<|end_header_id|>",
                user_message,
                "<|eot_id|>",
                "<|start_header_id|>assistant<|end_header_id|>",
                generation_prefix,
            ]
        )

    def _build_command(self, prompt: str) -> list[str]:
        executable = self._resolve_executable()
        if executable is None:
            raise ProviderUnavailableError("orpheus executable is not configured")
        model = self._config.orpheus_model
        if model is None:
            raise MissingModelError("orpheus_model is required")
        return [
            executable,
            "--model",
            str(model.expanduser()),
            "--prompt",
            prompt,
            "--special",
            "--simple-io",
            "--single-turn",
            "--no-display-prompt",
            "--log-disable",
        ]

    def _resolve_executable(self) -> str | None:
        return self._config.orpheus_executable or "llama-cli"

    def _resolve_command_path(self, command: str) -> str | None:
        if Path(command).exists():
            return command
        return shutil.which(command)


def _resolve_text(request: VoiceRequest) -> str:
    if request.text is not None:
        return normalize_whitespace(request.text)
    if request.input_path is not None:
        return normalize_whitespace(read_text(request.input_path))
    raise AudioGenerationError("either text or input_path must be provided")


def _collect_runtime_payload(completed: subprocess.CompletedProcess[str]) -> str:
    stdout = completed.stdout.strip() if completed.stdout else ""
    stderr = completed.stderr.strip() if completed.stderr else ""
    if stdout and stderr:
        return "\n".join([stdout, stderr])
    return stdout or stderr


def _extract_custom_tokens(payload: str) -> list[int]:
    return [int(match.group(1)) for match in CUSTOM_TOKEN_PATTERN.finditer(payload)]
