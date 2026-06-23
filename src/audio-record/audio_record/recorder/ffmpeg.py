import platform
import subprocess
from pathlib import Path

from audio_record.models.settings import RecordingSettings
from audio_record.recorder.devices import resolve_input_device


SUPPORTED_FORMATS = {"flac", "m4a", "mp3", "wav"}


class AudioRecorderError(RuntimeError):
    pass


class AudioRecordingError(AudioRecorderError):
    pass


class FFmpegCommandBuilder:
    def build(self, settings: RecordingSettings, output_file: Path) -> list[str]:
        settings.validate()
        output_format = settings.output_format.lower()

        if output_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {settings.output_format}. "
                f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )

        command = ["ffmpeg", "-y"]
        command.extend(self._input_args(settings.device))

        if settings.duration is not None:
            command.extend(["-t", _format_duration(settings.duration)])

        command.extend(
            [
                "-ar",
                str(settings.sample_rate),
                "-ac",
                str(settings.channels),
            ]
        )
        command.extend(_codec_args(output_format))
        command.append(str(output_file))
        return command

    def _input_args(self, device: str | None) -> list[str]:
        system = platform.system().lower()
        input_device = resolve_input_device(device)

        if system == "darwin":
            return ["-f", "avfoundation", "-i", input_device]

        if system == "windows":
            return ["-f", "dshow", "-i", input_device]

        if system == "linux":
            return ["-f", "pulse", "-i", input_device]

        raise AudioRecorderError(f"Unsupported platform: {platform.system()}")


class FFmpegRecorder:
    def __init__(self, builder: FFmpegCommandBuilder | None = None) -> None:
        self.builder = builder or FFmpegCommandBuilder()
        self._process: subprocess.Popen[bytes] | None = None

    def start(
        self,
        settings: RecordingSettings,
        output_file: Path,
        verbose: bool = False,
    ) -> subprocess.Popen[bytes]:
        if self._process is not None and self._process.poll() is None:
            raise AudioRecordingError("recording is already running")

        command = self.builder.build(settings, output_file)
        if verbose:
            print(f"Running: {' '.join(command)}")

        try:
            self._process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=None if verbose else subprocess.DEVNULL,
                stderr=None if verbose else subprocess.DEVNULL,
            )
        except FileNotFoundError as error:
            raise AudioRecorderError("ffmpeg executable not found") from error

        return self._process

    def wait(self) -> None:
        if self._process is None:
            raise AudioRecordingError("recording has not started")

        process = self._process
        try:
            return_code = process.wait()
        except KeyboardInterrupt:
            self.stop()
            raise
        finally:
            if self._process is process:
                self._process = None

        if return_code != 0:
            raise AudioRecordingError(f"ffmpeg exited with code {return_code}")

    def stop(self) -> None:
        process = self._process
        if process is None or process.poll() is not None:
            self._process = None
            return

        if process.stdin is not None:
            try:
                process.stdin.write(b"q")
                process.stdin.flush()
            except BrokenPipeError:
                process.terminate()
        else:
            process.terminate()

        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        finally:
            self._process = None


def _codec_args(output_format: str) -> list[str]:
    if output_format == "mp3":
        return ["-f", "mp3", "-codec:a", "libmp3lame"]

    if output_format == "m4a":
        return ["-f", "mp4", "-codec:a", "aac"]

    if output_format == "flac":
        return ["-f", "flac", "-codec:a", "flac"]

    return ["-f", "wav"]


def _format_duration(duration: float) -> str:
    if float(duration).is_integer():
        return str(int(duration))

    return str(duration)
