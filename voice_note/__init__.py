from pathlib import Path


_TOOL_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "voice-note" / "voice_note"
if _TOOL_PACKAGE.exists():
    __path__.append(str(_TOOL_PACKAGE))
