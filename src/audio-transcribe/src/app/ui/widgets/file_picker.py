from pathlib import Path

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import DirectoryTree, Footer, Header


class PathPickerScreen(Screen):
    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()
        self.start_path = start_path or Path.cwd()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DirectoryTree(str(self.start_path.expanduser()))
        yield Footer()
