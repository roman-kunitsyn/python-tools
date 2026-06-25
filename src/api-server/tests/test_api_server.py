from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.audio_recordings import AudioRecordingService
from app.services.meeting_recordings import MeetingRecordingService
from app.services.transcriptions import TranscriptionService
from app.services.voice_notes import VoiceNoteService


class FakeAudioRecorder:
    def __init__(self, settings, verbose: bool = False) -> None:
        self.settings = settings
        self.verbose = verbose
        self._output_file = settings.output_file or Path(tempfile.gettempdir()) / "fake.wav"

    def start(self) -> Path:
        return self._output_file

    def stop(self) -> Path:
        return self._output_file

    def cleanup(self, audio_file: Path) -> None:
        return None


class FakePushToTalkRecorder:
    def __init__(
        self,
        audio_output_folder: Path | None = None,
        audio_file: Path | None = None,
        audio_device: str | None = None,
        max_recording_seconds: int | None = None,
        keep_audio: bool = False,
        verbose: bool = False,
        timestamp_provider=None,
    ) -> None:
        self.audio_output_folder = audio_output_folder
        self.audio_file = audio_file or (audio_output_folder / "audio.wav" if audio_output_folder else Path(tempfile.gettempdir()) / "voice-note.wav")
        self.audio_device = audio_device
        self.max_recording_seconds = max_recording_seconds
        self.keep_audio = keep_audio
        self.verbose = verbose
        self.timestamp_provider = timestamp_provider

    def start(self) -> Path:
        return self.audio_file

    def stop(self) -> Path:
        return self.audio_file

    def cleanup(self, audio_file: Path) -> None:
        return None


class FakeWriter:
    writes_to_file = True

    def __init__(self, output_file: Path) -> None:
        self.output_file = output_file
        self.written: list[str] = []

    def write(self, text: str) -> None:
        self.written.append(text)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(text)


class FakeJsonWriter:
    def __init__(self, output_file: Path, session: str) -> None:
        self.output_file = output_file
        self.session = session
        self.written = []

    def write_note(self, note) -> None:
        self.written.append(note)


class FakeTranscriber:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def transcribe(self, audio_file: Path) -> str:
        return "hello world"


class ApiServerTests(unittest.TestCase):
    def test_health_lists_tools(self) -> None:
        client = TestClient(create_app())
        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertGreaterEqual(len(payload["tools"]), 4)

    def test_tools_route_lists_tools(self) -> None:
        client = TestClient(create_app())
        response = client.get("/tools")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(len(payload), 4)

    def test_audio_recording_session_start_and_stop(self) -> None:
        service = AudioRecordingService()

        with patch("app.services.audio_recordings.AudioRecorder", FakeAudioRecorder):
            session_id, output_file = service.start(
                output_file=Path("tmp/audio.wav"),
                device="Mic",
                duration=None,
                sample_rate=16000,
                channels=1,
                output_format="wav",
                verbose=False,
            )
            self.assertTrue(session_id)
            self.assertEqual(output_file, Path("tmp/audio.wav"))
            self.assertEqual(service.stop(session_id), Path("tmp/audio.wav"))

    def test_meeting_recording_session_writes_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            meetings_dir = Path(temp_dir) / "meetings"
            service = MeetingRecordingService()

            with patch("app.services.meeting_recordings.AudioRecorder", FakeAudioRecorder):
                session_id, session = service.start(
                    meetings_dir=meetings_dir,
                    stamp="team-sync",
                    device_name="Mic",
                    timestamp="2026_06_26-10_30_00",
                    verbose=False,
                )

            self.assertTrue(session_id)
            self.assertTrue(session.meeting_dir.exists())
            self.assertEqual(
                session.metadata_file.read_text().strip(),
                '{\n  "stamp": "team-sync",\n  "timestamp": "2026_06_26-10_30_00"\n}',
            )
            stopped = service.stop(session_id)
            self.assertEqual(stopped.audio_file, session.audio_file)

    def test_transcription_service_builds_expected_command(self) -> None:
        service = TranscriptionService()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            audio_file = temp_path / "sample.wav"
            audio_file.write_text("audio")
            model_file = temp_path / "ggml-small.bin"
            model_file.write_text("model")

            recorded = {}

            def fake_run(command, check):
                recorded["command"] = command
                recorded["check"] = check
                return None

            with patch("app.services.transcriptions.subprocess.run", fake_run):
                output_file = service.transcribe(
                    audio_file=audio_file,
                    output_file=None,
                    output_format="json",
                    model_file=model_file,
                    language="auto",
                    verbose=False,
                )

            self.assertEqual(output_file, audio_file.with_suffix(".json"))
            self.assertEqual(recorded["command"][0], "whisper-cli")
            self.assertIn("-oj", recorded["command"])

    def test_voice_note_session_transcribes_and_writes_outputs(self) -> None:
        service = VoiceNoteService()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            session_dir = temp_path / "session"
            audio_file = session_dir / "audio.wav"
            text_output_file = session_dir / "transcribe.txt"
            json_output_file = session_dir / "transcribe.json"

            with patch("app.services.voice_notes.PushToTalkRecorder", FakePushToTalkRecorder), patch(
                "app.services.voice_notes.WhisperTranscriber", FakeTranscriber
            ), patch("app.services.voice_notes.build_writer", lambda output_file: FakeWriter(output_file)), patch(
                "app.services.voice_notes.TranscriptJsonWriter", FakeJsonWriter
            ):
                session_id, session = service.start(
                    audio_output_folder=session_dir / "audio",
                    keep_audio=False,
                    text_output_file=text_output_file,
                    json_output_file=json_output_file,
                    append_timestamp=True,
                    language="en",
                    model="small",
                    verbose=False,
                    session_dir=session_dir,
                    audio_file=audio_file,
                    audio_device="Mic",
                    max_recording_seconds=90,
                )
                self.assertTrue(session_id)
                self.assertEqual(session.audio_file, audio_file)
                payload, audio_path, text = service.stop(session_id)

            self.assertEqual(audio_path, audio_file)
            self.assertEqual(text, "hello world")
            self.assertEqual(payload.session_dir, session_dir)
            self.assertTrue(text_output_file.exists())
            self.assertEqual(text_output_file.read_text().strip().endswith("hello world"), True)


if __name__ == "__main__":
    unittest.main()
