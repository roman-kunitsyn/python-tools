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
        log_file: Path | None = None,
        translate_to_english: bool = True,
    ) -> None:
        self.model = model
        self.language = language
        self.verbose = verbose
        self.log_file = log_file
        self.translate_to_english = translate_to_english

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

            if self.translate_to_english:
                command.append("-tr")

            try:
                self._run(command)
            except FileNotFoundError as error:
                raise FileNotFoundError("whisper-cli executable not found") from error

            transcript_file = output_base.with_suffix(".txt")
            return transcript_file.read_text().strip()

    def _run(self, command: list[str]) -> None:
        if self.log_file is None:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a") as log:
            log.write(f"$ {' '.join(command)}\n")
            log.flush()
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
            log.write("\n")


def resolve_model_file(model: str) -> Path:
    model_path = Path(model).expanduser()
    if model_path.suffix:
        return model_path

    return DEFAULT_MODEL_DIR / f"ggml-{model}.bin"
