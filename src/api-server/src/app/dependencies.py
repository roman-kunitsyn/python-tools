from __future__ import annotations

from dataclasses import dataclass

from app.services.audio_recordings import AudioRecordingService
from app.services.catalog import ToolCatalogService
from app.services.meeting_recordings import MeetingRecordingService
from app.services.sessions import SessionStore
from app.services.transcriptions import TranscriptionService
from app.services.voice_notes import VoiceNoteService


@dataclass
class AppServices:
    catalog: ToolCatalogService
    audio_recordings: AudioRecordingService
    transcriptions: TranscriptionService
    meeting_recordings: MeetingRecordingService
    voice_notes: VoiceNoteService


def build_services() -> AppServices:
    return AppServices(
        catalog=ToolCatalogService(),
        audio_recordings=AudioRecordingService(SessionStore()),
        transcriptions=TranscriptionService(),
        meeting_recordings=MeetingRecordingService(SessionStore()),
        voice_notes=VoiceNoteService(SessionStore()),
    )
