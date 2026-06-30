from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import (
    AudioGenerationError,
    ProviderUnavailableError,
    ValidationError,
)
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import AudioResult
from voice_generator.models.voice import VoiceInfo
from voice_generator.utils.audio import (
    convert_audio_with_ffmpeg,
    ensure_output_path,
    output_format_from_path,
    normalize_output_format,
    resolve_output_path,
)
from voice_generator.utils.files import read_text
from voice_generator.utils.text import normalize_whitespace


class MacOSSayProvider:
    id = "macos"
    name = "macOS Say"

    def __init__(self, config: VoiceGeneratorConfig) -> None:
        self._config = config

    def list_voices(self) -> list[VoiceInfo]:
        self.validate()
        command = ["say", "-v", "?"]
        completed = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
        )
        voices: list[VoiceInfo] = []
        for line in completed.stdout.splitlines():
            parsed = _parse_voice_line(line)
            if parsed is None:
                continue
            voices.append(
                VoiceInfo(
                    provider=self.id,
                    voice_id=parsed["name"],
                    name=parsed["name"],
                    language=parsed["language"],
                    gender=None,
                    tags=["macos", "say"],
                    installed=True,
                )
            )
        return voices

    def supports_streaming(self) -> bool:
        return False

    def supports_ssml(self) -> bool:
        return False

    def validate(self) -> None:
        if shutil.which("say") is None:
            raise ProviderUnavailableError("macOS say is not available on PATH")
        if shutil.which("ffmpeg") is None:
            raise ProviderUnavailableError("ffmpeg is required for output conversion")

    def synthesize(self, request: VoiceRequest) -> AudioResult:
        self.validate()
        if request.pitch is not None:
            raise ValidationError("macOS say does not support pitch control")

        text = _resolve_text(request)
        voice = request.voice or self._config.default_voice
        output_format = output_format_from_path(request.output_path) or normalize_output_format(
            request.format
        )
        output_path = resolve_output_path(
            request.output_path,
            provider=self.id,
            voice=voice or "voice",
            output_format=output_format,
        )
        ensure_output_path(output_path)

        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="voice-generator-macos-") as tempdir:
            temp_aiff = Path(tempdir) / "output.aiff"
            command = ["say"]
            if voice:
                command.extend(["-v", voice])
            if request.speed is not None:
                command.extend(["-r", str(_resolve_rate(request.speed))])
            command.extend(["-o", str(temp_aiff)])
            if request.input_path is not None:
                command.extend(["-f", str(request.input_path)])
            else:
                command.append(text)

            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as error:
                raise AudioGenerationError(
                    f"macOS say failed: {error.stderr or error.stdout or error}"
                ) from error

            if output_format == "wav":
                convert_audio_with_ffmpeg(
                    temp_aiff,
                    output_path,
                    format=output_format,
                    ffmpeg_path=self._config.ffmpeg_path,
                )
            else:
                output_path.write_bytes(temp_aiff.read_bytes())

        generation_time = time.perf_counter() - start
        return AudioResult(
            provider=self.id,
            voice=voice,
            duration=None,
            sample_rate=None,
            output_file=output_path,
            generation_time=generation_time,
            metadata={"engine": "say"},
        )

    def generate(self, request: VoiceRequest) -> AudioResult:
        return self.synthesize(request)


def _parse_voice_line(line: str) -> dict[str, str] | None:
    match = re.match(r"^(?P<name>.+?)\s{2,}(?P<language>\S+)\s+#\s*(?P<sample>.*)$", line)
    if match is None:
        return None
    return match.groupdict()


def _resolve_text(request: VoiceRequest) -> str:
    if request.text is not None:
        return normalize_whitespace(request.text)
    if request.input_path is not None:
        return normalize_whitespace(read_text(request.input_path))
    raise ValidationError("either text or input_path must be provided")


def _resolve_rate(speed: float) -> int:
    base_rate = 175
    return max(50, int(base_rate * speed))
