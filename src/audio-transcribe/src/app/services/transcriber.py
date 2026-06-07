from pathlib import Path

from src.app.models.config import TranscribeConfig
from src.app.services.whisper import WhisperWrapper


FORMAT_TO_FLAG = {
    "txt": "-otxt",
    "json": "-oj",
    "srt": "-osrt",
}

SUPPORTED_FORMATS = set(FORMAT_TO_FLAG)


def validate_output_format(output_format: str) -> None:
    if output_format not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(
            f"Unsupported output format: {output_format}. Supported formats: {supported}"
        )


def validate_audio_file(audio_file: Path | None) -> Path:
    if audio_file is None:
        raise ValueError("Audio file is required")
    if not audio_file.exists():
        raise ValueError(f"Audio file does not exist: {audio_file}")
    if not audio_file.is_file():
        raise ValueError(f"Audio path is not a file: {audio_file}")
    return audio_file


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


def get_whisper_flag(output_format: str) -> str:
    validate_output_format(output_format)
    return FORMAT_TO_FLAG[output_format]


class TranscribeService:
    def __init__(
        self,
        whisper: WhisperWrapper | None = None,
        verbose: bool = False,
    ) -> None:
        self.whisper = whisper or WhisperWrapper()
        self.verbose = verbose

    def transcribe(self, config: TranscribeConfig) -> Path:
        validate_output_format(config.output_format)
        audio_file = validate_audio_file(config.audio_file)
        validate_model_file(config.model_file)
        transcript_file = build_output_file(
            audio_file=audio_file,
            output_file=config.output_file,
            output_format=config.output_format,
        )

        self.whisper.run(
            audio_file=audio_file,
            output_file=transcript_file,
            output_format=config.output_format,
            model_file=config.model_file,
            language=config.language,
            verbose=self.verbose,
        )

        return transcript_file
