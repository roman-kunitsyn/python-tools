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
import io
from contextlib import nullcontext
from datetime import datetime
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import ContextManager

VERSION = "0.1.0"
DEFAULT_LANGUAGE = "auto"
DEFAULT_MODEL = "small"
DEFAULT_MODEL_DIR = Path.home() / "whisper" / "models"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHANNELS = 1
LOG_ROOT = Path.cwd() / "logs" / "dictate"


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
    devices = _list_avfoundation_devices()

    if device is None:
        return _default_avfoundation_input(devices)

    if device.isdigit():
        return f":{device}"

    if device.startswith(":"):
        return device

    for audio_device in devices:
        if device == audio_device["name"]:
            return f":{audio_device['id']}"

    normalized_device = _normalize_device_name(device)
    for audio_device in devices:
        if normalized_device == _normalize_device_name(audio_device["name"]):
            return f":{audio_device['id']}"

    if normalized_device in {
        "built in microphone",
        "builtin microphone",
        "internal microphone",
        "macbook pro microphone",
    }:
        for audio_device in devices:
            normalized_name = _normalize_device_name(audio_device["name"])
            if "microphone" in normalized_name and (
                "built in" in normalized_name or "macbook" in normalized_name
            ):
                return f":{audio_device['id']}"

    raise DictateError(f"Audio input device not found: {device}")


def _default_avfoundation_input(devices: list[dict[str, str]]) -> str:
    if not devices:
        return ":0"

    preferred = _pick_preferred_device(devices)
    if preferred is not None:
        return f":{preferred['id']}"

    return f":{devices[0]['id']}"


def _pick_preferred_device(devices: list[dict[str, str]]) -> dict[str, str] | None:
    for audio_device in devices:
        normalized_name = _normalize_device_name(audio_device["name"])
        if _looks_like_microphone(normalized_name):
            return audio_device

    for audio_device in devices:
        normalized_name = _normalize_device_name(audio_device["name"])
        if _looks_like_input_device(normalized_name):
            return audio_device

    return None


def _looks_like_microphone(normalized_name: str) -> bool:
    if "blackhole" in normalized_name:
        return False
    if "obs" in normalized_name:
        return False
    if "aggregate" in normalized_name:
        return False
    return "microphone" in normalized_name or "mic" in normalized_name


def _looks_like_input_device(normalized_name: str) -> bool:
    if "blackhole" in normalized_name:
        return False
    if "obs" in normalized_name:
        return False
    if "aggregate" in normalized_name:
        return False
    return True


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
    log_file: Path | None,
) -> None:
    command = build_record_command(
        output=output,
        device=device,
        duration=duration,
    )

    if verbose:
        print(f"Running: {' '.join(command)}", file=sys.stderr)

    try:
        with _open_log_file(log_file) as log:
            _write_command_log(log, command)
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=log
                if log is not None
                else (None if verbose else subprocess.DEVNULL),
                stderr=log
                if log is not None
                else (None if verbose else subprocess.DEVNULL),
            )

            if duration is None:
                try:
                    wait_for_stop_signal()
                except DictateError:
                    stop_audio_recording(process)
                    raise
                except KeyboardInterrupt:
                    pass

            stop_audio_recording(process)
    except FileNotFoundError as error:
        raise DictateError("ffmpeg executable not found") from error

    if verbose:
        print("Recording finished.", file=sys.stderr)


def wait_for_stop_signal() -> None:
    print(
        "\n🎤 Recording...",
        file=sys.stderr,
    )
    print(
        "Press ENTER to stop.\n",
        file=sys.stderr,
    )

    with _open_stop_input_stream() as stop_input:
        stop_input.readline()


def _open_stop_input_stream() -> ContextManager[io.TextIOBase]:
    if sys.stdin.isatty():
        return nullcontext(sys.stdin)

    try:
        return open("/dev/tty", encoding="utf-8")
    except OSError as error:
        raise DictateError(
            "No controlling terminal available. Use --duration for non-interactive use."
        ) from error


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
    log_file: Path | None,
    transcript_file: Path,
) -> str:
    model_file = resolve_model_file(model)
    if not model_file.exists():
        raise DictateError(f"Model file does not exist: {model_file}")
    if not model_file.is_file():
        raise DictateError(f"Model path is not a file: {model_file}")

    transcript_base = transcript_file.with_suffix("")
    command = build_whisper_command(
        wav=wav,
        transcript_base=transcript_base,
        model_file=model_file,
        language=language,
    )

    if verbose:
        print(f"Running: {' '.join(command)}", file=sys.stderr)

    try:
        with _open_log_file(log_file) as log:
            _write_command_log(log, command)
            result = subprocess.run(
                command,
                check=True,
                text=True,
                capture_output=log is None and not verbose,
                stdout=log if log is not None else None,
                stderr=log if log is not None else None,
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
        print(
            result.stderr,
            file=sys.stderr,
            end="" if result.stderr.endswith("\n") else "\n",
        )

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


def create_session_files() -> tuple[Path, Path, Path, Path]:
    timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
    session_dir = LOG_ROOT / f"dictate-{timestamp}"
    audio_dir = session_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    audio_file = audio_dir / f"audio_{timestamp}.wav"
    transcript_file = session_dir / "transcribe.txt"
    log_file = session_dir / "log.txt"
    log_file.touch(exist_ok=True)
    return session_dir, audio_file, transcript_file, log_file


def _open_log_file(log_file: Path | None) -> ContextManager[io.TextIOBase | None]:
    if log_file is None:
        return nullcontext(None)

    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file.open("a", encoding="utf-8")


def _write_command_log(log: io.TextIOBase | None, command: list[str]) -> None:
    if log is None:
        return

    log.write(f"$ {' '.join(command)}\n")
    log.flush()


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
        session_dir, audio_file, transcript_file, log_file = create_session_files()
        if args.verbose:
            print(f"Log file: {log_file}", file=sys.stderr)

        record_audio(
            output=audio_file,
            device=args.device,
            duration=args.duration,
            verbose=args.verbose,
            log_file=log_file,
        )

        text = transcribe(
            wav=audio_file,
            language=args.language,
            model=args.model,
            verbose=args.verbose,
            log_file=log_file,
            transcript_file=transcript_file,
        )

        write_output(
            text=text,
            path=args.output,
        )

        if args.verbose:
            print(f"Session dir: {session_dir}", file=sys.stderr)

        return 0
    except KeyboardInterrupt:
        print("dictate: interrupted", file=sys.stderr)
        return 130
    except DictateError as error:
        print(f"dictate: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
