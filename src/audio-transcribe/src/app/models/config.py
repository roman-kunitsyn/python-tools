from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL = Path.home() / "whisper" / "models" / "ggml-small.bin"


@dataclass
class TranscribeConfig:
    audio_file: Path | None
    output_file: Path | None
    output_format: str
    model_file: Path
    language: str = "auto"
