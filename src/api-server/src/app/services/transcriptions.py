from __future__ import annotations

import subprocess
from pathlib import Path

from app.bootstrap import ensure_workspace_paths

ensure_workspace_paths()


FORMAT_TO_FLAG = {
    "txt": "-otxt",
    "json": "-oj",
    "srt": "-osrt",
}

SUPPORTED_FORMATS = set(FORMAT_TO_FLAG)


class TranscriptionService:
    def transcribe(
        self,
        *,
        audio_file: Path,
        output_file: Path | None,
        output_format: str,
        model_file: Path,
        language: str,
        verbose: bool,
    ) -> Path:
        self._validate_output_format(output_format)
        self._validate_audio_file(audio_file)
        self._validate_model_file(model_file)

        transcript_file = self._build_output_file(audio_file, output_file, output_format)
        command = [
            "whisper-cli",
            "-m",
            str(model_file),
            "-f",
            str(audio_file),
            "-of",
            str(transcript_file.with_suffix("")),
            FORMAT_TO_FLAG[output_format],
        ]

        if language != "auto":
            command.extend(["-l", language])

        if verbose:
            print(f"Running: {' '.join(command)}")

        subprocess.run(command, check=True)
        return transcript_file

    def _validate_output_format(self, output_format: str) -> None:
        if output_format not in SUPPORTED_FORMATS:
            supported = ", ".join(sorted(SUPPORTED_FORMATS))
            raise ValueError(
                f"Unsupported output format: {output_format}. Supported formats: {supported}"
            )

    def _validate_audio_file(self, audio_file: Path) -> None:
        if not audio_file.exists():
            raise ValueError(f"Audio file does not exist: {audio_file}")
        if not audio_file.is_file():
            raise ValueError(f"Audio path is not a file: {audio_file}")

    def _validate_model_file(self, model_file: Path) -> None:
        if not model_file.exists():
            raise ValueError(f"Model file does not exist: {model_file}")
        if not model_file.is_file():
            raise ValueError(f"Model path is not a file: {model_file}")

    def _build_output_file(
        self,
        audio_file: Path,
        output_file: Path | None,
        output_format: str,
    ) -> Path:
        suffix = f".{output_format}"
        if output_file is None:
            return audio_file.with_suffix(suffix)
        return output_file.with_suffix(suffix)
