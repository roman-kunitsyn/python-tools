from __future__ import annotations

import argparse
import subprocess

import uvicorn
from fastapi import FastAPI

from app.bootstrap import ensure_workspace_paths
from app.config import Settings
from app.dependencies import AppServices, build_services
from app.routers import (
    audio_recordings_router,
    health_router,
    meeting_recordings_router,
    transcriptions_router,
    voice_notes_router,
)

ensure_workspace_paths()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title=settings.title, version=settings.version)
    app.state.settings = settings
    app.state.services = build_services()

    app.include_router(health_router)
    app.include_router(audio_recordings_router)
    app.include_router(transcriptions_router)
    app.include_router(meeting_recordings_router)
    app.include_router(voice_notes_router)
    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Tools API server.")
    parser.add_argument("--host", default=Settings().host, help="Host to bind.")
    parser.add_argument("--port", type=int, default=Settings().port, help="Port to bind.")
    parser.add_argument("--reload", action="store_true", help="Enable uvicorn reload.")
    parser.add_argument(
        "--log-level",
        default=Settings().log_level,
        choices=("critical", "error", "warning", "info", "debug", "trace"),
        help="Uvicorn log level.",
    )
    return parser


def run_server(args: argparse.Namespace) -> None:
    settings = Settings(host=args.host, port=args.port, reload=args.reload, log_level=args.log_level)
    if settings.reload:
        uvicorn.run(
            "app.main:create_app",
            factory=True,
            host=settings.host,
            port=settings.port,
            reload=True,
            log_level=settings.log_level,
        )
        return

    app = create_app(settings)
    uvicorn.run(app, host=settings.host, port=settings.port, reload=False, log_level=settings.log_level)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        run_server(args)
        return 0
    except KeyboardInterrupt:
        return 130
    except subprocess.CalledProcessError as error:
        print(f"External command failed with exit code {error.returncode}.")
        return 2
