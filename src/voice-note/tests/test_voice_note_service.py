import json
import io
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from rich.console import Console
from unittest.mock import patch

import httpx
from textual.widgets import Select

from voice_note.cli.cli_app import VoiceNoteCliApp, choose_cli_session, prompt_session_title
from voice_note.cli.parser import build_settings_from_args
from voice_note.models.assistant_message import AssistantMessage
from voice_note.models.note import VoiceNote
from voice_note.models.session import VoiceNoteSession, slugify_session_title
from voice_note.models.session_note import SessionNote
from voice_note.models.settings import VoiceNoteSettings
from voice_note.output.session_store import SessionNoteStore
from voice_note.output.assistant_store import AssistantMessageStore
from voice_note.output.writer import FileWriter, TranscriptJsonWriter
from voice_note.audio.player import AudioPlaybackController, speak_text
from voice_note.config import DEFAULT_CONFIG_FILE, VoiceNoteConfigStore
from voice_note.services.assistant_context import (
    AssistantChatMessage,
    AssistantContextBuilder,
)
from voice_note.services.assistant_service import AssistantService
from voice_note.services.ollama_client import OllamaClient
from voice_note.services.session_service import SessionService
from voice_note.services.voice_note_service import VoiceNoteService, format_note
from voice_note.audio.recorder import PushToTalkRecorder
from voice_note.tui.app import VoiceNoteApp
from voice_note.tui.assistant import build_assistant_tab
from voice_note.tui.components import render_assistant_message_card, render_note_card
from voice_note.tui import clipboard as clipboard_module
from voice_note.tui.screens import NoteEditResult
from voice_note.tui.app import (
    _parse_ffmpeg_audio_devices,
    _parse_ollama_list_line,
    _format_file_size,
    _whisper_model_name,
    _format_countdown,
    _editor_command,
    _format_status,
    _format_settings_sections,
    _normalize_editor,
    _session_name,
    _status_class,
    _transcript_link,
    _transcript_url,
    _vscode_url,
    discover_local_audio_devices,
    discover_local_ollama_models,
    discover_local_whisper_models,
    RefreshingSelect,
)
from voice_note.transcription.whisper_transcriber import WhisperTranscriber


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

    def test_stop_writes_transcript_json_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "voice_note_2026_06_23-22_15_00"
            store = SessionNoteStore(
                notes_file=session_dir / "notes.json",
                transcript_file=session_dir / "transcribe.txt",
                session="voice_note_2026_06_23-22_15_00",
                append_timestamp=False,
            )
            service = VoiceNoteService(
                recorder=FakeRecorder(),
                transcriber=FakeTranscriber(),
                writer=MemoryWriter(),
                session_store=store,
                append_timestamp=False,
            )

            service.start_recording()
            service.stop_recording_and_transcribe()

            payload = json.loads((session_dir / "notes.json").read_text())
            transcript_text = (session_dir / "transcribe.txt").read_text()

        self.assertEqual(payload["session"], "voice_note_2026_06_23-22_15_00")
        self.assertEqual(
            payload["data"],
            [
                {
                    "id": payload["data"][0]["id"],
                    "text": "hello world",
                    "created_at": payload["data"][0]["created_at"],
                    "audio_file": "note.wav",
                }
            ],
        )
        self.assertEqual(transcript_text, "hello world\n")

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
        self.assertEqual(
            settings.text_output_file, settings.session_dir / "transcribe.txt"
        )
        self.assertEqual(settings.json_output_file, settings.session_dir / "notes.json")
        self.assertEqual(settings.log_file, settings.session_dir / "log.txt")
        self.assertEqual(settings.audio_device, "built-in microphone")
        self.assertEqual(settings.editor, "code")
        self.assertEqual(settings.max_recording_seconds, 90)
        self.assertEqual(settings.timestamp_format, "%Y_%m_%d-%H_%M_%S")
        self.assertTrue(settings.keep_audio)
        self.assertEqual(settings.session_title, "voice_note")

    def test_loads_json_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text(
                '{"mode":"tui","language":"en","model":"small",'
                '"append_timestamp":true,"keep_audio":true,'
                '"session_title":"project review",'
                '"timestamp_format":"%Y-%m-%d_%H",'
                '"session_dir":"./from-config",'
                '"audio_output_folder":"./audio","text_output_file":"./notes.md"}'
            )

            settings = VoiceNoteSettings.from_file(config_file)

        self.assertEqual(settings.mode, "tui")
        self.assertEqual(settings.language, "en")
        self.assertEqual(settings.model, "small")
        self.assertTrue(settings.append_timestamp)
        self.assertTrue(settings.keep_audio)
        self.assertEqual(settings.session_title, "project review")
        self.assertEqual(settings.timestamp_format, "%Y-%m-%d_%H")
        self.assertEqual(settings.session_dir, Path("./from-config"))
        self.assertEqual(settings.audio_output_folder, Path("./audio"))
        self.assertEqual(settings.text_output_file, Path("./notes.md"))
        self.assertEqual(settings.audio_device, "built-in microphone")
        self.assertEqual(settings.editor, "code")

    def test_loads_default_config_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text('{"session_title":"default config"}')
            args = Namespace(
                mode=None,
                config=None,
                session=None,
                verbose=False,
                audio_output_folder=None,
                keep_audio=False,
                text_output_file=None,
                json_output_file=None,
                append_timestamp=False,
                language=None,
                model=None,
                assistant_model=None,
                audio_device=None,
                editor=None,
                max_recording_seconds=None,
            )

            with patch("voice_note.cli.parser.DEFAULT_CONFIG_FILE", config_file):
                settings = build_settings_from_args(args)

        self.assertEqual(settings.session_title, "default config")

    def test_session_flag_overrides_config_session_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            config_file.write_text(
                '{"session_dir":"./from-config","session_title":"from config"}'
            )

            args = Namespace(
                mode=None,
                config=config_file,
                session=Path(temp_dir) / "from-cli",
                verbose=False,
                audio_output_folder=None,
                keep_audio=False,
                text_output_file=None,
                json_output_file=None,
                append_timestamp=False,
                language=None,
                model=None,
                assistant_model=None,
                audio_device=None,
                editor=None,
                max_recording_seconds=None,
            )

            settings = build_settings_from_args(args)

        self.assertEqual(settings.session_dir, Path(temp_dir) / "from-cli")
        self.assertEqual(settings.session_title, "from config")

    def test_saves_and_loads_config_round_trip_without_runtime_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            settings = VoiceNoteSettings(
                mode="tui",
                audio_output_folder=Path("/tmp/audio"),
                keep_audio=True,
                text_output_file=Path("/tmp/transcribe.txt"),
                json_output_file=Path("/tmp/notes.json"),
                append_timestamp=True,
                language="en",
                model="small",
                assistant_model="qwen2.5:3b",
                verbose=True,
                session_dir=Path("/tmp/session"),
                session_title="project review",
                audio_file=Path("/tmp/audio.wav"),
                log_file=Path("/tmp/log.txt"),
                audio_device="microphone-1",
                editor="nvim",
                max_recording_seconds=60,
                timestamp_format="%Y-%m-%d_%H",
            )

            saved_path = settings.save_to_file(config_file)
            loaded = VoiceNoteSettings.from_file(saved_path)
            payload = json.loads(config_file.read_text())

            self.assertEqual(saved_path, config_file)
            self.assertEqual(loaded.mode, "tui")
            self.assertEqual(loaded.audio_output_folder, Path("/tmp/audio"))
            self.assertEqual(loaded.session_title, "project review")
            self.assertEqual(loaded.timestamp_format, "%Y-%m-%d_%H")
            self.assertIsNone(payload.get("session_dir"))
            self.assertIsNone(payload.get("audio_file"))
            self.assertEqual(payload.get("timestamp_format"), "%Y-%m-%d_%H")
            self.assertEqual(DEFAULT_CONFIG_FILE.name, "config.json")
            self.assertEqual(
                VoiceNoteConfigStore(config_file).load().session_title, "project review"
            )

    def test_parses_ollama_list_line(self) -> None:
        self.assertEqual(
            _parse_ollama_list_line("llama3.2:3b  123456  2.0 GB  2 weeks ago"),
            ("llama3.2:3b (2.0 GB)", "llama3.2:3b"),
        )
        self.assertIsNone(_parse_ollama_list_line("NAME ID SIZE MODIFIED"))
        self.assertIsNone(_parse_ollama_list_line(""))

    def test_ollama_model_options_use_local_models_and_keep_current_value(
        self,
    ) -> None:
        app = VoiceNoteApp(
            settings=VoiceNoteSettings(assistant_model="custom:latest"),
            session_service=SessionService(base_dir=Path("/tmp/voice_notes")),
        )

        with patch(
            "voice_note.tui.app.discover_local_ollama_models",
            return_value=[
                ("llama3.2:3b (2.0 GB)", "llama3.2:3b"),
                ("mistral:7b (4.1 GB)", "mistral:7b"),
            ],
        ):
            options = app._assistant_model_options("custom:latest")

        self.assertEqual(
            options,
            [
                ("custom:latest", "custom:latest"),
                ("llama3.2:3b (2.0 GB)", "llama3.2:3b"),
                ("mistral:7b (4.1 GB)", "mistral:7b"),
            ],
        )

    def test_ollama_model_discovery_handles_missing_command(self) -> None:
        with patch("voice_note.tui.app.subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(discover_local_ollama_models(), [])

    def test_parses_ffmpeg_audio_device_listing(self) -> None:
        sample_output = """
[AVFoundation input device @ 0x7fa] AVFoundation audio devices:
[AVFoundation input device @ 0x7fa] [0] MacBook Pro Microphone
[AVFoundation input device @ 0x7fa] [1] BlackHole 2ch
[AVFoundation input device @ 0x7fa] AVFoundation video devices:
"""

        self.assertEqual(
            _parse_ffmpeg_audio_devices(sample_output),
            [
                ("MacBook Pro Microphone [0]", "MacBook Pro Microphone"),
                ("BlackHole 2ch [1]", "BlackHole 2ch"),
            ],
        )

    def test_audio_device_discovery_uses_ffmpeg_and_keeps_current_value(
        self,
    ) -> None:
        app = VoiceNoteApp(
            settings=VoiceNoteSettings(audio_device="virtual mic"),
            session_service=SessionService(base_dir=Path("/tmp/voice_notes")),
        )

        ffmpeg_output = """
[AVFoundation input device @ 0x7fa] AVFoundation audio devices:
[AVFoundation input device @ 0x7fa] [0] MacBook Pro Microphone
[AVFoundation input device @ 0x7fa] [1] BlackHole 2ch
"""
        completed = type("Completed", (), {"stderr": ffmpeg_output, "stdout": ""})()

        with patch("voice_note.tui.app.subprocess.run", return_value=completed):
            options = app._audio_device_options("virtual mic")

        self.assertEqual(
            options,
            [
                ("virtual mic", "virtual mic"),
                ("MacBook Pro Microphone [0]", "MacBook Pro Microphone"),
                ("BlackHole 2ch [1]", "BlackHole 2ch"),
            ],
        )

    def test_audio_device_discovery_handles_missing_ffmpeg(self) -> None:
        with patch("voice_note.tui.app.subprocess.run", side_effect=FileNotFoundError):
            self.assertEqual(discover_local_audio_devices(), [])

    def test_parses_whisper_model_name_and_format_size(self) -> None:
        self.assertEqual(_whisper_model_name(Path("/tmp/whisper/models/ggml-base.bin")), "base")
        self.assertEqual(_whisper_model_name(Path("/tmp/whisper/models/custom.bin")), "custom")
        self.assertEqual(_format_file_size(1024), "1 KB")
        self.assertEqual(_format_file_size(1536), "1.5 KB")

    def test_whisper_model_discovery_uses_local_model_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            models_dir = Path(temp_dir) / "whisper" / "models"
            models_dir.mkdir(parents=True)
            base_model = models_dir / "ggml-base.bin"
            small_model = models_dir / "ggml-small.bin"
            base_model.write_bytes(b"a" * 1024)
            small_model.write_bytes(b"b" * 1536)

            with patch("voice_note.tui.app.DEFAULT_MODEL_DIR", models_dir):
                options = discover_local_whisper_models()

        self.assertEqual(
            options,
            [("base (1 KB)", "base"), ("small (1.5 KB)", "small")],
        )

    def test_whisper_model_options_keep_current_value_when_missing(self) -> None:
        app = VoiceNoteApp(
            settings=VoiceNoteSettings(model="custom-model"),
            session_service=SessionService(base_dir=Path("/tmp/voice_notes")),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            models_dir = Path(temp_dir) / "whisper" / "models"
            models_dir.mkdir(parents=True)
            (models_dir / "ggml-base.bin").write_bytes(b"a" * 1024)

            with patch("voice_note.tui.app.DEFAULT_MODEL_DIR", models_dir):
                options = app._model_options("custom-model")

        self.assertEqual(
            options,
            [("custom-model", "custom-model"), ("base (1 KB)", "base")],
        )

    def test_rejects_recording_limit_over_five_minutes(self) -> None:
        with self.assertRaises(ValueError):
            VoiceNoteSettings(max_recording_seconds=301).validate()

    def test_parser_rejects_zero_recording_limit(self) -> None:
        args = Namespace(
            mode=None,
            config=None,
            session=None,
            verbose=False,
            audio_output_folder=None,
            keep_audio=False,
            text_output_file=None,
            json_output_file=None,
            append_timestamp=False,
            language=None,
            model=None,
            assistant_model=None,
            audio_device=None,
            editor=None,
            max_recording_seconds=0,
        )

        with self.assertRaises(ValueError):
            build_settings_from_args(args)


class CliPromptTest(unittest.TestCase):
    def test_prompt_session_title_uses_default_when_blank(self) -> None:
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, color_system="standard")

        title = prompt_session_title(
            "voice_note",
            console=console,
            input_func=lambda: "",
        )

        self.assertEqual(title, "voice_note")
        self.assertIn("default: voice_note", buffer.getvalue())

    def test_session_line_uses_full_folder_name_and_link(self) -> None:
        session_dir = Path("/tmp/voice_note_2026_07_11-23_31_13")
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, color_system="standard")

        app = VoiceNoteCliApp(
            service=type("FakeService", (), {"writes_to_file": False})(),
            console=console,
            session_title="voice_note",
            session_dir=session_dir,
        )

        line = app._session_line()

        self.assertIn("voice_note_2026_07_11-23_31_13", line)
        self.assertIn(session_dir.resolve().as_uri(), line)
        self.assertIn("Session:", line)

    def test_choose_cli_session_returns_existing_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = SessionService(base_dir=Path(temp_dir) / "voice_notes")
            older = service.create_session(
                title="Daily Standup",
                timestamp="2026_07_11-22_00_00",
            )
            newer = service.create_session(
                title="Project Review",
                timestamp="2026_07_11-23_00_00",
            )
            buffer = io.StringIO()
            console = Console(file=buffer, force_terminal=True, color_system="standard")

            session = choose_cli_session(
                session_service=service,
                default_title="voice_note",
                console=console,
                input_func=lambda: "2",
            )

            self.assertEqual(session.session_dir, newer.session_dir)
            output = buffer.getvalue()
            self.assertIn("Select session", output)
            self.assertIn("Create new session", output)
            self.assertIn(newer.folder_name, output)
            self.assertIn(older.folder_name, output)

    def test_choose_cli_session_creates_default_session_when_no_sessions_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = SessionService(base_dir=Path(temp_dir) / "voice_notes")
            buffer = io.StringIO()
            console = Console(file=buffer, force_terminal=True, color_system="standard")

            session = choose_cli_session(
                session_service=service,
                default_title="voice_note",
                console=console,
                input_func=lambda: "",
            )

            self.assertEqual(session.title, "voice_note")
            self.assertTrue(session.session_dir.exists())
            self.assertEqual(session.session_dir.parent, service.base_dir)


class CliStatusRenderingTest(unittest.TestCase):
    def test_render_countdown_emits_clear_line_and_timestamp(self) -> None:
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, color_system="standard")

        class FakeService:
            writes_to_file = False

            def start_recording(self) -> None:
                return None

            def stop_recording_and_transcribe(self):
                raise AssertionError("not used")

        app = VoiceNoteCliApp(
            service=FakeService(),
            console=console,
            session_title="voice_note",
            session_dir=Path("/tmp/voice_note_2026_07_11-23_31_13"),
        )
        app.recording = True
        app.recording_started_at = 100.0

        with patch("voice_note.cli.cli_app.time.monotonic", return_value=100.0):
            with patch("voice_note.cli.cli_app._timestamp", return_value="12:34:56"):
                app._render_countdown(force=True)

        output = buffer.getvalue()
        self.assertIn("\x1b[2K", output)
        self.assertIn("12:34:56", output)
        self.assertIn("Recording", output)
        self.assertIn("05:00", output)


class CliStopRecordingTest(unittest.TestCase):
    def test_stop_recording_writes_plain_transcript_body(self) -> None:
        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, color_system="standard")

        class FakeService:
            writes_to_file = True

            def start_recording(self) -> None:
                return None

            def stop_recording_and_transcribe(self):
                return VoiceNote(
                    text="Hello, my name is Roman and I write long notes.",
                    created_at=datetime(2026, 7, 11, 23, 30, 0),
                    audio_file=Path("note.wav"),
                )

        app = VoiceNoteCliApp(
            service=FakeService(),
            console=console,
            session_title="voice_note",
            session_dir=Path("/tmp/voice_note_2026_07_11-23_31_13"),
        )

        app._stop_recording()

        output = buffer.getvalue()
        self.assertIn("Transcribing...", output)
        self.assertIn("Note:", output)
        self.assertIn("voice_note_2026_07_11-23_31_13", output)
        self.assertIn("Hello, my name is Roman and I write long notes.", output)
        self.assertIn("\n\nHello, my name is Roman and I write long notes.", output)
        self.assertNotIn("    Hello, my name", output)


class FileWriterTest(unittest.TestCase):
    def test_appends_text_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "notes.md"
            writer = FileWriter(output_file)

            writer.write("first")
            writer.write("second\n")

            self.assertEqual(output_file.read_text(), "first\nsecond\n")


class TranscriptJsonWriterTest(unittest.TestCase):
    def test_appends_multiple_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "transcribe.json"
            writer = TranscriptJsonWriter(output_file, session="session-a")

            writer.write_note(
                VoiceNote(
                    text="first",
                    created_at=datetime(2026, 6, 23, 22, 0, 0),
                    audio_file=Path("audio_1.wav"),
                )
            )
            writer.write_note(
                VoiceNote(
                    text="second",
                    created_at=datetime(2026, 6, 23, 22, 1, 0),
                    audio_file=Path("audio_2.wav"),
                )
            )

            payload = json.loads(output_file.read_text())

        self.assertEqual(payload["session"], "session-a")
        self.assertEqual(
            payload["data"],
            [
                {"audio": "audio_1.wav", "text": "first"},
                {"audio": "audio_2.wav", "text": "second"},
            ],
        )


class SessionServiceTest(unittest.TestCase):
    def test_creates_discovers_and_renames_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            service = SessionService(base_dir=Path(temp_dir) / "voice_notes")
            session = service.create_session(
                title="Project Review", timestamp="2026_07_04-12_34_58"
            )

            self.assertEqual(session.title, "Project Review")
            self.assertEqual(session.slug, "project_review")
            self.assertEqual(session.folder_name, "project_review_2026_07_04-12_34_58")
            self.assertTrue(session.session_dir.exists())
            self.assertTrue(session.audio_dir.exists())
            self.assertTrue(session.transcript_file.exists())
            self.assertTrue(session.notes_file.exists())
            self.assertTrue(session.log_file.exists())

            discovered = service.discover_sessions()
            self.assertEqual(
                [item.session_dir for item in discovered], [session.session_dir]
            )

            renamed = service.rename_session(session, "Daily Standup")
            self.assertEqual(renamed.title, "Daily Standup")
            self.assertEqual(renamed.slug, "daily_standup")
            self.assertEqual(renamed.folder_name, "daily_standup_2026_07_04-12_34_58")
            self.assertTrue(renamed.session_dir.exists())

    def test_slugify_session_title(self) -> None:
        self.assertEqual(slugify_session_title("Project Review"), "project_review")
        self.assertEqual(slugify_session_title(""), "voice_note")
        self.assertEqual(slugify_session_title("  "), "voice_note")


class SessionNoteStoreTest(unittest.TestCase):
    def test_appends_notes_oldest_first_and_renders_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "voice_note_2026_07_04-12_34_58"
            store = SessionNoteStore(
                notes_file=session_dir / "notes.json",
                transcript_file=session_dir / "transcribe.txt",
                session="voice_note_2026_07_04-12_34_58",
                append_timestamp=True,
            )

            first = store.append_note(
                "first",
                created_at=datetime(2026, 7, 4, 12, 35, 16),
                audio_file=Path("audio_1.wav"),
            )
            second = store.append_note(
                "second",
                created_at=datetime(2026, 7, 4, 12, 36, 12),
                audio_file=Path("audio_2.wav"),
            )

            notes = store.load_notes()
            payload = json.loads((session_dir / "notes.json").read_text())
            transcript_text = (session_dir / "transcribe.txt").read_text()

        self.assertEqual(
            [note.note_id for note in notes], [first.note_id, second.note_id]
        )
        self.assertEqual(payload["data"][0]["text"], "first")
        self.assertEqual(
            transcript_text,
            "[2026-07-04 12:35:16]\n\nfirst\n\n[2026-07-04 12:36:12]\n\nsecond\n",
        )

    def test_updates_and_deletes_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "voice_note_2026_07_04-12_34_58"
            store = SessionNoteStore(
                notes_file=session_dir / "notes.json",
                transcript_file=session_dir / "transcribe.txt",
                session="voice_note_2026_07_04-12_34_58",
                append_timestamp=False,
            )

            note = store.append_note(
                "original",
                created_at=datetime(2026, 7, 4, 12, 35, 16),
                audio_file=Path("audio_1.wav"),
            )
            updated_note = store.update_note(note.note_id, "edited text")
            store.delete_note(note.note_id)

            payload = json.loads((session_dir / "notes.json").read_text())
            transcript_text = (session_dir / "transcribe.txt").read_text()

        self.assertEqual(updated_note.text, "edited text")
        self.assertEqual(payload["data"], [])
        self.assertEqual(transcript_text, "")


class AssistantMessageStoreTest(unittest.TestCase):
    def test_appends_messages_oldest_first_and_renders_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "voice_note_2026_07_04-12_34_58"
            store = AssistantMessageStore(
                messages_file=session_dir / "assistant.json",
                transcript_file=session_dir / "assistant.txt",
                session="voice_note_2026_07_04-12_34_58",
            )

            first = store.append_message(
                role="user",
                prompt="give me a summary",
                response="",
                created_at=datetime(2026, 7, 4, 12, 35, 16),
            )
            second = store.append_message(
                role="assistant",
                prompt="give me a summary",
                response="Summary output",
                created_at=datetime(2026, 7, 4, 12, 36, 12),
                response_state="complete",
            )

            messages = store.load_messages()
            payload = json.loads((session_dir / "assistant.json").read_text())
            transcript_text = (session_dir / "assistant.txt").read_text()

        self.assertEqual(
            [message.message_id for message in messages],
            [first.message_id, second.message_id],
        )
        self.assertEqual(payload["data"][0]["role"], "user")
        self.assertIn("Role: user", transcript_text)
        self.assertIn("Prompt: give me a summary", transcript_text)
        self.assertIn("Response: Summary output", transcript_text)
        self.assertIn("State: complete", transcript_text)


class AssistantContextBuilderTest(unittest.TestCase):
    def test_builds_session_summary_from_notes(self) -> None:
        notes = [
            SessionNote(
                note_id="note-1",
                text="first note",
                created_at=datetime(2026, 7, 4, 12, 35, 16),
            ),
            SessionNote(
                note_id="note-2",
                text="second note",
                created_at=datetime(2026, 7, 4, 12, 36, 12),
            ),
            SessionNote(
                note_id="note-3",
                text="",
                created_at=datetime(2026, 7, 4, 12, 37, 8),
            ),
        ]

        context = AssistantContextBuilder().build(
            notes=notes,
            prompt="give me summary",
            session_title="project review",
        )

        self.assertEqual(len(context.messages), 2)
        self.assertEqual(context.messages[0].role, "system")
        self.assertIn("Session title: project review", context.messages[0].content)
        self.assertIn(
            "1. [2026-07-04 12:35:16] first note", context.messages[0].content
        )
        self.assertIn(
            "2. [2026-07-04 12:36:12] second note", context.messages[0].content
        )
        self.assertNotIn("note-3", context.messages[0].content)
        self.assertEqual(context.messages[1].role, "user")
        self.assertEqual(context.messages[1].content, "give me summary")


class OllamaClientTest(unittest.TestCase):
    def test_chat_sends_messages_and_parses_response(self) -> None:
        requests: list[dict] = []

        class FakeResponse:
            def __init__(self) -> None:
                self.status_code = 200
                self.request = httpx.Request("POST", "http://localhost:11434/api/chat")

            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict:
                return {
                    "model": "llama3.2",
                    "done": True,
                    "message": {"role": "assistant", "content": "Summary output"},
                }

        class FakeClient:
            def post(self, path: str, json: dict) -> FakeResponse:
                requests.append({"path": path, "json": json})
                return FakeResponse()

        client = OllamaClient(
            model="llama3.2",
            client=FakeClient(),  # type: ignore[arg-type]
        )

        result = client.chat(
            [
                AssistantChatMessage(role="system", content="context"),
                AssistantChatMessage(role="user", content="give me summary"),
            ],
            stream=False,
        )

        self.assertEqual(requests[0]["path"], "/api/chat")
        self.assertEqual(requests[0]["json"]["model"], "llama3.2")
        self.assertFalse(requests[0]["json"]["stream"])
        self.assertEqual(result.content, "Summary output")
        self.assertEqual(result.model, "llama3.2")
        self.assertTrue(result.done)

    def test_chat_raises_http_errors(self) -> None:
        class FakeResponse:
            def __init__(self) -> None:
                self.request = httpx.Request("POST", "http://localhost:11434/api/chat")

            def raise_for_status(self) -> None:
                raise httpx.HTTPStatusError(
                    "bad status",
                    request=self.request,
                    response=httpx.Response(500, request=self.request),
                )

        class FakeClient:
            def post(self, path: str, json: dict) -> FakeResponse:
                return FakeResponse()

        client = OllamaClient(
            model="llama3.2",
            client=FakeClient(),  # type: ignore[arg-type]
        )

        with self.assertRaises(httpx.HTTPStatusError):
            client.chat([AssistantChatMessage(role="user", content="hello")])


class AssistantServiceTest(unittest.TestCase):
    def test_generate_response_uses_notes_as_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "voice_note_2026_07_04-12_34_58"
            notes_store = SessionNoteStore(
                notes_file=session_dir / "notes.json",
                transcript_file=session_dir / "transcribe.txt",
                session="voice_note_2026_07_04-12_34_58",
            )
            notes_store.append_note(
                "first note",
                created_at=datetime(2026, 7, 4, 12, 35, 16),
            )
            assistant_store = AssistantMessageStore(
                messages_file=session_dir / "assistant.json",
                transcript_file=session_dir / "assistant.txt",
                session="voice_note_2026_07_04-12_34_58",
            )
            captured_messages: list[list[AssistantChatMessage]] = []

            class FakeOllamaClient:
                def chat(
                    self, messages: list[AssistantChatMessage], stream: bool = False
                ):
                    captured_messages.append(messages)

                    class Result:
                        content = "Summary output"
                        done = True
                        model = "llama3.2"
                        raw = {"done": True}

                    return Result()

            service = AssistantService(
                session=VoiceNoteSession(
                    title="Project Review",
                    slug="project_review",
                    timestamp="2026_07_04-12_34_58",
                    session_dir=session_dir,
                ),
                notes_store=notes_store,
                assistant_store=assistant_store,
                ollama_client=FakeOllamaClient(),
            )

            result = service.generate_response("give me summary")
            messages = assistant_store.load_messages()

        self.assertEqual(result.response_text, "Summary output")
        self.assertEqual(len(captured_messages), 1)
        self.assertEqual(captured_messages[0][0].role, "system")
        self.assertIn("first note", captured_messages[0][0].content)
        self.assertEqual([message.role for message in messages], ["user", "assistant"])


class VoiceNoteAppNavigationTest(unittest.TestCase):
    def test_note_navigation_uses_vim_and_arrow_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )

            app.notes = [
                SessionNote(
                    note_id="note-1",
                    text="first",
                    created_at=datetime(2026, 7, 4, 12, 35, 16),
                ),
                SessionNote(
                    note_id="note-2",
                    text="second",
                    created_at=datetime(2026, 7, 4, 12, 36, 12),
                ),
            ]
            app.selected_note_id = "note-1"
            app._render_notes = lambda: None  # type: ignore[method-assign]

            app.action_next_note()
            self.assertEqual(app.selected_note_id, "note-2")

            app.action_next_note()
            self.assertEqual(app.selected_note_id, "note-2")

            app.action_previous_note()
            self.assertEqual(app.selected_note_id, "note-1")

            app.action_previous_note()
            self.assertEqual(app.selected_note_id, "note-1")

    def test_note_navigation_bindings_include_arrow_keys(self) -> None:
        bindings = {binding[0]: binding[1] for binding in VoiceNoteApp.BINDINGS}
        self.assertEqual(bindings["j"], "next_note")
        self.assertEqual(bindings["k"], "previous_note")
        self.assertEqual(bindings["down"], "next_note")
        self.assertEqual(bindings["up"], "previous_note")
        self.assertEqual(bindings["shift+j"], "extend_next_note")
        self.assertEqual(bindings["shift+k"], "extend_previous_note")
        self.assertEqual(bindings["shift+down"], "extend_next_note")
        self.assertEqual(bindings["shift+up"], "extend_previous_note")
        self.assertEqual(bindings["y"], "copy_selection")
        self.assertEqual(bindings["ctrl+shift+c"], "copy_selection")
        self.assertEqual(bindings["s"], "stop_playback")

    def test_play_note_falls_back_to_say_for_text_only_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )

            note = SessionNote(
                note_id="note-1",
                text="text only note",
                created_at=datetime(2026, 7, 4, 12, 35, 16),
                audio_file=None,
            )
            captured: list[str] = []
            playback_calls: list[tuple[str, str]] = []

            class FakePlayer:
                def speak_text(self, text: str) -> str:
                    playback_calls.append(("speak", text))
                    return "playing"

                def play_audio_file(self, audio_file: Path) -> str:
                    playback_calls.append(("play", str(audio_file)))
                    return "playing"

                def stop(self) -> str:
                    playback_calls.append(("stop", ""))
                    return "stopped"

            app._selected_note = lambda: note  # type: ignore[method-assign]
            app._set_status = lambda status: captured.append(status)  # type: ignore[method-assign]
            app.audio_player = FakePlayer()  # type: ignore[assignment]

            app.action_play_note()

            self.assertEqual(playback_calls, [("speak", "text only note")])
            self.assertEqual(captured[-1], "Status: Playing")

    def test_shift_navigation_extends_selection_and_copies_plain_text(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )

            app.notes = [
                SessionNote(
                    note_id="note-1",
                    text="first note",
                    created_at=datetime(2026, 7, 4, 12, 35, 16),
                ),
                SessionNote(
                    note_id="note-2",
                    text="second note",
                    created_at=datetime(2026, 7, 4, 12, 36, 12),
                ),
                SessionNote(
                    note_id="note-3",
                    text="third note",
                    created_at=datetime(2026, 7, 4, 12, 37, 8),
                ),
            ]
            app.selected_note_id = "note-2"
            app.selection_anchor_index = 1
            app.selection_end_index = 1
            app._render_notes = lambda: None  # type: ignore[method-assign]
            captured: list[str] = []
            app._set_status = lambda status: captured.append(status)  # type: ignore[method-assign]

            with patch("voice_note.tui.app.copy_text_to_clipboard") as copy_mock:
                copy_mock.side_effect = lambda text: captured.append(text)
                app.action_extend_previous_note()
                self.assertEqual(app.selected_note_id, "note-1")
                self.assertEqual(app.selection_anchor_index, 1)
                self.assertEqual(app.selection_end_index, 0)

                app.action_copy_selection()

            self.assertEqual(captured[-2], "first note\n\nsecond note")
            self.assertEqual(captured[-1], "Status: Copied")

    def test_copy_selection_uses_plain_text_without_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )

            app.notes = [
                SessionNote(
                    note_id="note-1",
                    text="first note",
                    created_at=datetime(2026, 7, 4, 12, 35, 16),
                    audio_file=Path("audio_1.wav"),
                )
            ]
            app.selected_note_id = "note-1"
            app.selection_anchor_index = 0
            app.selection_end_index = 0
            app._render_notes = lambda: None  # type: ignore[method-assign]
            copied: list[str] = []
            app._set_status = lambda status: None  # type: ignore[method-assign]

            with patch("voice_note.tui.app.copy_text_to_clipboard") as copy_mock:
                copy_mock.side_effect = lambda text: copied.append(text)
                app.action_copy_selection()

            self.assertEqual(copied, ["first note"])

    def test_assistant_recording_routes_prompt_without_persisting_notes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )

            calls: list[tuple[str, tuple, dict]] = []

            class FakeService:
                def stop_recording_and_transcribe(
                    self, persist: bool = True
                ) -> VoiceNote:
                    calls.append(("stop", (), {"persist": persist}))
                    return VoiceNote(
                        text="assistant prompt",
                        created_at=datetime(2026, 7, 4, 12, 35, 16),
                        audio_file=Path("recording.wav"),
                    )

            app.service = FakeService()  # type: ignore[assignment]
            app.assistant_service = object()  # type: ignore[assignment]
            app._submit_assistant_prompt = lambda prompt, source_audio=None: (
                calls.append(  # type: ignore[method-assign]
                    ("prompt", (prompt, source_audio), {})
                )
            )
            app.active_tab = "assistant"
            app.recording_mode = "assistant"
            app.stopping = False
            app.recording = True
            app._stop_countdown_timers = lambda: None  # type: ignore[method-assign]
            app._set_recording_theme = lambda recording: None  # type: ignore[method-assign]
            app._set_status = lambda status: calls.append(("status", (status,), {}))  # type: ignore[method-assign]
            app.run_worker = lambda work, thread=True: work()  # type: ignore[method-assign]
            app.call_from_thread = lambda fn, *args: fn(*args)  # type: ignore[method-assign]

            app.active_tab = "notes"
            app._stop_recording()

        self.assertIn(("stop", (), {"persist": False}), calls)
        self.assertIn(
            ("prompt", ("assistant prompt", Path("recording.wav")), {}), calls
        )

    def test_assistant_message_playback_uses_source_audio_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )
            message = AssistantMessage(
                message_id="msg-1",
                role="user",
                prompt="recorded prompt",
                response="",
                created_at=datetime(2026, 7, 4, 12, 35, 16),
                source_audio=Path("recording.wav"),
            )
            playback_calls: list[tuple[str, str]] = []

            class FakePlayer:
                def play_audio_file(self, audio_file: Path) -> str:
                    playback_calls.append(("play", str(audio_file)))
                    return "playing"

                def speak_text(self, text: str) -> str:
                    playback_calls.append(("speak", text))
                    return "playing"

                def stop(self) -> str:
                    playback_calls.append(("stop", ""))
                    return "stopped"

            app._selected_assistant_message = lambda: message  # type: ignore[method-assign]
            app._set_status = lambda status: None  # type: ignore[method-assign]
            app.audio_player = FakePlayer()  # type: ignore[assignment]

            app.action_play_assistant_message()

            self.assertEqual(playback_calls, [("play", "recording.wav")])

    def test_stop_playback_stops_current_audio(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )
            calls: list[str] = []

            class FakePlayer:
                def play_audio_file(self, audio_file: Path) -> str:
                    calls.append(f"play:{audio_file}")
                    return "playing"

                def speak_text(self, text: str) -> str:
                    calls.append(f"speak:{text}")
                    return "playing"

                def stop(self) -> str:
                    calls.append("stop")
                    return "stopped"

            app.audio_player = FakePlayer()  # type: ignore[assignment]
            app._set_status = lambda status: calls.append(status)  # type: ignore[method-assign]

            app.action_stop_playback()

            self.assertEqual(calls, ["stop", "Status: Stopped"])

    def test_assistant_selection_copies_text_without_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )
            app.assistant_messages = [
                AssistantMessage(
                    message_id="msg-1",
                    role="user",
                    prompt="give me summary",
                    response="",
                    created_at=datetime(2026, 7, 4, 12, 35, 16),
                ),
                AssistantMessage(
                    message_id="msg-2",
                    role="assistant",
                    prompt="give me summary",
                    response="Summary output",
                    created_at=datetime(2026, 7, 4, 12, 36, 12),
                ),
            ]
            app.assistant_selected_message_id = "msg-1"
            app.assistant_selection_anchor_index = 0
            app.assistant_selection_end_index = 1

            text = app._selected_assistant_messages_text()

        self.assertEqual(text, "give me summary\n\nSummary output")


class TuiComponentRefactorTest(unittest.TestCase):
    def test_render_note_card_preserves_note_header_and_styles(self) -> None:
        note = SessionNote(
            note_id="note-1",
            text="Hello world",
            created_at=datetime(2026, 7, 4, 12, 35, 16),
            audio_file=Path("audio_1.wav"),
        )

        panel = render_note_card(
            note=note,
            index=1,
            selected=True,
            in_selection=False,
            zoom=1,
        )

        self.assertEqual(panel.title, "▶ 01. 2026-07-04 12:35:16  [audio]")
        self.assertEqual(panel.border_style, "black")

    def test_render_assistant_message_card_uses_green_active_style(self) -> None:
        message = AssistantMessage(
            message_id="msg-1",
            role="assistant",
            prompt="give me summary",
            response="Summary output",
            created_at=datetime(2026, 7, 4, 12, 36, 12),
        )

        panel = render_assistant_message_card(
            message=message,
            index=2,
            selected=True,
            in_selection=False,
            zoom=1,
        )

        self.assertEqual(panel.title, "▶ Response: 02. 2026-07-04 12:36:12")
        self.assertEqual(panel.border_style, "#16a34a")

    def test_render_assistant_message_card_uses_red_range_style(self) -> None:
        message = AssistantMessage(
            message_id="msg-1",
            role="assistant",
            prompt="give me summary",
            response="Summary output",
            created_at=datetime(2026, 7, 4, 12, 36, 12),
        )

        panel = render_assistant_message_card(
            message=message,
            index=2,
            selected=False,
            in_selection=True,
            zoom=1,
        )

        self.assertEqual(panel.title, "▣ Response: 02. 2026-07-04 12:36:12")
        self.assertEqual(panel.border_style, "#dc2626")

    def test_assistant_tab_placeholder_is_present(self) -> None:
        assistant_tab = build_assistant_tab()

        self.assertEqual(assistant_tab.id, "assistant-view")
        self.assertEqual(len(list(assistant_tab.compose())), 5)

    def test_save_shortcut_saves_config_on_settings_tab(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.json"
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
                config_file=config_file,
            )
            calls: list[str] = []
            app._workspace_tab = lambda: "settings"  # type: ignore[method-assign]
            app.action_save_config = lambda: calls.append("config")  # type: ignore[method-assign]

            app.action_save_notes()

        self.assertEqual(calls, ["config"])

    def test_settings_path_fields_use_placeholders_not_values(self) -> None:
        app = VoiceNoteApp(
            settings=VoiceNoteSettings(
                session_dir=Path("/tmp/voice_note_2026_07_12-12_00_00")
            ),
            session_service=SessionService(base_dir=Path("/tmp/voice_notes")),
        )

        self.assertEqual(app._audio_output_folder_value(), "")
        self.assertEqual(app._text_output_file_value(), "")
        self.assertEqual(app._json_output_file_value(), "")
        self.assertEqual(app._log_file_value(), "")
        self.assertEqual(
            app._audio_output_folder_placeholder(),
            "logs/voice_notes/voice_note_2026_07_12-12_00_00/audio",
        )
        self.assertEqual(
            app._text_output_file_placeholder(),
            "logs/voice_notes/voice_note_2026_07_12-12_00_00/transcribe.txt",
        )
        self.assertEqual(
            app._json_output_file_placeholder(),
            "logs/voice_notes/voice_note_2026_07_12-12_00_00/notes.json",
        )
        self.assertEqual(
            app._log_file_placeholder(),
            "logs/voice_notes/voice_note_2026_07_12-12_00_00/log.txt",
        )

    def test_settings_path_hint_without_session_is_concrete(self) -> None:
        app = VoiceNoteApp(
            settings=VoiceNoteSettings(session_title="project review"),
            session_service=SessionService(base_dir=Path("/tmp/voice_notes")),
        )

        hint = app._audio_output_folder_placeholder()

        self.assertIn("logs/voice_notes/project_review_", hint)
        self.assertTrue(hint.endswith("/audio"))

    def test_show_settings_tab_focuses_nested_tabs(self) -> None:
        app = VoiceNoteApp(
            settings=VoiceNoteSettings(),
            session_service=SessionService(base_dir=Path("/tmp/voice_notes")),
        )
        called: list[str] = []
        app._focus_settings_tabs = lambda: called.append("tabs")  # type: ignore[method-assign]

        app._show_tab("settings")

        self.assertEqual(called, ["tabs"])

    def test_assistant_new_note_opens_prompt_editor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )
            captured: list[str] = []
            app._open_assistant_prompt_editor = (  # type: ignore[method-assign]
                lambda title: captured.append(title)
            )
            app._workspace_tab = lambda: "assistant"  # type: ignore[method-assign]

            app.action_new_note()

        self.assertEqual(captured, ["New prompt"])

    def test_audio_device_change_updates_live_recorder(self) -> None:
        app = VoiceNoteApp(
            settings=VoiceNoteSettings(audio_device="built-in microphone"),
            session_service=SessionService(base_dir=Path("/tmp/voice_notes")),
        )
        app.service = type(
            "FakeService",
            (),
            {
                "recorder": type(
                    "FakeRecorder",
                    (),
                    {"audio_device": "built-in microphone"},
                )(),
            },
        )()

        app._update_audio_device("BlackHole 2ch")

        self.assertEqual(app.settings.audio_device, "BlackHole 2ch")
        self.assertEqual(app.service.recorder.audio_device, "BlackHole 2ch")

    def test_refreshing_select_rebuilds_options_on_refresh(self) -> None:
        calls: list[int] = []

        def provider() -> list[tuple[str, str]]:
            calls.append(1)
            return [("Built-in Mic [0]", "built-in"), ("BlackHole [1]", "blackhole")]

        widget = RefreshingSelect(
            [("Built-in Mic [0]", "built-in")],
            options_provider=provider,
            value="built-in",
        )

        widget.refresh_options()

        self.assertEqual(len(calls), 1)
        self.assertEqual(
            [value for _, value in widget._options],  # type: ignore[attr-defined]
            [Select.NULL, "built-in", "blackhole"],
        )

    def test_settings_sections_list_all_config_variables_with_descriptions(
        self,
    ) -> None:
        settings = VoiceNoteSettings(
            mode="tui",
            audio_output_folder=Path("/tmp/audio"),
            keep_audio=True,
            text_output_file=Path("/tmp/transcribe.txt"),
            json_output_file=Path("/tmp/notes.json"),
            append_timestamp=True,
            language="en",
            model="small",
            assistant_model="qwen2.5:3b",
            verbose=True,
            session_dir=Path("/tmp/session"),
            session_title="project review",
            audio_file=Path("/tmp/audio.wav"),
            log_file=Path("/tmp/log.txt"),
            audio_device="microphone-1",
            editor="nvim",
            max_recording_seconds=60,
        )

        sections = _format_settings_sections(settings, current_tab="settings")

        combined = "\n".join(sections.values())
        for keyword in [
            "mode:",
            "verbose:",
            "audio_device:",
            "language:",
            "model:",
            "assistant_model:",
            "max_recording_seconds:",
            "audio_output_folder:",
            "keep_audio:",
            "text_output_file:",
            "json_output_file:",
            "append_timestamp:",
            "editor:",
            "log_file:",
            "session_title:",
            "timestamp_format:",
            "session_dir:",
            "audio_file:",
            "current_tab:",
        ]:
            self.assertIn(keyword, combined)
        self.assertIn("Run mode for the app", combined)
        self.assertIn("Ollama model used by the Assistant tab", combined)
        self.assertIn("Session and runtime", combined)

    def test_assistant_prompt_is_stored_before_response_generation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "voice_note_2026_07_04-12_34_58"
            assistant_store = AssistantMessageStore(
                messages_file=session_dir / "assistant.json",
                transcript_file=session_dir / "assistant.txt",
                session="voice_note_2026_07_04-12_34_58",
            )
            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )
            app.assistant_store = assistant_store
            app.assistant_service = type(
                "FakeAssistantService",
                (),
                {
                    "generate_response_text": lambda self, prompt: (
                        self.assert_prompt_visible(prompt)
                    ),
                    "assert_prompt_visible": lambda self, prompt: (
                        self._assert_prompt_visible(prompt)
                    ),
                },
            )()

            def assert_prompt_visible(prompt: str) -> str:
                messages = assistant_store.load_messages()
                self.assertEqual(len(messages), 1)
                self.assertEqual(messages[0].role, "user")
                self.assertEqual(messages[0].prompt, prompt)
                self.assertEqual(messages[0].response_state, "sent")
                return "assistant response"

            app.assistant_service._assert_prompt_visible = assert_prompt_visible  # type: ignore[attr-defined]
            app._reload_assistant_messages = lambda select_message_id=None: None  # type: ignore[method-assign]
            app._set_status = lambda status: None  # type: ignore[method-assign]
            app.run_worker = lambda work, thread=True: work()  # type: ignore[method-assign]
            app.call_from_thread = lambda fn, *args: fn(*args)  # type: ignore[method-assign]

            app._submit_assistant_prompt("give me summary")

            messages = assistant_store.load_messages()

        self.assertEqual([message.role for message in messages], ["user", "assistant"])
        self.assertEqual(messages[0].prompt, "give me summary")
        self.assertEqual(messages[1].response, "assistant response")

    def test_editing_assistant_prompt_regenerates_response(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "voice_note_2026_07_04-12_34_58"
            assistant_store = AssistantMessageStore(
                messages_file=session_dir / "assistant.json",
                transcript_file=session_dir / "assistant.txt",
                session="voice_note_2026_07_04-12_34_58",
            )
            prompt_message = assistant_store.append_message(
                role="user",
                prompt="original prompt",
                response="",
                response_state="sent",
            )
            assistant_store.append_message(
                role="assistant",
                prompt="original prompt",
                response="original response",
                response_state="complete",
            )

            app = VoiceNoteApp(
                settings=VoiceNoteSettings(),
                session_service=SessionService(base_dir=Path(temp_dir)),
            )
            app.assistant_store = assistant_store

            class FakeAssistantService:
                def __init__(self) -> None:
                    self.prompts: list[str] = []

                def generate_response_text(self, prompt: str) -> str:
                    self.prompts.append(prompt)
                    return "regenerated response"

            app.assistant_service = FakeAssistantService()  # type: ignore[assignment]
            app._set_status = lambda status: None  # type: ignore[method-assign]
            app.run_worker = lambda work, thread=True: work()  # type: ignore[method-assign]
            app.call_from_thread = lambda fn, *args: fn(*args)  # type: ignore[method-assign]

            app._on_assistant_editor_result(
                NoteEditResult(mode="save", text="updated prompt"),
                prompt_message,
            )

            messages = assistant_store.load_messages()

        self.assertEqual(app.assistant_service.prompts, ["updated prompt"])
        self.assertEqual(messages[0].prompt, "updated prompt")
        self.assertEqual(messages[1].response, "regenerated response")


class ClipboardAdapterTest(unittest.TestCase):
    def test_copy_text_to_clipboard_uses_pbcopy_on_macos(self) -> None:
        calls: list[list[str]] = []

        with (
            patch("voice_note.tui.clipboard.platform.system", return_value="Darwin"),
            patch(
                "voice_note.tui.clipboard.shutil.which", return_value="/usr/bin/pbcopy"
            ),
            patch("voice_note.tui.clipboard.subprocess.run") as run_mock,
        ):
            run_mock.side_effect = lambda command, **kwargs: calls.append(command)
            clipboard_module.copy_text_to_clipboard("hello world")

        self.assertEqual(calls, [["pbcopy"]])


class AudioPlayerTest(unittest.TestCase):
    def test_play_audio_file_toggles_pause_resumes_and_stops_previous(self) -> None:
        controller = AudioPlaybackController()
        procs = []

        class FakeProc:
            def __init__(self, command: list[str]) -> None:
                self.command = command
                self.signals: list[object] = []
                self.returncode: int | None = None

            def poll(self) -> int | None:
                return self.returncode

            def send_signal(self, sig: object) -> None:
                self.signals.append(sig)

            def terminate(self) -> None:
                self.signals.append("terminate")
                self.returncode = 0

            def wait(self, timeout: float | None = None) -> int:
                self.returncode = 0
                return 0

            def kill(self) -> None:
                self.signals.append("kill")
                self.returncode = 0

        def fake_popen(command: list[str], **kwargs):
            proc = FakeProc(command)
            procs.append(proc)
            return proc

        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch("voice_note.audio.player.sys.platform", "darwin"),
            patch("voice_note.audio.player.subprocess.Popen", side_effect=fake_popen),
        ):
            audio_one = Path(temp_dir) / "one.wav"
            audio_two = Path(temp_dir) / "two.wav"
            audio_one.write_text("audio")
            audio_two.write_text("audio")

            self.assertEqual(controller.play_audio_file(audio_one), "playing")
            self.assertEqual(procs[0].command, ["afplay", str(audio_one.resolve())])

            self.assertEqual(controller.play_audio_file(audio_one), "paused")
            self.assertIn(controller.is_paused(), [True])

            self.assertEqual(controller.play_audio_file(audio_one), "playing")
            self.assertIn(controller.is_playing(), [True])

            self.assertEqual(controller.play_audio_file(audio_two), "playing")
            self.assertIn("terminate", procs[0].signals)
            self.assertEqual(procs[1].command, ["afplay", str(audio_two.resolve())])

    def test_speak_text_uses_say_on_macos(self) -> None:
        procs = []

        class FakeProc:
            def __init__(self, command: list[str]) -> None:
                self.command = command
                self.signals: list[object] = []
                self.returncode: int | None = None

            def poll(self) -> int | None:
                return self.returncode

            def send_signal(self, sig: object) -> None:
                self.signals.append(sig)

            def terminate(self) -> None:
                self.signals.append("terminate")
                self.returncode = 0

            def wait(self, timeout: float | None = None) -> int:
                self.returncode = 0
                return 0

            def kill(self) -> None:
                self.signals.append("kill")
                self.returncode = 0

        def fake_popen(command: list[str], **kwargs):
            proc = FakeProc(command)
            procs.append(proc)
            return proc

        with (
            patch("voice_note.audio.player.sys.platform", "darwin"),
            patch("voice_note.audio.player.subprocess.Popen", side_effect=fake_popen),
        ):
            controller = AudioPlaybackController()
            self.assertEqual(controller.speak_text("hello world"), "playing")
            self.assertEqual(procs[0].command, ["say", "hello world"])

            self.assertEqual(controller.speak_text("hello world"), "paused")
            self.assertEqual(controller.speak_text("hello world"), "playing")


class WhisperTranscriberTest(unittest.TestCase):
    def test_transcribe_uses_translate_flag_for_english_output(self) -> None:
        commands = []

        class FakeWhisperTranscriber(WhisperTranscriber):
            def _run(self, command: list[str]) -> None:
                commands.append(command)
                output_base = Path(command[command.index("-of") + 1])
                output_base.with_suffix(".txt").write_text("translated text")

        with tempfile.TemporaryDirectory() as temp_dir:
            model_file = Path(temp_dir) / "ggml-small.bin"
            model_file.write_text("model")
            audio_file = Path(temp_dir) / "audio.wav"
            audio_file.write_text("audio")
            transcriber = FakeWhisperTranscriber(model=str(model_file))

            self.assertEqual(transcriber.transcribe(audio_file), "translated text")

        self.assertIn("-tr", commands[0])

    def test_transcribe_raises_clear_error_when_output_file_is_missing(self) -> None:
        class MissingOutputWhisperTranscriber(WhisperTranscriber):
            def _run(self, command: list[str]) -> None:
                return None

        with tempfile.TemporaryDirectory() as temp_dir:
            model_file = Path(temp_dir) / "ggml-small.bin"
            model_file.write_text("model")
            audio_file = Path(temp_dir) / "audio.wav"
            audio_file.write_text("audio")
            transcriber = MissingOutputWhisperTranscriber(model=str(model_file))

            with self.assertRaises(RuntimeError) as ctx:
                transcriber.transcribe(audio_file)

        self.assertIn("did not create the transcript file", str(ctx.exception))


class PushToTalkRecorderTest(unittest.TestCase):
    def test_build_output_file_uses_explicit_audio_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_file = Path(temp_dir) / "voice_note" / "audio" / "audio.wav"
            recorder = PushToTalkRecorder(audio_file=audio_file, keep_audio=True)

            self.assertEqual(recorder._build_output_file(), audio_file)
            self.assertTrue(audio_file.parent.exists())

    def test_recorder_keeps_audio_device_setting(self) -> None:
        recorder = PushToTalkRecorder(
            audio_device="built-in microphone",
            max_recording_seconds=120,
        )

        self.assertEqual(recorder.audio_device, "built-in microphone")
        self.assertEqual(recorder.max_recording_seconds, 120)

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

    def test_start_passes_recording_limit_to_audio_settings(self) -> None:
        captured = {}

        class FakeAudioRecorder:
            def __init__(self, settings, verbose: bool = False) -> None:
                captured["settings"] = settings

            def start(self) -> Path:
                return Path("note.wav")

        recorder = PushToTalkRecorder(
            audio_file=Path("note.wav"),
            audio_device="built-in microphone",
            max_recording_seconds=123,
        )
        recorder._audio_recorder_type = FakeAudioRecorder

        self.assertEqual(recorder.start(), Path("note.wav"))
        self.assertEqual(captured["settings"].duration, 123)
        self.assertEqual(captured["settings"].device, "built-in microphone")


class TuiStatusTest(unittest.TestCase):
    def test_status_format_and_classes(self) -> None:
        self.assertEqual(_format_status("Idle"), "Status: Idle")
        self.assertEqual(_format_status("Status: Error"), "Status: Error")
        self.assertEqual(_status_class("Status: Idle"), "status-idle")
        self.assertEqual(_status_class("Status: Recording..."), "status-recording")
        self.assertEqual(
            _status_class("Status: Transcribing..."), "status-transcribing"
        )
        self.assertEqual(_status_class("Status: Saved"), "status-saved")
        self.assertEqual(
            _status_class("Status: Record Stop by time overflow"),
            "status-overflow",
        )
        self.assertEqual(_status_class("Status: Error"), "status-error")
        self.assertEqual(_format_countdown(300), "05:00")
        self.assertEqual(_format_countdown(65), "01:05")
        self.assertEqual(_format_countdown(0), "00:00")

    def test_session_name_and_transcript_link(self) -> None:
        transcript_file = (
            Path("logs")
            / "voice_notes"
            / "voice_note_2026_06_23-22_15_00"
            / "transcribe.txt"
        )

        self.assertEqual(
            _session_name(transcript_file), "voice_note_2026_06_23-22_15_00"
        )
        self.assertEqual(
            _transcript_link(transcript_file),
            f"Session: {transcript_file.parent}",
        )
        self.assertEqual(
            _transcript_url(transcript_file, "code"),
            _vscode_url(transcript_file.parent),
        )
        self.assertEqual(
            _transcript_url(transcript_file, "nvim"),
            transcript_file.parent.resolve().as_uri(),
        )
        self.assertEqual(_session_name(None), "Voice Note Session")
        self.assertEqual(_transcript_link(None), "Session: not selected")
        self.assertIsNone(_transcript_url(None))

    def test_editor_normalization(self) -> None:
        self.assertEqual(_normalize_editor("vscode"), "code")
        self.assertEqual(_normalize_editor("neovim"), "nvim")

        with self.assertRaises(ValueError):
            _normalize_editor("vim")

    def test_editor_commands(self) -> None:
        session_dir = Path("logs/voice_notes/session")

        self.assertEqual(
            _editor_command(session_dir, "code"),
            ["code", str(session_dir)],
        )
        self.assertEqual(
            _editor_command(session_dir, "nvim"),
            ["nvim", str(session_dir)],
        )


if __name__ == "__main__":
    unittest.main()
