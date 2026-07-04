import shutil
import subprocess
import sys
from pathlib import Path


def play_audio_file(audio_file: Path) -> None:
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_file}")

    if sys.platform == "darwin":
        subprocess.run(["afplay", str(audio_file)], check=True)
        return

    if shutil.which("ffplay") is not None:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", str(audio_file)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    raise RuntimeError("No supported audio player found")
