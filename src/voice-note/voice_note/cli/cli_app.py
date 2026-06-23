import sys
import termios
import tty

from voice_note.services.voice_note_service import VoiceNoteService


HELP_TEXT = """SPACE = start/stop recording
ESC   = exit
CTRL+C = exit"""


class VoiceNoteCliApp:
    def __init__(self, service: VoiceNoteService) -> None:
        self.service = service
        self.recording = False

    def run(self) -> int:
        print(HELP_TEXT)
        print("Press SPACE to start recording, SPACE again to stop.")

        try:
            while True:
                key = read_key()
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

    def _start_recording(self) -> None:
        self.service.start_recording()
        self.recording = True
        print("Recording...")

    def _stop_recording(self) -> None:
        self.recording = False
        print("Transcribing...")
        note = self.service.stop_recording_and_transcribe()
        if self.service.writes_to_file:
            print(note.text)


def read_key() -> str:
    file_descriptor = sys.stdin.fileno()
    old_settings = termios.tcgetattr(file_descriptor)
    try:
        tty.setraw(file_descriptor)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(file_descriptor, termios.TCSADRAIN, old_settings)
