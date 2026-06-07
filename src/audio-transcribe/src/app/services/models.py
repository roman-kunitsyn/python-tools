from pathlib import Path

from src.app.models.config import DEFAULT_MODEL_DIR


def list_model_files(model_dir: Path = DEFAULT_MODEL_DIR) -> list[Path]:
    if not model_dir.exists() or not model_dir.is_dir():
        return []

    return sorted(path for path in model_dir.iterdir() if path.is_file())
