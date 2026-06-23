from pathlib import Path

from audio_record.models.settings import DEFAULT_FORMAT, RecordingSettings
from audio_record.recorder.devices import AudioDeviceNotFoundError
from audio_record.recorder.ffmpeg import (
    AudioRecorderError,
    AudioRecordingError,
    FFmpegRecorder,
)
from audio_record.utils.tempfiles import build_temp_audio_file


class AudioRecorder:
    def __init__(
        self,
        settings: RecordingSettings | None = None,
        ffmpeg: FFmpegRecorder | None = None,
        verbose: bool = False,
    ) -> None:
        self.settings = settings or RecordingSettings()
        self.ffmpeg = ffmpeg or FFmpegRecorder()
        self.verbose = verbose
        self._output_file: Path | None = None

    def record(
        self,
        output_file: Path | None = None,
        duration: float | None = None,
    ) -> Path:
        settings = self._settings_for_call(output_file=output_file, duration=duration)
        target = self._resolve_output_file(settings)
        self.ffmpeg.start(settings=settings, output_file=target, verbose=self.verbose)
        self.ffmpeg.wait()
        return target

    def start(self, output_file: Path | None = None) -> Path:
        settings = self._settings_for_call(output_file=output_file)
        target = self._resolve_output_file(settings)
        self.ffmpeg.start(settings=settings, output_file=target, verbose=self.verbose)
        self._output_file = target
        return target

    def stop(self) -> Path:
        if self._output_file is None:
            raise AudioRecordingError("recording has not started")

        output_file = self._output_file
        self.ffmpeg.stop()
        self._output_file = None
        return output_file

    def _settings_for_call(
        self,
        output_file: Path | None = None,
        duration: float | None = None,
    ) -> RecordingSettings:
        return RecordingSettings(
            output_file=output_file or self.settings.output_file,
            device=self.settings.device,
            duration=duration if duration is not None else self.settings.duration,
            sample_rate=self.settings.sample_rate,
            channels=self.settings.channels,
            output_format=self.settings.output_format,
        )

    def _resolve_output_file(self, settings: RecordingSettings) -> Path:
        output_file = settings.output_file
        output_format = settings.output_format or DEFAULT_FORMAT

        if output_file is None:
            return build_temp_audio_file(output_format)

        if output_file.suffix:
            return output_file

        return output_file.with_suffix(f".{output_format}")
