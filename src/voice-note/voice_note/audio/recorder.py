import sys
from datetime import datetime
from pathlib import Path


TIMESTAMP_FORMAT = "%Y_%m_%d-%H_%M_%S"


def _ensure_audio_record_path() -> None:
    tool_dir = Path(__file__).resolve().parents[2]
    audio_record_dir = tool_dir.parent / "audio-record"
    audio_record_path = str(audio_record_dir)
    if audio_record_path not in sys.path:
        sys.path.insert(0, audio_record_path)


class PushToTalkRecorder:
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
        _ensure_audio_record_path()
        from audio_record import AudioRecorder, RecordingSettings

        self.audio_output_folder = audio_output_folder
        self.audio_file = audio_file
        self.audio_device = audio_device
        self.max_recording_seconds = max_recording_seconds
        self.keep_audio = keep_audio
        self.verbose = verbose
        self.timestamp_provider = timestamp_provider or build_timestamp
        self._audio_recorder_type = AudioRecorder
        self._settings_type = RecordingSettings
        self._recorder = None
        self._current_file: Path | None = None

    def start(self) -> Path:
        output_file = self._build_output_file()
        settings = self._settings_type(
            output_file=output_file,
            device=self.audio_device,
            duration=self.max_recording_seconds,
        )
        self._recorder = self._audio_recorder_type(settings=settings, verbose=self.verbose)
        self._current_file = self._recorder.start()
        return self._current_file

    def stop(self) -> Path:
        if self._recorder is None:
            raise RuntimeError("recording has not started")

        audio_file = self._recorder.stop()
        self._recorder = None
        self._current_file = None
        return audio_file

    def cleanup(self, audio_file: Path) -> None:
        if self.keep_audio:
            return
        audio_file.unlink(missing_ok=True)

    def _build_output_file(self) -> Path | None:
        if self.audio_file is not None:
            self.audio_file.parent.mkdir(parents=True, exist_ok=True)
            return self.audio_file

        if self.audio_output_folder is None:
            return None

        self.audio_output_folder.mkdir(parents=True, exist_ok=True)
        timestamp = self.timestamp_provider()
        return self.audio_output_folder / f"audio_{timestamp}.wav"


def build_timestamp() -> str:
    return datetime.now().strftime(TIMESTAMP_FORMAT)
