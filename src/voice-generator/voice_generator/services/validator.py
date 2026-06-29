from __future__ import annotations

import os
import shutil
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.services.registry import ProviderRegistry


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check: str
    message: str
    severity: str = "error"
    path: Path | None = None


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


def validate_environment(
    config: VoiceGeneratorConfig,
    registry: ProviderRegistry | None = None,
) -> ValidationReport:
    registry = registry or ProviderRegistry()
    issues: list[ValidationIssue] = []

    issues.extend(_validate_ffmpeg(config))
    issues.extend(_validate_directories(config))
    issues.extend(_validate_default_provider(config, registry))
    issues.extend(_validate_provider_runtime(config, registry))
    issues.extend(_validate_cloud_credentials(config, registry))

    return ValidationReport(issues=issues)


def _validate_ffmpeg(config: VoiceGeneratorConfig) -> list[ValidationIssue]:
    if config.ffmpeg_path is not None:
        if config.ffmpeg_path.exists():
            return []
        return [
            ValidationIssue(
                check="ffmpeg",
                message=f"ffmpeg path does not exist: {config.ffmpeg_path}",
                path=config.ffmpeg_path,
            )
        ]

    if shutil.which("ffmpeg") is None:
        return [
            ValidationIssue(
                check="ffmpeg",
                message="ffmpeg was not found on PATH",
            )
        ]

    return []


def _validate_directories(config: VoiceGeneratorConfig) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for label, directory in (
        ("cache_directory", config.cache_directory),
        ("models_directory", config.models_directory),
    ):
        if directory is None:
            continue
        if directory.exists():
            continue
        issues.append(
            ValidationIssue(
                check=label,
                message=f"{label} does not exist: {directory}",
                path=directory,
            )
        )
    return issues


def _validate_default_provider(
    config: VoiceGeneratorConfig,
    registry: ProviderRegistry,
) -> list[ValidationIssue]:
    if config.default_provider is None:
        return []
    provider_ids = {provider.id for provider in registry.list_providers()}
    if config.default_provider not in provider_ids:
        return [
            ValidationIssue(
                check="default_provider",
                message=f"unknown default provider: {config.default_provider}",
            )
        ]
    return []


def _validate_provider_runtime(
    config: VoiceGeneratorConfig,
    registry: ProviderRegistry,
) -> list[ValidationIssue]:
    if config.default_provider is None:
        return []
    issues: list[ValidationIssue] = []
    try:
        provider = registry.get_provider(config.default_provider)
    except Exception as error:
        issues.append(
            ValidationIssue(
                check="provider",
                message=str(error),
            )
        )
        return issues
    try:
        provider.validate()
    except Exception as error:
        issues.append(
            ValidationIssue(
                check=config.default_provider,
                message=str(error),
            )
        )
    return issues


def _validate_cloud_credentials(
    config: VoiceGeneratorConfig,
    registry: ProviderRegistry,
) -> list[ValidationIssue]:
    if config.default_provider != "elevenlabs":
        return []
    if os.getenv("ELEVENLABS_API_KEY"):
        return []
    return [
        ValidationIssue(
            check="elevenlabs_api_key",
            message="ELEVENLABS_API_KEY is not set",
        )
    ]
