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

    :r !dictate
"""

from __future__ import annotations

import argparse
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "0.1.0"


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------


def parse_args():

    parser = argparse.ArgumentParser(description="Voice dictation.")

    parser.add_argument(
        "--language",
        default="auto",
    )

    parser.add_argument(
        "--model",
        default="small",
    )

    parser.add_argument(
        "--output",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
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


def record_audio(
    output: Path,
    verbose: bool,
):

    command = [
        "ffmpeg",
        "-y",
        #
        # macOS
        #
        "-f",
        "avfoundation",
        #
        # default microphone
        #
        "-i",
        ":0",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output),
    ]

    if verbose:
        print("Recording...", file=sys.stderr)

    process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(
        "\n🎤 Recording...",
        file=sys.stderr,
    )

    print(
        "Press ENTER to stop.\n",
        file=sys.stderr,
    )

    input()

    process.send_signal(signal.SIGINT)

    process.wait()

    if verbose:
        print("Recording finished.", file=sys.stderr)


# ---------------------------------------------------------
# Whisper
# ---------------------------------------------------------


def transcribe(
    wav: Path,
    language: str,
    model: str,
    verbose: bool,
) -> str:

    command = [
        "whisper-cli",
        "--model",
        model,
        "--file",
        str(wav),
    ]

    if language != "auto":
        command.extend(
            [
                "--language",
                language,
            ]
        )

    if verbose:
        print(
            "Running Whisper...",
            file=sys.stderr,
        )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


# ---------------------------------------------------------
# Output
# ---------------------------------------------------------


def write_output(
    text: str,
    path: str | None,
):

    if path:
        Path(path).write_text(
            text,
            encoding="utf-8",
        )

        return

    print(text)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------


def main():

    args = parse_args()

    with tempfile.NamedTemporaryFile(
        suffix=".wav",
        delete=True,
    ) as tmp:
        wav = Path(tmp.name)

        record_audio(
            wav,
            args.verbose,
        )

        text = transcribe(
            wav,
            args.language,
            args.model,
            args.verbose,
        )

        write_output(
            text,
            args.output,
        )


if __name__ == "__main__":
    main()
