import shutil
import subprocess
import sys
import signal
import threading
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlaybackTarget:
    kind: str
    value: str


class AudioPlaybackController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._target: PlaybackTarget | None = None
        self._paused = False

    def play_audio_file(self, audio_file: Path) -> str:
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file does not exist: {audio_file}")

        resolved = str(audio_file.resolve())
        if sys.platform == "darwin":
            command = ["afplay", resolved]
        elif shutil.which("ffplay") is not None:
            command = ["ffplay", "-nodisp", "-autoexit", resolved]
        else:
            raise RuntimeError("No supported audio player found")

        return self._toggle_or_start(PlaybackTarget("audio", resolved), command)

    def speak_text(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned == "":
            raise ValueError("text must not be empty")

        if sys.platform != "darwin":
            raise RuntimeError("Text-to-speech fallback is only supported on macOS")

        return self._toggle_or_start(PlaybackTarget("speech", cleaned), ["say", cleaned])

    def stop(self) -> str:
        with self._lock:
            if not self._is_active_locked():
                return "idle"

            self._terminate_locked()
            return "stopped"

    def pause(self) -> str:
        with self._lock:
            if not self._is_active_locked() or self._paused:
                return "idle"

            assert self._process is not None
            self._process.send_signal(signal.SIGSTOP)
            self._paused = True
            return "paused"

    def resume(self) -> str:
        with self._lock:
            if not self._is_active_locked() or not self._paused:
                return "idle"

            assert self._process is not None
            self._process.send_signal(signal.SIGCONT)
            self._paused = False
            return "playing"

    def is_playing(self) -> bool:
        with self._lock:
            return self._is_active_locked() and not self._paused

    def is_paused(self) -> bool:
        with self._lock:
            return self._is_active_locked() and self._paused

    def _toggle_or_start(self, target: PlaybackTarget, command: list[str]) -> str:
        with self._lock:
            self._cleanup_finished_locked()
            if self._process is not None and self._target == target:
                if self._paused:
                    self._process.send_signal(signal.SIGCONT)
                    self._paused = False
                    return "playing"

                self._process.send_signal(signal.SIGSTOP)
                self._paused = True
                return "paused"

            self._terminate_locked()
            self._process = subprocess.Popen(  # noqa: S603
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                text=True,
            )
            self._target = target
            self._paused = False
            return "playing"

    def _cleanup_finished_locked(self) -> None:
        if self._process is not None and self._process.poll() is not None:
            self._process = None
            self._target = None
            self._paused = False

    def _is_active_locked(self) -> bool:
        self._cleanup_finished_locked()
        return self._process is not None

    def _terminate_locked(self) -> None:
        if self._process is None:
            self._target = None
            self._paused = False
            return

        try:
            self._process.terminate()
            self._process.wait(timeout=0.5)
        except Exception:
            try:
                self._process.kill()
            except Exception:
                pass
        finally:
            self._process = None
            self._target = None
            self._paused = False


_DEFAULT_CONTROLLER = AudioPlaybackController()


def play_audio_file(audio_file: Path) -> str:
    return _DEFAULT_CONTROLLER.play_audio_file(audio_file)


def speak_text(text: str) -> str:
    return _DEFAULT_CONTROLLER.speak_text(text)


def stop_audio_playback() -> str:
    return _DEFAULT_CONTROLLER.stop()
