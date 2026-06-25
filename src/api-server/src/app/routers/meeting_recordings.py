from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.meeting_recordings import (
    MeetingRecordingStartRequest,
    MeetingRecordingStartResponse,
    MeetingRecordingStopResponse,
)

router = APIRouter(prefix="/meeting-recordings", tags=["meeting-recordings"])


@router.post("", response_model=MeetingRecordingStartResponse, status_code=202)
def start_meeting_recording(
    request: MeetingRecordingStartRequest,
    app_request: Request,
) -> MeetingRecordingStartResponse:
    settings = app_request.app.state.settings
    service = app_request.app.state.services.meeting_recordings
    meetings_dir = request.meetings_dir or settings.default_meetings_dir

    try:
        session_id, session = service.start(
            meetings_dir=meetings_dir,
            stamp=request.stamp,
            device_name=request.device_name,
            timestamp=request.timestamp,
            verbose=request.verbose,
        )
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=f"Meeting folder already exists: {error.filename}") from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=503, detail=str(error)) from error

    return MeetingRecordingStartResponse(
        session_id=session_id,
        meeting_dir=session.meeting_dir,
        audio_file=session.audio_file,
        metadata_file=session.metadata_file,
        timestamp=session.timestamp,
        state="running",
    )


@router.post("/{session_id}/stop", response_model=MeetingRecordingStopResponse)
def stop_meeting_recording(session_id: str, app_request: Request) -> MeetingRecordingStopResponse:
    service = app_request.app.state.services.meeting_recordings
    try:
        session = service.stop(session_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Meeting recording session not found") from error
    except Exception as error:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=503, detail=str(error)) from error

    return MeetingRecordingStopResponse(
        session_id=session_id,
        meeting_dir=session.meeting_dir,
        audio_file=session.audio_file,
        metadata_file=session.metadata_file,
        timestamp=session.timestamp,
        state="completed",
    )
