import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from voice_note.models.note import VoiceNote
from voice_note.models.settings import VoiceNoteSettings
from voice_note.output.writer import FileWriter
from voice_note.services.voice_note_service import VoiceNoteService, format_note
from voice_note.audio.recorder import PushToTalkRecorder


class FakeRecorder:
    def __init__(self) -> None:
        self.audio_file = Path("note.wav")
        self.cleaned: list[Path] = []

    def start(self) -> Path:
        return self.audio_file

    def stop(self) -> Path:
        return self.audio_file

    def cleanup(self, audio_file: Path) -> None:
        self.cleaned.append(audio_file)


class FakeTranscriber:
    def transcribe(self, audio_file: Path) -> str:
        return " hello world "


class MemoryWriter:
    def __init__(self) -> None:
        self.values: list[str] = []

    def write(self, text: str) -> None:
        self.values.append(text)


class VoiceNoteServiceTest(unittest.TestCase):
    def test_stop_records_transcribes_writes_and_cleans_up(self) -> None:
        recorder = FakeRecorder()
        writer = MemoryWriter()
        service = VoiceNoteService(
            recorder=recorder,
            transcriber=FakeTranscriber(),
            writer=writer,
        )

        audio_file = service.start_recording()
        note = service.stop_recording_and_transcribe()

        self.assertEqual(audio_file, Path("note.wav"))
        self.assertEqual(note.text, "hello world")
        self.assertEqual(writer.values, ["hello world"])
        self.assertEqual(recorder.cleaned, [Path("note.wav")])

    def test_format_note_with_timestamp(self) -> None:
        note = VoiceNote(
            text="Need to investigate RLS.",
            created_at=datetime(2026, 6, 23, 14, 35, 10),
            audio_file=Path("note.wav"),
        )

        self.assertEqual(
            format_note(note, append_timestamp=True),
            "[2026-06-23 14:35:10]\n\nNeed to investigate RLS.\n",
        )


class SettingsTest(unittest.TestCase):
    def test_default_storage_paths_use_voice_note_session_folder(self) -> None:
        settings = VoiceNoteSettings().with_default_storage(
            timestamp="2026_06_23-14_35_10",
            base_dir=Path("logs") / "voice_notes",
        )

        self.assertEqual(
            settings.session_dir,
            Path("logs") / "voice_notes" / "voice_note_2026_06_23-14_35_10",
        )
        self.assertEqual(
            settings.audio_output_folder,
            settings.session_dir / "audio",
        )
        self.assertEqual(
            settings.audio_file,
            settings.session_dir / "audio" / "audio_2026_06_23-14_35_10.wav",
        )
        self.assertEqual(settings.text_output_file, settings.session_dir / "transcribe.txt")
        self.assertTrue(settings.keep_audio)

    def test_loads_json_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text(
                '{"mode":"tui","language":"en","model":"small",'
                '"append_timestamp":true,"keep_audio":true,'
                '"audio_output_folder":"./audio","text_output_file":"./notes.md"}'
            )

            settings = VoiceNoteSettings.from_file(config_file)

        self.assertEqual(settings.mode, "tui")
        self.assertEqual(settings.language, "en")
        self.assertEqual(settings.model, "small")
        self.assertTrue(settings.append_timestamp)
        self.assertTrue(settings.keep_audio)
        self.assertEqual(settings.audio_output_folder, Path("./audio"))
        self.assertEqual(settings.text_output_file, Path("./notes.md"))


class FileWriterTest(unittest.TestCase):
    def test_appends_text_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "notes.md"
            writer = FileWriter(output_file)

            writer.write("first")
            writer.write("second\n")

            self.assertEqual(output_file.read_text(), "first\nsecond\n")


class PushToTalkRecorderTest(unittest.TestCase):
    def test_build_output_file_uses_explicit_audio_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file = Path(temp_dir) / "voice_note" / "audio" / "audio.wav"
            recorder = PushToTalkRecorder(audio_file=audio_file, keep_audio=True)

            self.assertEqual(recorder._build_output_file(), audio_file)
            self.assertTrue(audio_file.parent.exists())


if __name__ == "__main__":
    unittest.main()
