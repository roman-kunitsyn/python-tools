from pathlib import Path


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
