from __future__ import annotations

from pydantic import BaseModel


class ToolInfo(BaseModel):
    name: str
    description: str
    routes: list[str]


class HealthResponse(BaseModel):
    status: str
    tools: list[ToolInfo]
