from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL_DIR = Path.home() / "whisper" / "models"
DEFAULT_MODEL = DEFAULT_MODEL_DIR / "ggml-small.bin"


@dataclass
class TranscribeConfig:
    audio_file: Path | None
    output_file: Path | None
    output_format: str
    model_file: Path
    language: str = "auto"
