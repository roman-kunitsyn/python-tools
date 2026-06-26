from __future__ import annotations

import asyncio
import json
import wave
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from aiogram.fsm.storage.memory import MemoryStorage

from telegram_bot.bot import build_dispatcher
from telegram_bot.config import BotSettings
from telegram_bot.handlers.utils import split_text
from telegram_bot.models import AudioSource
from telegram_bot.services.conversation import ConversationStore
from telegram_bot.services.voice_note import TelegramVoiceNoteService, build_audio_source


class FakeBot:
    def __init__(self) -> None:
        self.downloaded: list[tuple[str, Path]] = []

    async def get_file(self, file_id: str) -> SimpleNamespace:
        return SimpleNamespace(file_path=f"remote/{file_id}.ogg")

    async def download_file(self, file_path: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(f"downloaded:{file_path}")
        self.downloaded.append((file_path, destination))


class FakeTranscriber:
    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path | None]] = []

    async def transcribe(self, audio_file: Path, output_file: Path | None = None) -> str:
        self.calls.append((audio_file, output_file))
        transcript = f"transcript:{audio_file.stem}"
        if output_file is not None:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(transcript)
        return transcript


def build_message(
    *,
    message_id: int,
    chat_id: int,
    user_id: int,
    voice_file_id: str | None = None,
    audio_file_id: str | None = None,
    audio_file_name: str | None = None,
    audio_title: str | None = None,
) -> SimpleNamespace:
    voice = SimpleNamespace(file_id=voice_file_id) if voice_file_id else None
    audio = (
        SimpleNamespace(
            file_id=audio_file_id,
            file_name=audio_file_name,
            title=audio_title,
        )
        if audio_file_id
        else None
    )
    return SimpleNamespace(
        message_id=message_id,
        chat=SimpleNamespace(id=chat_id),
        from_user=SimpleNamespace(id=user_id),
        voice=voice,
        audio=audio,
    )


async def fake_convert_to_wav(input_file: Path) -> Path:
    output_file = input_file.with_suffix(".wav")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_file), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(8000)
        wav_file.writeframes(b"\x00\x00" * 800)
    return output_file


class TelegramBotTests(unittest.IsolatedAsyncioTestCase):
    def test_conversation_store_tracks_voice_note_sessions(self) -> None:
        store = ConversationStore()
        session = SimpleNamespace(chat_id=1)

        self.assertFalse(store.is_voice_note_active(1))
        store.start_voice_note(session)  # type: ignore[arg-type]
        self.assertTrue(store.is_voice_note_active(1))
        self.assertIs(store.get(1), session)
        self.assertIs(store.remove(1), session)
        self.assertFalse(store.is_voice_note_active(1))

    def test_split_text_chunks_long_messages(self) -> None:
        self.assertEqual(split_text("abcdef", 2), ["ab", "cd", "ef"])

    def test_build_audio_source_for_voice_message(self) -> None:
        message = build_message(
            message_id=5,
            chat_id=1,
            user_id=2,
            voice_file_id="voice-file",
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
        message = build_message(
            message_id=9,
            chat_id=1,
            user_id=2,
            audio_file_id="audio-file",
            audio_file_name="clip.ogg",
            audio_title="Clip",
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

    def test_dispatcher_uses_memory_storage(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = BotSettings(
                token="test-token",
                voice_notes_dir=Path(temp_dir) / "voice_notes",
            )
            dispatcher = build_dispatcher(TelegramVoiceNoteService(settings))

        self.assertIsInstance(dispatcher.fsm.storage, MemoryStorage)

    async def test_service_processes_multiple_voice_notes_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = BotSettings(
                token="test-token",
                voice_notes_dir=Path(temp_dir) / "voice_notes",
            )
            transcriber = FakeTranscriber()
            service = TelegramVoiceNoteService(
                settings,
                transcription_service=transcriber,
            )
            bot = FakeBot()

            await service.start_session(
                build_message(
                    message_id=1,
                    chat_id=99,
                    user_id=42,
                )
            )

            with unittest.mock.patch.object(
                service.storage_service,
                "convert_to_wav",
                side_effect=fake_convert_to_wav,
            ):
                first = await service.process_voice_message(
                    bot,
                    build_message(
                        message_id=2,
                        chat_id=99,
                        user_id=42,
                        voice_file_id="voice-1",
                    ),
                )
                second = await service.process_voice_message(
                    bot,
                    build_message(
                        message_id=3,
                        chat_id=99,
                        user_id=42,
                        voice_file_id="voice-2",
                    ),
                )

            session = service.get_active_session(99)
            self.assertIsNotNone(session)
            assert session is not None
            self.assertEqual(len(session.entries), 2)
            self.assertEqual(first.entry.index, 1)
            self.assertEqual(second.entry.index, 2)
            self.assertEqual(first.entry.source_file.name, "voice_001.ogg")
            self.assertEqual(second.entry.source_file.name, "voice_002.ogg")
            self.assertEqual(len(bot.downloaded), 2)
            self.assertTrue(first.entry.wav_file.exists())
            self.assertTrue(second.entry.wav_file.exists())
            self.assertEqual(first.reply_text, "transcript:voice_001")
            self.assertEqual(second.reply_text, "transcript:voice_002")

            transcript = session.transcript_file.read_text()
            self.assertIn("Voice #1", transcript)
            self.assertIn("Voice #2", transcript)
            self.assertLess(transcript.index("transcript:voice_001"), transcript.index("transcript:voice_002"))

            metadata = json.loads(session.metadata_file.read_text())
            self.assertEqual(metadata["session_id"], session.session_id)
            self.assertEqual(len(metadata["voices"]), 2)
            self.assertEqual(metadata["voices"][0]["file"], "voice_001.ogg")
            self.assertEqual(metadata["voices"][1]["file"], "voice_002.ogg")

    async def test_finish_session_keeps_local_artifacts_and_returns_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = BotSettings(
                token="test-token",
                voice_notes_dir=Path(temp_dir) / "voice_notes",
            )
            service = TelegramVoiceNoteService(
                settings,
                transcription_service=FakeTranscriber(),
            )
            bot = FakeBot()

            await service.start_session(build_message(message_id=1, chat_id=7, user_id=3))
            with unittest.mock.patch.object(
                service.storage_service,
                "convert_to_wav",
                side_effect=fake_convert_to_wav,
            ):
                await service.process_voice_message(
                    bot,
                    build_message(
                        message_id=2,
                        chat_id=7,
                        user_id=3,
                        voice_file_id="voice-1",
                    ),
                )
                await service.process_voice_message(
                    bot,
                    build_message(
                        message_id=3,
                        chat_id=7,
                        user_id=3,
                        voice_file_id="voice-2",
                    ),
                )

            result = await service.finish_session(7)

            self.assertEqual(result.voice_count, 2)
            self.assertEqual(
                result.transcript_text,
                "transcript:voice_001\n\ntranscript:voice_002",
            )
            self.assertEqual(service.get_active_session(7), None)
            self.assertTrue(result.transcript_file.exists())
            self.assertTrue(result.session.session_dir.exists())

            metadata = json.loads(result.session.metadata_file.read_text())
            self.assertIsNotNone(metadata["completed_at"])
            self.assertEqual(len(metadata["voices"]), 2)

    async def test_cancel_session_removes_session_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = BotSettings(
                token="test-token",
                voice_notes_dir=Path(temp_dir) / "voice_notes",
            )
            service = TelegramVoiceNoteService(
                settings,
                transcription_service=FakeTranscriber(),
            )
            bot = FakeBot()

            await service.start_session(build_message(message_id=1, chat_id=11, user_id=4))
            with unittest.mock.patch.object(
                service.storage_service,
                "convert_to_wav",
                side_effect=fake_convert_to_wav,
            ):
                await service.process_voice_message(
                    bot,
                    build_message(
                        message_id=2,
                        chat_id=11,
                        user_id=4,
                        voice_file_id="voice-1",
                    ),
                )

            session = service.get_active_session(11)
            assert session is not None
            session_dir = session.session_dir

            await service.cancel_session(11)

            self.assertFalse(session_dir.exists())
            self.assertIsNone(service.get_active_session(11))


if __name__ == "__main__":
    unittest.main()
