import math
import select
import sys
import termios
import time
import tty

from voice_note.services.voice_note_service import VoiceNoteService


HELP_TEXT = """SPACE = start/stop recording
ESC   = exit
CTRL+C = exit"""


class VoiceNoteCliApp:
    def __init__(
        self,
        service: VoiceNoteService,
        max_recording_seconds: int = 300,
    ) -> None:
        self.service = service
        self.max_recording_seconds = max_recording_seconds
        self.recording = False
        self.recording_started_at: float | None = None
        self.last_remaining_seconds: int | None = None

    def run(self) -> int:
        print(HELP_TEXT)
        print("Press SPACE to start recording, SPACE again to stop.")

        file_descriptor = sys.stdin.fileno()
        old_settings = termios.tcgetattr(file_descriptor)
        try:
            tty.setraw(file_descriptor)
            while True:
                key = read_key(timeout=0.2)

                if self.recording and self._recording_overflowed():
                    self._stop_recording(time_overflow=True)
                    continue

                if self.recording:
                    self._render_countdown()

                if key is None:
                    continue

                if key in ("\x1b", "\x03", "q"):
                    if self.recording:
                        self._stop_recording()
                    return 0

                if key == " ":
                    if self.recording:
                        self._stop_recording()
                    else:
                        self._start_recording()
        except KeyboardInterrupt:
            if self.recording:
                self._stop_recording()
            return 130
        finally:
            termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)

    def _start_recording(self) -> None:
        self.service.start_recording()
        self.recording = True
        self.recording_started_at = time.monotonic()
        self.last_remaining_seconds = None
        self._render_countdown(force=True)

    def _stop_recording(self, time_overflow: bool = False) -> None:
        self.recording = False
        self.recording_started_at = None
        self.last_remaining_seconds = None
        print()
        if time_overflow:
            print("Record Stop by time overflow")
        print("Transcribe...")
        note = self.service.stop_recording_and_transcribe()
        if self.service.writes_to_file:
            print(note.text)

    def _recording_overflowed(self) -> bool:
        if self.recording_started_at is None:
            return False

        return time.monotonic() - self.recording_started_at >= self.max_recording_seconds

    def _render_countdown(self, force: bool = False) -> None:
        remaining_seconds = self._remaining_seconds()
        if not force and remaining_seconds == self.last_remaining_seconds:
            return

        self.last_remaining_seconds = remaining_seconds
        print(
            f"\rRecording... {_format_countdown(remaining_seconds)}",
            end="",
            flush=True,
        )

    def _remaining_seconds(self) -> int:
        if self.recording_started_at is None:
            return self.max_recording_seconds

        elapsed = time.monotonic() - self.recording_started_at
        return max(0, math.ceil(self.max_recording_seconds - elapsed))


def read_key(timeout: float) -> str | None:
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.read(1)

    return None


def _format_countdown(seconds: int) -> str:
    minutes, remaining_seconds = divmod(max(0, seconds), 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"
