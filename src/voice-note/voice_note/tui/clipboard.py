from __future__ import annotations

import platform
import shutil
import subprocess


def copy_text_to_clipboard(text: str) -> None:
    if text == "":
        raise ValueError("clipboard text must not be empty")

    system = platform.system().lower()

    if system == "darwin" and shutil.which("pbcopy") is not None:
        subprocess.run(["pbcopy"], input=text, text=True, check=True)
        return

    if system == "linux":
        if shutil.which("wl-copy") is not None:
            subprocess.run(["wl-copy"], input=text, text=True, check=True)
            return

        if shutil.which("xclip") is not None:
            subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
            return

        if shutil.which("xsel") is not None:
            subprocess.run(["xsel", "--clipboard", "--input"], input=text, text=True, check=True)
            return

    if system == "windows" and shutil.which("clip") is not None:
        subprocess.run(["clip"], input=text, text=True, check=True)
        return

    raise RuntimeError("No supported clipboard tool found")
