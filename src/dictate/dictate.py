#!/usr/bin/env python3

"""
dictate.py

Simple voice dictation CLI.

Workflow

    Record microphone
            ↓
      Save temp wav
            ↓
      Run whisper-cli
            ↓
      Print transcript

Examples

    dictate

    dictate --language en

    dictate --model small.en

    dictate --output text.txt

    dictate --duration 5

    :r !dictate
"""

from __future__ import annotations

import argparse
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "0.1.0"
DEFAULT_LANGUAGE = "auto"
DEFAULT_MODEL = "small"
DEFAULT_MODEL_DIR = Path.home() / "whisper" / "models"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1


class DictateError(RuntimeError):
    pass


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dictate",
        description="Voice dictation.",
    )

    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Language passed to whisper-cli. Default: auto.",
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name or model file path. Default: small.",
    )

    parser.add_argument(
        "--output",
        help="Write the transcript to this file instead of stdout.",
    )

    parser.add_argument(
        "--device",
        help="Audio input device name or id. Defaults to the system input device.",
    )

    parser.add_argument(
        "--duration",
        type=float,
        help="Maximum recording duration in seconds.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print command details while recording and transcribing.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Recording
# ---------------------------------------------------------


def resolve_input_device(device: str | None) -> str:
    system = platform.system().lower()

    if system == "darwin":
        return _resolve_avfoundation_input(device)

    if system == "windows":
        name = device or "default"
        return name if name.startswith("audio=") else f"audio={name}"

    if system == "linux":
        return device or "default"

    raise DictateError(f"Unsupported platform: {platform.system()}")


def _resolve_avfoundation_input(device: str | None) -> str:
    if device is None:
        return ":0"

    if device.isdigit():
        return f":{device}"

    if device.startswith(":"):
        return device

    devices = _list_avfoundation_devices()
    for audio_device in devices:
        if device == audio_device["name"]:
            return f":{audio_device['id']}"

    normalized_device = _normalize_device_name(device)
    for audio_device in devices:
        if normalized_device == _normalize_device_name(audio_device["name"]):
            return f":{audio_device['id']}"

    if normalized_device in {"built in microphone", "builtin microphone", "internal microphone"}:
        for audio_device in devices:
            normalized_name = _normalize_device_name(audio_device["name"])
            if "microphone" in normalized_name and (
                "built in" in normalized_name or "macbook" in normalized_name
            ):
                return f":{audio_device['id']}"

    raise DictateError(f"Audio input device not found: {device}")


def _list_avfoundation_devices() -> list[dict[str, str]]:
    try:
        result = subprocess.run(
            ["ffmpeg", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise DictateError("ffmpeg executable not found") from error

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    devices: list[dict[str, str]] = []
    in_audio_section = False

    for line in output.splitlines():
        if "AVFoundation video devices" in line:
            in_audio_section = False
            continue

        if "AVFoundation audio devices" in line:
            in_audio_section = True
            continue

        if not in_audio_section:
            continue

        match = re.search(r"\[(\d+)\]\s+(.+)$", line)
        if match:
            devices.append(
                {
                    "id": match.group(1),
                    "name": match.group(2).strip(),
                }
            )

    return devices


def _normalize_device_name(device_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", device_name.lower()).strip()


def build_record_command(
    output: Path,
    device: str | None,
    duration: float | None,
) -> list[str]:
    command = [
        "ffmpeg",
        "-y",
        "-f",
        _recording_format(),
        "-i",
        resolve_input_device(device),
        "-ac",
        str(DEFAULT_CHANNELS),
        "-ar",
        str(DEFAULT_SAMPLE_RATE),
    ]

    if duration is not None:
        command.extend(["-t", _format_duration(duration)])

    command.append(str(output))
    return command


def record_audio(
    output: Path,
    device: str | None,
    duration: float | None,
    verbose: bool,
) -> None:
    command = build_record_command(
        output=output,
        device=device,
        duration=duration,
    )

    if verbose:
        print(f"Running: {' '.join(command)}", file=sys.stderr)

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=None if verbose else subprocess.DEVNULL,
            stderr=None if verbose else subprocess.DEVNULL,
        )
    except FileNotFoundError as error:
        raise DictateError("ffmpeg executable not found") from error

    if duration is None:
        print(
            "\n🎤 Recording...",
            file=sys.stderr,
        )
        print(
            "Press ENTER to stop.\n",
            file=sys.stderr,
        )

        try:
            input()
        except EOFError as error:
            stop_audio_recording(process)
            raise DictateError(
                "stdin is not interactive. Use --duration for non-interactive use."
            ) from error
        except KeyboardInterrupt:
            pass

    stop_audio_recording(process)

    if verbose:
        print("Recording finished.", file=sys.stderr)


def stop_audio_recording(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    if process.stdin is not None:
        try:
            process.stdin.write(b"q")
            process.stdin.flush()
        except BrokenPipeError:
            process.terminate()
    else:
        process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _recording_format() -> str:
    system = platform.system().lower()

    if system == "darwin":
        return "avfoundation"

    if system == "windows":
        return "dshow"

    if system == "linux":
        return "pulse"

    raise DictateError(f"Unsupported platform: {platform.system()}")


# ---------------------------------------------------------
# Whisper
# ---------------------------------------------------------


def resolve_model_file(model: str) -> Path:
    model_path = Path(model).expanduser()

    if model_path.exists() or model_path.suffix or model_path.parent != Path("."):
        return model_path

    return DEFAULT_MODEL_DIR / f"ggml-{model}.bin"


def build_whisper_command(
    wav: Path,
    transcript_base: Path,
    model_file: Path,
    language: str,
) -> list[str]:
    command = [
        "whisper-cli",
        "-m",
        str(model_file),
        "-f",
        str(wav),
        "-of",
        str(transcript_base),
        "-otxt",
    ]

    if language != DEFAULT_LANGUAGE:
        command.extend(
            [
                "-l",
                language,
            ]
        )

    return command


def transcribe(
    wav: Path,
    language: str,
    model: str,
    verbose: bool,
) -> str:
    model_file = resolve_model_file(model)
    if not model_file.exists():
        raise DictateError(f"Model file does not exist: {model_file}")
    if not model_file.is_file():
        raise DictateError(f"Model path is not a file: {model_file}")

    with tempfile.TemporaryDirectory(prefix="dictate-") as temp_dir:
        transcript_base = Path(temp_dir) / "transcript"
        command = build_whisper_command(
            wav=wav,
            transcript_base=transcript_base,
            model_file=model_file,
            language=language,
        )

        if verbose:
            print(f"Running: {' '.join(command)}", file=sys.stderr)

        try:
            result = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=not verbose,
            )
        except FileNotFoundError as error:
            raise DictateError("whisper-cli executable not found") from error
        except subprocess.CalledProcessError as error:
            stderr = (error.stderr or "").strip()
            stdout = (error.stdout or "").strip()
            details = stderr or stdout
            if details:
                raise DictateError(
                    f"whisper-cli failed with exit code {error.returncode}: {details}"
                ) from error
            raise DictateError(
                f"whisper-cli failed with exit code {error.returncode}"
            ) from error

        if verbose and result.stderr:
            print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")

        transcript_file = transcript_base.with_suffix(".txt")
        if not transcript_file.exists():
            raise DictateError(
                "whisper-cli completed but did not create the transcript file: "
                f"{transcript_file}"
            )

        return transcript_file.read_text(encoding="utf-8").strip()


# ---------------------------------------------------------
# Output
# ---------------------------------------------------------


def write_output(
    text: str,
    path: str | None,
) -> None:
    if path:
        output_path = Path(path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        return

    print(text)


# ---------------------------------------------------------
# Utilities
# ---------------------------------------------------------


def _format_duration(duration: float) -> str:
    if float(duration).is_integer():
        return str(int(duration))

    return str(duration)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------


def main() -> int:
    args = parse_args()

    try:
        with tempfile.TemporaryDirectory(prefix="dictate-") as temp_dir:
            wav = Path(temp_dir) / "dictate.wav"

            record_audio(
                output=wav,
                device=args.device,
                duration=args.duration,
                verbose=args.verbose,
            )

            text = transcribe(
                wav=wav,
                language=args.language,
                model=args.model,
                verbose=args.verbose,
            )

            write_output(
                text=text,
                path=args.output,
            )

        return 0
    except KeyboardInterrupt:
        print("dictate: interrupted", file=sys.stderr)
        return 130
    except DictateError as error:
        print(f"dictate: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
