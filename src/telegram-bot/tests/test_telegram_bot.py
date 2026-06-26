from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from telegram_bot.config import BotSettings
from telegram_bot.handlers.utils import split_text
from telegram_bot.models import AudioSource, TranscriptionResult
from telegram_bot.services.conversation import ConversationStore
from telegram_bot.services.voice_note import (
    TelegramVoiceNoteService,
    build_audio_source,
)


class FakeBot:
    def __init__(self) -> None:
        self.downloaded: list[tuple[str, Path]] = []

    async def get_file(self, file_id: str) -> SimpleNamespace:
        return SimpleNamespace(file_path=f"remote/{file_id}.ogg")

    async def download_file(self, file_path: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("audio")
        self.downloaded.append((file_path, destination))


class FakeTranscriber:
    def __init__(self) -> None:
        self.audio_files: list[Path] = []
        self.output_files: list[Path | None] = []

    def transcribe(self, audio_file: Path, output_file: Path | None = None) -> str:
        self.audio_files.append(audio_file)
        self.output_files.append(output_file)
        if output_file is not None:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("hello world")
        return "hello world"


class TelegramBotTests(unittest.TestCase):
    def test_conversation_store_tracks_voice_note_mode(self) -> None:
        store = ConversationStore()

        self.assertFalse(store.is_voice_note_active(1))
        store.start_voice_note(1)
        self.assertTrue(store.is_voice_note_active(1))
        self.assertTrue(store.consume_voice_note(1))
        self.assertFalse(store.is_voice_note_active(1))

    def test_split_text_chunks_long_messages(self) -> None:
        chunks = split_text("abcdef", 2)

        self.assertEqual(chunks, ["ab", "cd", "ef"])

    def test_build_audio_source_for_voice_message(self) -> None:
        message = SimpleNamespace(
            message_id=5,
            voice=SimpleNamespace(file_id="voice-file"),
            audio=None,
        )

        source = build_audio_source(message)

        self.assertEqual(
            source,
            AudioSource(
                kind="voice",
                file_id="voice-file",
                filename="voice_5.ogg",
                label="voice message",
            ),
        )

    def test_build_audio_source_for_audio_message(self) -> None:
        message = SimpleNamespace(
            message_id=9,
            voice=None,
            audio=SimpleNamespace(file_id="audio-file", file_name="clip.ogg", title="Clip"),
        )

        source = build_audio_source(message)

        self.assertEqual(
            source,
            AudioSource(
                kind="audio",
                file_id="audio-file",
                filename="clip.ogg",
                label="Clip",
            ),
        )

    def test_service_formats_transcript_message(self) -> None:
        service = TelegramVoiceNoteService(
            BotSettings(token="test-token"),
            transcription_service=FakeTranscriber(),
        )
        result = TranscriptionResult(
            source=AudioSource(
                kind="voice",
                file_id="file",
                filename="voice.ogg",
                label="voice message",
            ),
            local_file=Path("voice.ogg"),
            transcript="hello world",
            active_voice_note_session=True,
        )

        message = service.build_transcript_message(result)

        self.assertIn("Voice-note transcript", message)
        self.assertIn("hello world", message)

    def test_service_downloads_and_transcribes_audio(self) -> None:
        service = TelegramVoiceNoteService(
            BotSettings(token="test-token"),
            transcription_service=FakeTranscriber(),
        )
        bot = FakeBot()
        message = SimpleNamespace(
            message_id=12,
            chat=SimpleNamespace(id=99),
            voice=SimpleNamespace(file_id="voice-file"),
            audio=None,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            session_root = Path(temp_dir) / "logs" / "voice_notes"
            with patch(
                "telegram_bot.services.voice_note.DEFAULT_VOICE_NOTES_DIR",
                session_root,
            ), patch.object(service, "_convert_to_wav") as convert_mock:
                def fake_convert(input_file: Path, output_file: Path) -> None:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    output_file.write_text("wav")

                convert_mock.side_effect = fake_convert
                service.start_voice_note(99)
                result = asyncio.run(service.transcribe_message(bot, message))

            self.assertEqual(result.transcript, "hello world")
            self.assertEqual(result.source.filename, "voice_12.ogg")
            self.assertTrue(result.active_voice_note_session)
            self.assertEqual(len(bot.downloaded), 1)
            self.assertTrue(result.local_file.exists())
            self.assertTrue(result.local_file.parent.is_dir())
            self.assertTrue(str(result.local_file).startswith(str(session_root)))
            self.assertEqual(session_root.parent.name, "logs")
            self.assertEqual(result.local_file.suffix, ".wav")
            convert_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
