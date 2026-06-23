import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from voice_note.models.note import VoiceNote
from voice_note.models.settings import VoiceNoteSettings
from voice_note.output.writer import FileWriter
from voice_note.services.voice_note_service import VoiceNoteService, format_note
from voice_note.audio.recorder import PushToTalkRecorder
from voice_note.tui.app import (
    _format_status,
    _normalize_editor,
    _session_name,
    _status_class,
    _transcript_link,
    _transcript_url,
    _vscode_url,
)


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

    def test_output_file_returns_writer_output_file(self) -> None:
        writer = FileWriter(
            Path("logs")
            / "voice_notes"
            / "voice_note_2026_06_23-22_15_00"
            / "transcribe.txt"
        )
        service = VoiceNoteService(
            recorder=FakeRecorder(),
            transcriber=FakeTranscriber(),
            writer=writer,
        )

        self.assertEqual(service.output_file, writer.output_file)

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
            None,
        )
        self.assertEqual(settings.text_output_file, settings.session_dir / "transcribe.txt")
        self.assertEqual(settings.log_file, settings.session_dir / "log.txt")
        self.assertEqual(settings.audio_device, "built-in microphone")
        self.assertEqual(settings.editor, "code")
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
        self.assertEqual(settings.audio_device, "built-in microphone")
        self.assertEqual(settings.editor, "code")


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

    def test_recorder_keeps_audio_device_setting(self) -> None:
        recorder = PushToTalkRecorder(audio_device="built-in microphone")

        self.assertEqual(recorder.audio_device, "built-in microphone")

    def test_build_output_file_creates_timestamped_audio_files(self) -> None:
        timestamps = iter(("2026_06_23-20_59_14", "2026_06_23-21_00_01"))

        with tempfile.TemporaryDirectory() as temp_dir:
            audio_dir = Path(temp_dir) / "voice_note" / "audio"
            recorder = PushToTalkRecorder(
                audio_output_folder=audio_dir,
                keep_audio=True,
                timestamp_provider=lambda: next(timestamps),
            )

            self.assertEqual(
                recorder._build_output_file(),
                audio_dir / "audio_2026_06_23-20_59_14.wav",
            )
            self.assertEqual(
                recorder._build_output_file(),
                audio_dir / "audio_2026_06_23-21_00_01.wav",
            )


class TuiStatusTest(unittest.TestCase):
    def test_status_format_and_classes(self) -> None:
        self.assertEqual(_format_status("Idle"), "Status: Idle")
        self.assertEqual(_format_status("Status: Error"), "Status: Error")
        self.assertEqual(_status_class("Status: Idle"), "status-idle")
        self.assertEqual(_status_class("Status: Recording..."), "status-recording")
        self.assertEqual(_status_class("Status: Transcribing..."), "status-transcribing")
        self.assertEqual(_status_class("Status: Saved"), "status-saved")
        self.assertEqual(_status_class("Status: Error"), "status-error")

    def test_session_name_and_transcript_link(self) -> None:
        transcript_file = (
            Path("logs")
            / "voice_notes"
            / "voice_note_2026_06_23-22_15_00"
            / "transcribe.txt"
        )

        self.assertEqual(_session_name(transcript_file), "voice_note_2026_06_23-22_15_00")
        self.assertEqual(_transcript_link(transcript_file), f"Transcript: {transcript_file}")
        self.assertEqual(_transcript_url(transcript_file, "code"), _vscode_url(transcript_file))
        self.assertEqual(_transcript_url(transcript_file, "nvim"), transcript_file.resolve().as_uri())
        self.assertEqual(_session_name(None), "Voice Note Session")
        self.assertEqual(_transcript_link(None), "Transcript: stdout")
        self.assertIsNone(_transcript_url(None))

    def test_editor_normalization(self) -> None:
        self.assertEqual(_normalize_editor("vscode"), "code")
        self.assertEqual(_normalize_editor("neovim"), "nvim")

        with self.assertRaises(ValueError):
            _normalize_editor("vim")


if __name__ == "__main__":
    unittest.main()
