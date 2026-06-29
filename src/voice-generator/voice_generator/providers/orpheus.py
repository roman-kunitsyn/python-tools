from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import (
    AudioGenerationError,
    MissingModelError,
    ProviderUnavailableError,
    ValidationError,
)
from voice_generator.models.request import VoiceRequest
from voice_generator.models.response import VoiceResponse
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


class OrpheusProvider:
    id = "orpheus"
    name = "Orpheus"

    def __init__(self, config: VoiceGeneratorConfig) -> None:
        self._config = config

    def list_voices(self) -> list[VoiceInfo]:
        catalog = self._load_voice_catalog()
        if catalog is not None:
            return catalog
        default_voice = self._config.default_voice
        if default_voice is None:
            return []
        return [
            VoiceInfo(
                provider=self.id,
                voice_id=default_voice,
                name=default_voice,
                language=None,
                gender=None,
                tags=["orpheus"],
                installed=False,
            )
        ]

    def supports_streaming(self) -> bool:
        return False

    def supports_ssml(self) -> bool:
        return False

    def validate(self) -> None:
        command = self._resolve_command()
        if command is None:
            raise ProviderUnavailableError(
                "orpheus runtime command is not configured; set orpheus_command"
            )
        if self._resolve_command_path(command) is None:
            raise ProviderUnavailableError(f"orpheus runtime command not found: {command}")
        if self._config.orpheus_model_path is None:
            raise MissingModelError("orpheus_model_path is required")
        if not self._config.orpheus_model_path.exists():
            raise MissingModelError(
                f"orpheus model not found: {self._config.orpheus_model_path}"
            )
        if self._config.orpheus_voice_catalog is not None and not self._config.orpheus_voice_catalog.exists():
            raise ValidationError(
                f"orpheus voice catalog not found: {self._config.orpheus_voice_catalog}"
            )

    def generate(self, request: VoiceRequest) -> VoiceResponse:
        self.validate()
        text = _resolve_text(request)
        voice = request.voice or self._config.default_voice or "default"
        output_format = output_format_from_path(request.output_path) or normalize_output_format(
            request.format
        )
        output_path = resolve_output_path(
            request.output_path,
            provider=self.id,
            voice=voice,
            output_format=output_format,
        )
        ensure_output_path(output_path)

        start = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="voice-generator-orpheus-") as tempdir:
            temp_output = Path(tempdir) / "output.wav"
            command = self._build_command(
                text=text,
                voice=voice,
                output_path=temp_output,
                request=request,
            )
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as error:
                raise AudioGenerationError(
                    f"orpheus runtime failed: {error.stderr or error.stdout or error}"
                ) from error

            if not temp_output.exists():
                raise AudioGenerationError(
                    "orpheus runtime completed without producing the expected wav file"
                )

            if output_format == "wav":
                output_path.write_bytes(temp_output.read_bytes())
            else:
                convert_audio_with_ffmpeg(
                    temp_output,
                    output_path,
                    format=output_format,
                    ffmpeg_path=self._config.ffmpeg_path,
                )

        generation_time = time.perf_counter() - start
        return VoiceResponse(
            provider=self.id,
            voice=voice,
            duration=None,
            sample_rate=None,
            output_file=output_path,
            generation_time=generation_time,
            metadata={"engine": "orpheus"},
        )

    def _load_voice_catalog(self) -> list[VoiceInfo] | None:
        if self._config.orpheus_voice_catalog is None:
            return None
        payload = self._config.orpheus_voice_catalog.read_text(encoding="utf-8").strip()
        if not payload:
            return []
        if payload.startswith("["):
            data = json.loads(payload)
            return [_voice_from_json(item) for item in data]
        voices: list[VoiceInfo] = []
        for line in payload.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            voices.append(
                VoiceInfo(
                    provider=self.id,
                    voice_id=line,
                    name=line,
                    language=None,
                    gender=None,
                    tags=["orpheus"],
                    installed=True,
                )
            )
        return voices

    def _build_command(
        self,
        *,
        text: str,
        voice: str,
        output_path: Path,
        request: VoiceRequest,
    ) -> list[str]:
        command = self._resolve_command()
        if command is None:
            raise ProviderUnavailableError("orpheus runtime command is not configured")
        template = self._config.orpheus_command_template or (
            "{command} --model {model} --voice {voice} --text {text} --output {output}"
        )
        rendered = template.format(
            command=shlex.quote(command),
            model=shlex.quote(str(self._config.orpheus_model_path)),
            voice=shlex.quote(voice),
            text=shlex.quote(text),
            output=shlex.quote(str(output_path)),
            format=shlex.quote(normalize_output_format(request.format)),
            emotion=shlex.quote(request.emotion or ""),
            speed=shlex.quote(str(request.speed if request.speed is not None else "")),
            pitch=shlex.quote(str(request.pitch if request.pitch is not None else "")),
            temperature=shlex.quote(
                str(request.temperature if request.temperature is not None else "")
            ),
            seed=shlex.quote(str(request.seed if request.seed is not None else "")),
        )
        return shlex.split(rendered)

    def _resolve_command(self) -> str | None:
        return self._config.orpheus_command or "llama-cli"

    def _resolve_command_path(self, command: str) -> str | None:
        if Path(command).exists():
            return command
        return shutil.which(command)


def _voice_from_json(payload: object) -> VoiceInfo:
    if not isinstance(payload, dict):
        name = str(payload)
        return VoiceInfo(
            provider="orpheus",
            voice_id=name,
            name=name,
            language=None,
            gender=None,
            tags=["orpheus"],
            installed=True,
        )
    voice_id = str(payload.get("voice_id") or payload.get("id") or payload.get("name") or "")
    if not voice_id:
        raise ValidationError("orpheus voice catalog entry is missing a voice id")
    tags = payload.get("tags")
    if isinstance(tags, list):
        normalized_tags = [str(tag) for tag in tags]
    else:
        normalized_tags = ["orpheus"]
    return VoiceInfo(
        provider="orpheus",
        voice_id=voice_id,
        name=str(payload.get("name") or voice_id),
        language=(str(payload["language"]) if payload.get("language") is not None else None),
        gender=(str(payload["gender"]) if payload.get("gender") is not None else None),
        tags=normalized_tags,
        installed=bool(payload.get("installed", True)),
    )


def _resolve_text(request: VoiceRequest) -> str:
    if request.text is not None:
        return normalize_whitespace(request.text)
    if request.input_path is not None:
        return normalize_whitespace(read_text(request.input_path))
    raise ValidationError("either text or input_path must be provided")
