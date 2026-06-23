import tempfile
from pathlib import Path


def build_temp_audio_file(output_format: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        prefix="audio-record-",
        suffix=f".{output_format}",
        delete=False,
    )
    path = Path(handle.name)
    handle.close()
    path.unlink(missing_ok=True)
    return path
