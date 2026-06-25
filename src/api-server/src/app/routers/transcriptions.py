from __future__ import annotations

import subprocess

from fastapi import APIRouter, HTTPException, Request

from app.schemas.transcriptions import TranscriptionRequest, TranscriptionResponse

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])


@router.post("", response_model=TranscriptionResponse)
def transcribe(request: TranscriptionRequest, app_request: Request) -> TranscriptionResponse:
    service = app_request.app.state.services.transcriptions
    settings = app_request.app.state.settings
    model_file = request.model_file or settings.default_model_file

    try:
        output_file = service.transcribe(
            audio_file=request.audio_file,
            output_file=request.output_file,
            output_format=request.output_format,
            model_file=model_file,
            language=request.language,
            verbose=request.verbose,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except subprocess.CalledProcessError as error:  # type: ignore[name-defined]
        raise HTTPException(
            status_code=502,
            detail=f"whisper-cli failed with exit code {error.returncode}",
        ) from error

    return TranscriptionResponse(
        audio_file=request.audio_file,
        output_file=output_file,
        output_format=request.output_format,
        state="completed",
    )
