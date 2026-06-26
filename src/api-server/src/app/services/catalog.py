from __future__ import annotations

from app.schemas.common import ToolInfo


class ToolCatalogService:
    def list_tools(self) -> list[ToolInfo]:
        return [
            ToolInfo(
                name="audio-recordings",
                description="Record audio with ffmpeg and manage the recording session over HTTP.",
                routes=[
                    "POST /audio-recordings",
                    "POST /audio-recordings/{session_id}/stop",
                ],
            ),
            ToolInfo(
                name="transcriptions",
                description="Transcribe an audio file with whisper-cli.",
                routes=["POST /transcriptions"],
            ),
            ToolInfo(
                name="meeting-recordings",
                description="Create timestamped meeting recording folders and manage the recording session over HTTP.",
                routes=[
                    "POST /meeting-recordings",
                    "POST /meeting-recordings/{session_id}/stop",
                ],
            ),
            ToolInfo(
                name="voice-notes",
                description="Capture a voice note, transcribe it, and write transcript outputs.",
                routes=["POST /voice-notes", "POST /voice-notes/{session_id}/stop"],
            ),
        ]
