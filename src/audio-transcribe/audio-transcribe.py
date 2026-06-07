import argparse
import subprocess
import sys
from pathlib import Path


DEFAULT_MODEL = Path.home() / "whisper" / "models" / "ggml-small.bin"

FORMAT_TO_FLAG = {
    "txt": "-otxt",
    "json": "-oj",
    "srt": "-osrt",
}

SUPPORTED_FORMATS = set(FORMAT_TO_FLAG)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transcribe an audio file with whisper-cli."
    )
    parser.add_argument(
        "--audio-file",
        required=True,
        type=Path,
        help="Path to the source audio file.",
    )
    parser.add_argument(
        "--format",
        default="txt",
        help=f"Transcription output format. Supported: {', '.join(sorted(SUPPORTED_FORMATS))}.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        help="Output file path. The selected format extension is applied automatically.",
    )
    parser.add_argument(
        "--model-file",
        type=Path,
        default=DEFAULT_MODEL,
        help=f"Path to the Whisper model file. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Language passed to whisper-cli. Use 'auto' for auto-detection.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print command details before running whisper-cli.",
    )
    return parser


def log(message: str, verbose: bool) -> None:
    if verbose:
        print(message)


def validate_audio_file(audio_file: Path) -> None:
    if not audio_file.exists():
        raise ValueError(f"Audio file does not exist: {audio_file}")
    if not audio_file.is_file():
        raise ValueError(f"Audio path is not a file: {audio_file}")


def validate_model_file(model_file: Path) -> None:
    if not model_file.exists():
        raise ValueError(f"Model file does not exist: {model_file}")
    if not model_file.is_file():
        raise ValueError(f"Model path is not a file: {model_file}")


def build_output_file(
    audio_file: Path,
    output_file: Path | None,
    output_format: str,
) -> Path:
    validate_output_format(output_format)
    suffix = f".{output_format}"

    if output_file is None:
        return audio_file.with_suffix(suffix)

    return output_file.with_suffix(suffix)


def validate_output_format(output_format: str) -> None:
    if output_format not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(
            f"Unsupported output format: {output_format}. Supported formats: {supported}"
        )


def get_whisper_flag(output_format: str) -> str:
    validate_output_format(output_format)
    return FORMAT_TO_FLAG[output_format]


def run_whisper(
    audio_file: Path,
    output_file: Path,
    output_format: str,
    model_file: Path,
    language: str = "auto",
    verbose: bool = False,
) -> None:
    whisper_flag = get_whisper_flag(output_format)
    command = [
        "whisper-cli",
        "-m",
        str(model_file),
        "-f",
        str(audio_file),
        "-of",
        str(output_file.with_suffix("")),
        whisper_flag,
    ]

    if language != "auto":
        command.extend(["-l", language])

    log(f"Running: {' '.join(command)}", verbose)
    subprocess.run(command, check=True)


def transcribe_audio(
    audio_file: Path,
    output_format: str = "txt",
    output_file: Path | None = None,
    model_file: Path = DEFAULT_MODEL,
    language: str = "auto",
    verbose: bool = False,
) -> Path:
    validate_output_format(output_format)
    validate_audio_file(audio_file)
    validate_model_file(model_file)
    transcript_file = build_output_file(audio_file, output_file, output_format)

    run_whisper(
        audio_file=audio_file,
        output_file=transcript_file,
        output_format=output_format,
        model_file=model_file,
        language=language,
        verbose=verbose,
    )

    return transcript_file


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        transcript_file = transcribe_audio(
            audio_file=args.audio_file,
            output_format=args.format,
            output_file=args.output_file,
            model_file=args.model_file,
            language=args.language,
            verbose=args.verbose,
        )
    except ValueError as error:
        print(f"Validation error: {error}", file=sys.stderr)
        return 1
    except FileNotFoundError as error:
        print(f"Whisper failed: {error}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as error:
        print(f"Whisper failed with exit code {error.returncode}.", file=sys.stderr)
        return 2

    log(f"Transcription written to: {transcript_file}", args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
