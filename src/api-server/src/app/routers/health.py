from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.common import HealthResponse, ToolInfo

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    services = request.app.state.services
    return HealthResponse(status="ok", tools=services.catalog.list_tools())


@router.get("/tools", response_model=list[ToolInfo])
def tools(request: Request) -> list[ToolInfo]:
    services = request.app.state.services
    return services.catalog.list_tools()
