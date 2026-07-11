#!/usr/bin/env python3

"""
rewrite.py

Generic text transformation CLI.

Supports:
    --input
    --output
    --format text|json
    --verbose
    --model
    --version

Can read from:
    --input
    stdin

Can write to:
    stdout
    file

Designed for editor integration.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

VERSION = "0.1.0"


# ---------------------------------------------------------
# CLI
# ---------------------------------------------------------


def parse_args():
    parser = argparse.ArgumentParser(description="Rewrite text using an LLM.")

    parser.add_argument(
        "--input",
        help="Input text. If omitted, stdin is used.",
    )

    parser.add_argument(
        "--output",
        help="Write result to file.",
    )

    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
    )

    parser.add_argument(
        "--model",
        default="qwen2.5:3b",
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
# IO
# ---------------------------------------------------------


def read_input(args) -> str:
    if args.input:
        return args.input

    if not sys.stdin.isatty():
        return sys.stdin.read()

    print("Enter text. Finish with Ctrl+D:\n")

    return sys.stdin.read()


def write_output(text: str, args):

    if args.output:
        Path(args.output).write_text(
            text,
            encoding="utf-8",
        )
        return

    print(text, end="")


# ---------------------------------------------------------
# Prompt
# ---------------------------------------------------------


SYSTEM_PROMPT = """
You are an expert editor.

Rewrite the text.

Requirements:

- Fix grammar.
- Improve clarity.
- Keep original meaning.
- Use professional tone.
- Do not add explanations.
- Return only rewritten text.
"""


def build_prompt(text: str) -> str:
    return f"""{SYSTEM_PROMPT}

Text:

{text}
"""


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------


def call_ollama(prompt: str, model: str) -> str:

    result = subprocess.run(
        [
            "ollama",
            "run",
            model,
        ],
        input=prompt,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


# ---------------------------------------------------------
# Formatting
# ---------------------------------------------------------


def format_output(text: str, fmt: str):

    if fmt == "text":
        return text

    return json.dumps(
        {
            "text": text,
        },
        ensure_ascii=False,
        indent=2,
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------


def main():

    args = parse_args()

    source = read_input(args)

    prompt = build_prompt(source)

    if args.verbose:
        print(
            f"Model: {args.model}",
            file=sys.stderr,
        )

    result = call_ollama(
        prompt,
        args.model,
    )

    output = format_output(
        result,
        args.format,
    )

    write_output(
        output,
        args,
    )


if __name__ == "__main__":
    main()
