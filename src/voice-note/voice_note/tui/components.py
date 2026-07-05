from __future__ import annotations

from rich import box
from rich.panel import Panel
from rich.text import Text

from voice_note.models.assistant_message import AssistantMessage
from voice_note.models.session_note import SessionNote


def render_note_card(
    note: SessionNote,
    index: int,
    selected: bool,
    in_selection: bool,
    zoom: int,
) -> Panel:
    timestamp = note.created_at.strftime("%Y-%m-%d %H:%M:%S")
    header = f"{index:02d}. {timestamp}"
    if note.audio_file is not None:
        header += "  [audio]"

    body = note.text.strip() or "(empty note)"
    zoom_padding = {1: (0, 1), 2: (1, 2), 3: (1, 3)}.get(max(1, min(3, zoom)), (0, 1))
    if selected:
        title = f"▶ {header}"
    elif in_selection:
        title = f"▣ {header}"
    else:
        title = header

    if selected:
        panel_style = "black on white"
        border_style = "black"
        body_style = "bold black"
    elif in_selection:
        panel_style = "black on #dbeafe"
        border_style = "#2563eb"
        body_style = "black"
    else:
        panel_style = "default"
        border_style = "grey70"
        body_style = "default"
    body_text = Text(body, style=body_style)

    return Panel(
        body_text,
        title=title,
        border_style=border_style,
        style=panel_style,
        box=box.ROUNDED,
        padding=zoom_padding,
        expand=True,
    )


def render_assistant_message_card(
    message: AssistantMessage,
    index: int,
    selected: bool,
    in_selection: bool,
    zoom: int,
) -> Panel:
    timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
    header = f"{index:02d}. {timestamp}"
    content = message.prompt.strip() if message.role == "user" else message.response.strip()
    label = "Prompt" if message.role == "user" else "Response"
    if message.source_audio is not None:
        header += "  [audio]"

    body = content or "(empty message)"
    zoom_padding = {1: (0, 1), 2: (1, 2), 3: (1, 3)}.get(max(1, min(3, zoom)), (0, 1))
    if selected:
        title = f"▶ {label}: {header}"
    elif in_selection:
        title = f"▣ {label}: {header}"
    else:
        title = f"{label}: {header}"

    if message.role == "user":
        panel_style = "black on #fef3c7" if not selected else "black on #dcfce7"
        border_style = "#d97706" if not selected else "#16a34a"
        body_style = "black" if not selected else "bold black"
    else:
        panel_style = "black on #dbeafe" if not selected else "black on #dcfce7"
        border_style = "#2563eb" if not selected else "#16a34a"
        body_style = "black" if not selected else "bold black"
    body_text = Text(body, style=body_style)

    return Panel(
        body_text,
        title=title,
        border_style=border_style,
        style=panel_style,
        box=box.ROUNDED,
        padding=zoom_padding,
        expand=True,
    )
