import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from voice_note.models.note import VoiceNote
from voice_note.models.settings import VoiceNoteSettings
from voice_note.output.writer import FileWriter
from voice_note.services.voice_note_service import VoiceNoteService, format_note


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


if __name__ == "__main__":
    unittest.main()
