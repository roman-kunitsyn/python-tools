import json
from pathlib import Path

from voice_note.models.note import VoiceNote


class TextWriter:
    writes_to_file = False
    output_file: Path | None = None

    def write(self, text: str) -> None:
        raise NotImplementedError


class StdoutWriter(TextWriter):
    def write(self, text: str) -> None:
        print(text)


class FileWriter(TextWriter):
    writes_to_file = True

    def __init__(self, output_file: Path) -> None:
        self.output_file = output_file

    def write(self, text: str) -> None:
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with self.output_file.open("a") as file:
            file.write(text)
            if not text.endswith("\n"):
                file.write("\n")


def build_writer(output_file: Path | None) -> TextWriter:
    if output_file is None:
        return StdoutWriter()

    return FileWriter(output_file)


class TranscriptJsonWriter:
    def __init__(self, output_file: Path, session: str) -> None:
        self.output_file = output_file
        self.session = session

    def write_note(self, note: VoiceNote) -> None:
        payload = self._read_payload()
        payload["session"] = self.session
        payload.setdefault("data", [])
        payload["data"].append(
            {
                "audio": str(note.audio_file),
                "text": note.text,
            }
        )
        self._write_payload(payload)

    def _read_payload(self) -> dict:
        if not self.output_file.exists():
            return {"session": self.session, "data": []}

        return json.loads(self.output_file.read_text())

    def _write_payload(self, payload: dict) -> None:
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(json.dumps(payload, indent=2) + "\n")
