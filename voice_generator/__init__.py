from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

_nested_package = Path(__file__).resolve().parent.parent / "src" / "voice-generator" / "voice_generator"
if _nested_package.exists():
    __path__.append(str(_nested_package))
