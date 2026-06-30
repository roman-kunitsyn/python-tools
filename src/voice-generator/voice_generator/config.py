from __future__ import annotations

import json
import os
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
    orpheus_runtime: str | None = None
    orpheus_model: Path | None = None
    orpheus_executable: str | None = None
    orpheus_decoder: str | None = None
    orpheus_voice_catalog: Path | None = None

    @classmethod
    def from_file(cls, config_file: Path) -> "VoiceGeneratorConfig":
        payload = _load_config_payload(config_file)
        return cls(
            default_provider=_optional_text(payload.get("default_provider")),
            default_voice=_optional_text(
                payload.get("default_voice") or payload.get("orpheus_default_voice")
            ),
            cache_directory=_optional_path(payload.get("cache_directory")),
            models_directory=_optional_path(payload.get("models_directory")),
            ffmpeg_path=_optional_path(payload.get("ffmpeg_path")),
            orpheus_runtime=_optional_text(
                payload.get("orpheus_runtime") or payload.get("runtime")
            ),
            orpheus_model=_optional_path(payload.get("orpheus_model") or payload.get("model")),
            orpheus_executable=_optional_text(
                payload.get("orpheus_executable") or payload.get("orpheus_command")
            ),
            orpheus_decoder=_optional_text(payload.get("orpheus_decoder")),
            orpheus_voice_catalog=_optional_path(
                payload.get("orpheus_voice_catalog") or payload.get("voice_catalog")
            ),
        )

    def with_overrides(
        self,
        *,
        default_provider: str | None = None,
        default_voice: str | None = None,
        cache_directory: Path | None = None,
        models_directory: Path | None = None,
        ffmpeg_path: Path | None = None,
        orpheus_runtime: str | None = None,
        orpheus_model: Path | None = None,
        orpheus_executable: str | None = None,
        orpheus_decoder: str | None = None,
        orpheus_voice_catalog: Path | None = None,
    ) -> "VoiceGeneratorConfig":
        return VoiceGeneratorConfig(
            default_provider=default_provider if default_provider is not None else self.default_provider,
            default_voice=default_voice if default_voice is not None else self.default_voice,
            cache_directory=cache_directory if cache_directory is not None else self.cache_directory,
            models_directory=models_directory if models_directory is not None else self.models_directory,
            ffmpeg_path=ffmpeg_path if ffmpeg_path is not None else self.ffmpeg_path,
            orpheus_runtime=orpheus_runtime if orpheus_runtime is not None else self.orpheus_runtime,
            orpheus_model=orpheus_model if orpheus_model is not None else self.orpheus_model,
            orpheus_executable=(
                orpheus_executable if orpheus_executable is not None else self.orpheus_executable
            ),
            orpheus_decoder=orpheus_decoder if orpheus_decoder is not None else self.orpheus_decoder,
            orpheus_voice_catalog=(
                orpheus_voice_catalog if orpheus_voice_catalog is not None else self.orpheus_voice_catalog
            ),
        )

    def validate(self) -> None:
        if self.default_provider is not None and not self.default_provider.strip():
            raise ValidationError("default_provider cannot be blank")
        if self.default_voice is not None and not self.default_voice.strip():
            raise ValidationError("default_voice cannot be blank")
        if self.orpheus_runtime is not None and not self.orpheus_runtime.strip():
            raise ValidationError("orpheus_runtime cannot be blank")
        if self.orpheus_executable is not None and not self.orpheus_executable.strip():
            raise ValidationError("orpheus_executable cannot be blank")
        if self.orpheus_decoder is not None and not self.orpheus_decoder.strip():
            raise ValidationError("orpheus_decoder cannot be blank")


def _load_config_payload(config_file: Path) -> dict[str, str]:
    text = config_file.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    if text.startswith("{"):
        payload = json.loads(text)
        return _flatten_json_payload(payload)
    return _parse_simple_mapping(text)


def _flatten_json_payload(payload: object, prefix: str = "") -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    flattened: dict[str, str] = {}
    for key, value in payload.items():
        nested_key = f"{prefix}{key}" if prefix else str(key)
        if isinstance(value, dict):
            flattened.update(_flatten_json_payload(value, prefix=f"{nested_key}_"))
        elif value is not None:
            flattened[nested_key] = str(value)
    return flattened


def _parse_simple_mapping(text: str) -> dict[str, str]:
    payload: dict[str, str] = {}
    current_prefix: str | None = None
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if indent == 0:
            if line.endswith(":"):
                current_prefix = line[:-1].strip()
                continue
            if ":" not in line:
                raise ValidationError(
                    f"invalid config line {raw_line!r}; expected key: value"
                )
            key, value = line.split(":", 1)
            payload[key.strip()] = _strip_scalar(value.strip())
            current_prefix = None
            continue
        if current_prefix is None:
            raise ValidationError(
                f"invalid nested config line {raw_line!r}; expected a section header first"
            )
        if ":" not in line:
            raise ValidationError(
                f"invalid nested config line {raw_line!r}; expected key: value"
            )
        key, value = line.split(":", 1)
        payload[f"{current_prefix}_{key.strip()}"] = _strip_scalar(value.strip())
    return payload


def _optional_path(value: str | None) -> Path | None:
    if value is None or value == "":
        return None
    return Path(value).expanduser()


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    return text


def _strip_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _env_text(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return None
    return value


def _env_path(name: str) -> Path | None:
    value = _env_text(name)
    if value is None:
        return None
    return Path(value).expanduser()


def apply_environment_overrides(config: VoiceGeneratorConfig) -> VoiceGeneratorConfig:
    runtime = _env_text("VOICE_GENERATOR_ORPHEUS_RUNTIME")
    model = _env_path("VOICE_GENERATOR_ORPHEUS_MODEL") or _env_path(
        "VOICE_GENERATOR_ORPHEUS_MODEL_PATH"
    )
    executable = _env_text("VOICE_GENERATOR_ORPHEUS_EXECUTABLE") or _env_text(
        "VOICE_GENERATOR_ORPHEUS_COMMAND"
    )
    decoder = _env_text("VOICE_GENERATOR_ORPHEUS_DECODER")
    return config.with_overrides(
        default_provider=_env_text("VOICE_GENERATOR_DEFAULT_PROVIDER"),
        default_voice=_env_text("VOICE_GENERATOR_DEFAULT_VOICE"),
        cache_directory=_env_path("VOICE_GENERATOR_CACHE_DIRECTORY"),
        models_directory=_env_path("VOICE_GENERATOR_MODELS_DIRECTORY"),
        ffmpeg_path=_env_path("VOICE_GENERATOR_FFMPEG_PATH"),
        orpheus_runtime=runtime,
        orpheus_model=model,
        orpheus_executable=executable,
        orpheus_decoder=decoder,
        orpheus_voice_catalog=_env_path("VOICE_GENERATOR_ORPHEUS_VOICE_CATALOG"),
    )
