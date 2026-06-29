from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from voice_generator.errors import ValidationError


@dataclass(frozen=True)
class VoiceGeneratorConfig:
    default_provider: str | None = None
    default_voice: str | None = None
    cache_directory: Path | None = None
    models_directory: Path | None = None
    ffmpeg_path: Path | None = None
    orpheus_command: str | None = None
    orpheus_model_path: Path | None = None
    orpheus_voice_catalog: Path | None = None
    orpheus_command_template: str | None = None

    @classmethod
    def from_file(cls, config_file: Path) -> "VoiceGeneratorConfig":
        payload = _load_simple_mapping(config_file)
        return cls(
            default_provider=payload.get("default_provider"),
            default_voice=payload.get("default_voice"),
            cache_directory=_optional_path(payload.get("cache_directory")),
            models_directory=_optional_path(payload.get("models_directory")),
            ffmpeg_path=_optional_path(payload.get("ffmpeg_path")),
            orpheus_command=payload.get("orpheus_command"),
            orpheus_model_path=_optional_path(payload.get("orpheus_model_path")),
            orpheus_voice_catalog=_optional_path(payload.get("orpheus_voice_catalog")),
            orpheus_command_template=payload.get("orpheus_command_template"),
        )

    def with_overrides(
        self,
        *,
        default_provider: str | None = None,
        default_voice: str | None = None,
        cache_directory: Path | None = None,
        models_directory: Path | None = None,
        ffmpeg_path: Path | None = None,
        orpheus_command: str | None = None,
        orpheus_model_path: Path | None = None,
        orpheus_voice_catalog: Path | None = None,
        orpheus_command_template: str | None = None,
    ) -> "VoiceGeneratorConfig":
        return VoiceGeneratorConfig(
            default_provider=default_provider if default_provider is not None else self.default_provider,
            default_voice=default_voice if default_voice is not None else self.default_voice,
            cache_directory=cache_directory if cache_directory is not None else self.cache_directory,
            models_directory=models_directory if models_directory is not None else self.models_directory,
            ffmpeg_path=ffmpeg_path if ffmpeg_path is not None else self.ffmpeg_path,
            orpheus_command=orpheus_command if orpheus_command is not None else self.orpheus_command,
            orpheus_model_path=(
                orpheus_model_path if orpheus_model_path is not None else self.orpheus_model_path
            ),
            orpheus_voice_catalog=(
                orpheus_voice_catalog
                if orpheus_voice_catalog is not None
                else self.orpheus_voice_catalog
            ),
            orpheus_command_template=(
                orpheus_command_template
                if orpheus_command_template is not None
                else self.orpheus_command_template
            ),
        )

    def validate(self) -> None:
        if self.default_provider is not None and not self.default_provider.strip():
            raise ValidationError("default_provider cannot be blank")
        if self.default_voice is not None and not self.default_voice.strip():
            raise ValidationError("default_voice cannot be blank")
        if self.orpheus_command is not None and not self.orpheus_command.strip():
            raise ValidationError("orpheus_command cannot be blank")
        if (
            self.orpheus_command_template is not None
            and not self.orpheus_command_template.strip()
        ):
            raise ValidationError("orpheus_command_template cannot be blank")


def _load_simple_mapping(config_file: Path) -> dict[str, str]:
    text = config_file.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    if text.startswith("{"):
        payload = json.loads(text)
        return {str(key): str(value) for key, value in payload.items() if value is not None}

    payload: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValidationError(
                f"invalid config line {raw_line!r}; expected a simple key: value mapping"
            )
        key, value = line.split(":", 1)
        payload[key.strip()] = _strip_scalar(value.strip())
    return payload


def _optional_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value)


def _strip_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value
