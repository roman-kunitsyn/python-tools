from pathlib import Path
import sys


def _ensure_app_path() -> None:
    app_root = Path(__file__).resolve().parent / "src"
    app_path = str(app_root)
    if app_path not in sys.path:
        sys.path.insert(0, app_path)


_ensure_app_path()

from browser_automation.main import main


if __name__ == "__main__":
    raise SystemExit(main())
