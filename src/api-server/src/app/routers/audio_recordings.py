from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.schemas.audio_recordings import (
    AudioRecordingStartRequest,
    AudioRecordingStartResponse,
    AudioRecordingStopResponse,
)

router = APIRouter(prefix="/audio-recordings", tags=["audio-recordings"])


@router.post("", response_model=AudioRecordingStartResponse, status_code=202)
def start_audio_recording(
    request: AudioRecordingStartRequest,
    app_request: Request,
) -> AudioRecordingStartResponse:
    service = app_request.app.state.services.audio_recordings
    try:
        session_id, output_file = service.start(
            output_file=request.output_file,
            device=request.device,
            duration=request.duration,
            sample_rate=request.sample_rate,
            channels=request.channels,
            output_format=request.output_format,
            verbose=request.verbose,
        )
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=503, detail=str(error)) from error

    return AudioRecordingStartResponse(
        session_id=session_id,
        output_file=output_file,
        state="running",
    )


@router.post("/{session_id}/stop", response_model=AudioRecordingStopResponse)
def stop_audio_recording(session_id: str, app_request: Request) -> AudioRecordingStopResponse:
    service = app_request.app.state.services.audio_recordings
    try:
        output_file = service.stop(session_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Audio recording session not found") from error
    except Exception as error:  # pragma: no cover - defensive boundary
        raise HTTPException(status_code=503, detail=str(error)) from error

    return AudioRecordingStopResponse(
        session_id=session_id,
        output_file=output_file,
        state="completed",
    )
