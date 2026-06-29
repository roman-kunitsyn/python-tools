from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from voice_generator.config import VoiceGeneratorConfig
from voice_generator.errors import FeatureNotImplementedError, VoiceGeneratorError
from voice_generator.models.request import VoiceRequest
from voice_generator.services.benchmark import run_benchmark
from voice_generator.services.generator import generate_voice
from voice_generator.services.registry import ProviderRegistry
from voice_generator.services.validator import validate_environment

console = Console()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voice-generator",
        description="Generate speech audio from text through a provider registry.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional config file with default provider and path settings.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose diagnostic output.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("providers", help="List available providers.")

    voices_parser = subparsers.add_parser("voices", help="List known voices.")
    voices_parser.add_argument(
        "--provider",
        default=None,
        help="Limit the voice catalog to one provider.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate runtime dependencies.")
    validate_parser.add_argument(
        "--provider",
        default=None,
        help="Validate credentials for a specific provider.",
    )

    generate_parser = subparsers.add_parser("generate", help="Generate speech audio.")
    generate_parser.add_argument("--provider", default=None)
    generate_parser.add_argument("--voice", default=None)
    generate_parser.add_argument("--text", default=None)
    generate_parser.add_argument("--input", dest="input_path", type=Path, default=None)
    generate_parser.add_argument("--output", dest="output_path", type=Path, default=None)
    generate_parser.add_argument("--format", default="wav")
    generate_parser.add_argument("--language", default=None)
    generate_parser.add_argument("--emotion", default=None)
    generate_parser.add_argument("--speed", type=float, default=None)
    generate_parser.add_argument("--pitch", type=float, default=None)
    generate_parser.add_argument("--temperature", type=float, default=None)
    generate_parser.add_argument("--seed", type=int, default=None)
    generate_parser.add_argument("--stream", action="store_true")

    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark a provider.")
    benchmark_parser.add_argument("--provider", default=None)

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = _load_config(args.config)
        if args.verbose:
            console.print("[dim]Verbose mode enabled[/dim]")

        if args.command == "providers":
            return _run_providers()
        if args.command == "voices":
            return _run_voices(args.provider, config)
        if args.command == "validate":
            return _run_validate(args.provider, config)
        if args.command == "generate":
            return _run_generate(args, config)
        if args.command == "benchmark":
            return _run_benchmark(args.provider)
        parser.error(f"unknown command: {args.command}")
    except VoiceGeneratorError as error:
        console.print(f"[red]{error}[/red]", file=sys.stderr)
        return error.exit_code
    except FileNotFoundError as error:
        console.print(f"[red]{error}[/red]", file=sys.stderr)
        return 3
    except ValueError as error:
        console.print(f"[red]{error}[/red]", file=sys.stderr)
        return 1


def _run_providers() -> int:
    registry = ProviderRegistry()
    table = Table(title="Voice Providers")
    table.add_column("Provider")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("Streaming")
    table.add_column("SSML")
    for provider in registry.list_providers():
        table.add_row(
            provider.id,
            provider.name,
            provider.status,
            "yes" if provider.supports_streaming else "no",
            "yes" if provider.supports_ssml else "no",
        )
    console.print(table)
    return 0


def _run_voices(provider: str | None, config: VoiceGeneratorConfig) -> int:
    registry = ProviderRegistry()
    provider_id = provider or config.default_provider
    voices = registry.list_voices(provider_id)
    table = Table(title="Voice Catalog")
    table.add_column("Provider")
    table.add_column("Voice ID")
    table.add_column("Name")
    table.add_column("Language")
    table.add_column("Gender")
    table.add_column("Tags")
    table.add_column("Installed")
    for voice in voices:
        table.add_row(
            voice.provider,
            voice.voice_id,
            voice.name,
            voice.language or "",
            voice.gender or "",
            ", ".join(voice.tags),
            "yes" if voice.installed else "no",
        )
    console.print(table)
    if not voices:
        console.print("[dim]No provider backends are implemented yet.[/dim]")
    return 0


def _run_validate(provider: str | None, config: VoiceGeneratorConfig) -> int:
    target_config = config
    if provider is not None:
        target_config = config.with_overrides(default_provider=provider)
    report = validate_environment(target_config)
    if report.issues:
        table = Table(title="Validation Issues")
        table.add_column("Check")
        table.add_column("Severity")
        table.add_column("Message")
        for issue in report.issues:
            table.add_row(issue.check, issue.severity, issue.message)
        console.print(table)
    else:
        console.print("[green]Environment looks ready.[/green]")
    return 0 if report.ok else 1


def _run_generate(args: argparse.Namespace, config: VoiceGeneratorConfig) -> int:
    request = VoiceRequest(
        provider=args.provider or config.default_provider,
        voice=args.voice or config.default_voice,
        text=args.text,
        input_path=args.input_path,
        output_path=args.output_path,
        format=args.format,
        language=args.language,
        emotion=args.emotion,
        speed=args.speed,
        pitch=args.pitch,
        temperature=args.temperature,
        seed=args.seed,
        stream=args.stream,
    )
    result = generate_voice(request, config)
    console.print(result.model_dump())
    return 0


def _run_benchmark(provider: str | None) -> int:
    result = run_benchmark(provider)
    console.print(result.model_dump())
    return 0


def _load_config(config_file: Path | None) -> VoiceGeneratorConfig:
    if config_file is None:
        return VoiceGeneratorConfig()
    return VoiceGeneratorConfig.from_file(config_file)
