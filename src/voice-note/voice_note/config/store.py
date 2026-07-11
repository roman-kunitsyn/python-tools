from pathlib import Path

from voice_note.models.settings import VoiceNoteSettings


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"


class VoiceNoteConfigStore:
    def __init__(self, config_file: Path = DEFAULT_CONFIG_FILE) -> None:
        self.config_file = config_file

    def load(self) -> VoiceNoteSettings | None:
        if not self.config_file.exists():
            return None

        return VoiceNoteSettings.from_file(self.config_file)

    def save(self, settings: VoiceNoteSettings) -> Path:
        return settings.save_to_file(self.config_file)
