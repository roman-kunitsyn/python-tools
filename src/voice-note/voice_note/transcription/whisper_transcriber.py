import subprocess
import tempfile
from pathlib import Path


DEFAULT_MODEL_DIR = Path.home() / "whisper" / "models"


class WhisperTranscriber:
    def __init__(
        self,
        model: str = "base",
        language: str = "auto",
        verbose: bool = False,
    ) -> None:
        self.model = model
        self.language = language
        self.verbose = verbose

    def transcribe(self, audio_file: Path) -> str:
        model_file = resolve_model_file(self.model)
        if not model_file.exists():
            raise ValueError(f"Model file does not exist: {model_file}")

        with tempfile.TemporaryDirectory(prefix="voice-note-") as temp_dir:
            output_base = Path(temp_dir) / "transcript"
            command = [
                "whisper-cli",
                "-m",
                str(model_file),
                "-f",
                str(audio_file),
                "-of",
                str(output_base),
                "-otxt",
            ]

            if self.language != "auto":
                command.extend(["-l", self.language])

            if self.verbose:
                print(f"Running: {' '.join(command)}")

            try:
                subprocess.run(command, check=True)
            except FileNotFoundError as error:
                raise FileNotFoundError("whisper-cli executable not found") from error

            transcript_file = output_base.with_suffix(".txt")
            return transcript_file.read_text().strip()


def resolve_model_file(model: str) -> Path:
    model_path = Path(model).expanduser()
    if model_path.suffix:
        return model_path

    return DEFAULT_MODEL_DIR / f"ggml-{model}.bin"
