from __future__ import annotations

from pathlib import Path

from telegram_bot.bootstrap import ensure_voice_note_path

ensure_voice_note_path()

from voice_note.transcription.whisper_transcriber import WhisperTranscriber


class WhisperTranscriptionService:
    def __init__(
        self,
        model: str = "small",
        language: str = "auto",
        verbose: bool = False,
        log_file: Path | None = None,
    ) -> None:
        self.transcriber = WhisperTranscriber(
            model=model,
            language=language,
            verbose=verbose,
            log_file=log_file,
        )

    def transcribe(self, audio_file: Path) -> str:
        return self.transcriber.transcribe(audio_file).strip()
