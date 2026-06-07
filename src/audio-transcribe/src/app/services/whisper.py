import subprocess
from pathlib import Path


class WhisperWrapper:
    def run(
        self,
        audio_file: Path,
        output_file: Path,
        output_format: str,
        model_file: Path,
        language: str = "auto",
        verbose: bool = False,
    ) -> None:
        from src.app.services.transcriber import get_whisper_flag

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

        if verbose:
            print(f"Running: {' '.join(command)}")

        subprocess.run(command, check=True)
