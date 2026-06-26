from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from aiogram import Bot

from telegram_bot.config import BotSettings
from telegram_bot.models import AudioSource, VoiceNoteEntry, VoiceNoteSession


TIMESTAMP_FORMAT = "%Y_%m_%d-%H_%M_%S"


class VoiceNoteStorageService:
    def __init__(self, settings: BotSettings) -> None:
        self.settings = settings

    def create_session(self, chat_id: int, user_id: int) -> VoiceNoteSession:
        session_id = uuid4().hex
        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        session_dir = self.settings.voice_notes_dir / f"voice_note_{timestamp}_{session_id[:8]}"
        audio_dir = session_dir / "audio"
        transcript_file = session_dir / "transcript.md"
        metadata_file = session_dir / "metadata.json"

        self.settings.voice_notes_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=False)
        self._write_metadata(
            metadata_file,
            {
                "session_id": session_id,
                "user_id": user_id,
                "chat_id": chat_id,
                "created_at": datetime.now().isoformat(),
                "completed_at": None,
                "voices": [],
            },
        )

        return VoiceNoteSession(
            session_id=session_id,
            chat_id=chat_id,
            user_id=user_id,
            session_dir=session_dir,
            audio_dir=audio_dir,
            transcript_file=transcript_file,
            metadata_file=metadata_file,
        )

    async def download_audio(
        self,
        bot: Bot,
        source: AudioSource,
        destination: Path,
    ) -> Path:
        file = await bot.get_file(source.file_id)
        if file.file_path is None:
            raise RuntimeError("Telegram file path is missing")

        destination.parent.mkdir(parents=True, exist_ok=True)
        await bot.download_file(file.file_path, destination=destination)
        return destination

    async def convert_to_wav(self, input_file: Path) -> Path:
        output_file = input_file.with_suffix(".wav")
        if input_file.suffix.lower() == ".wav":
            if input_file != output_file:
                output_file.write_bytes(input_file.read_bytes())
            return output_file

        command = ["ffmpeg", "-y", "-i", str(input_file), str(output_file)]
        await asyncio.to_thread(self._run_command, command)
        return output_file

    async def append_transcript(self, session: VoiceNoteSession, entry: VoiceNoteEntry) -> None:
        await asyncio.to_thread(self._append_transcript_block, session.transcript_file, entry)
        await asyncio.to_thread(self._update_metadata, session)

    async def finalize_session(self, session: VoiceNoteSession) -> Path:
        session.completed_at = datetime.now()
        session.transcript_file.parent.mkdir(parents=True, exist_ok=True)
        session.transcript_file.touch(exist_ok=True)
        await asyncio.to_thread(self._write_final_metadata, session)
        return session.transcript_file

    async def cancel_session(self, session: VoiceNoteSession) -> None:
        await asyncio.to_thread(shutil.rmtree, session.session_dir, True)

    def _run_command(self, command: list[str]) -> None:
        try:
            subprocess.run(command, check=True, capture_output=True)
        except FileNotFoundError as error:
            raise FileNotFoundError("ffmpeg executable not found") from error

    def _append_transcript_block(self, transcript_file: Path, entry: VoiceNoteEntry) -> None:
        transcript_file.parent.mkdir(parents=True, exist_ok=True)
        block = [
            f"## Voice #{entry.index}",
            f"Audio: {entry.source_file.name}",
            f"WAV: {entry.wav_file.name}",
        ]
        if entry.duration_seconds is not None:
            block.append(f"Duration: {self._format_duration(entry.duration_seconds)}")
        if entry.detected_language:
            block.append(f"Language: {entry.detected_language}")
        block.append("")
        block.append(entry.transcript.strip() or "(no speech detected)")
        block.append("")

        existing = transcript_file.read_text() if transcript_file.exists() else ""
        content = existing.rstrip()
        if content:
            content += "\n\n"
        content += "\n".join(block).strip()
        transcript_file.write_text(content + "\n")

    def _update_metadata(self, session: VoiceNoteSession) -> None:
        self._write_metadata(session.metadata_file, self._metadata_payload(session))

    def _write_final_metadata(self, session: VoiceNoteSession) -> None:
        payload = self._metadata_payload(session)
        payload["completed_at"] = session.completed_at.isoformat() if session.completed_at else None
        self._write_metadata(session.metadata_file, payload)

    def _metadata_payload(self, session: VoiceNoteSession) -> dict:
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "chat_id": session.chat_id,
            "created_at": session.created_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "voices": [
                {
                    "index": entry.index,
                    "duration": entry.duration_seconds,
                    "file": entry.source_file.name,
                    "wav_file": entry.wav_file.name,
                    "transcript": entry.transcript,
                    "created_at": entry.created_at.isoformat(),
                }
                for entry in session.entries
            ],
        }

    def _write_metadata(self, metadata_file: Path, payload: dict) -> None:
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        metadata_file.write_text(json.dumps(payload, indent=2) + "\n")

    def _format_duration(self, seconds: float) -> str:
        whole_seconds = max(int(seconds), 0)
        minutes, remainder = divmod(whole_seconds, 60)
        return f"{minutes:02d}:{remainder:02d}"
