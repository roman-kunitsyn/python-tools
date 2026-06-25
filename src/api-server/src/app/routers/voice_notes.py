from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.voice_notes import (
    VoiceNoteStartRequest,
    VoiceNoteStartResponse,
    VoiceNoteStopResponse,
)

router = APIRouter(prefix="/voice-notes", tags=["voice-notes"])


@router.post("", response_model=VoiceNoteStartResponse, status_code=202)
def start_voice_note(request: VoiceNoteStartRequest, app_request: Request) -> VoiceNoteStartResponse:
    service = app_request.app.state.services.voice_notes
    try:
        session_id, session = service.start(
            audio_output_folder=request.audio_output_folder,
            keep_audio=request.keep_audio,
            text_output_file=request.text_output_file,
            json_output_file=request.json_output_file,
            append_timestamp=request.append_timestamp,
            language=request.language,
            model=request.model,
            verbose=request.verbose,
            session_dir=request.session_dir,
            audio_file=request.audio_file,
            audio_device=request.audio_device,
            max_recording_seconds=request.max_recording_seconds,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=503, detail=str(error)) from error

    return VoiceNoteStartResponse(
        session_id=session_id,
        session_dir=session.session_dir or app_request.app.state.settings.default_voice_notes_dir,
        audio_file=session.audio_file or request.audio_file or app_request.app.state.settings.default_voice_notes_dir,
        text_output_file=session.text_output_file,
        json_output_file=session.json_output_file,
        log_file=session.log_file,
        state="running",
    )


@router.post("/{session_id}/stop", response_model=VoiceNoteStopResponse)
def stop_voice_note(session_id: str, app_request: Request) -> VoiceNoteStopResponse:
    service = app_request.app.state.services.voice_notes
    try:
        session, audio_file, text = service.stop(session_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Voice note session not found") from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=503, detail=str(error)) from error

    return VoiceNoteStopResponse(
        session_id=session_id,
        session_dir=session.session_dir or app_request.app.state.settings.default_voice_notes_dir,
        audio_file=audio_file,
        text=text,
        text_output_file=session.text_output_file,
        json_output_file=session.json_output_file,
        state="completed",
    )
