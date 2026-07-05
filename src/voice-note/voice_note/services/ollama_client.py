from __future__ import annotations

from dataclasses import dataclass

import httpx

from voice_note.services.assistant_context import AssistantChatMessage


@dataclass(frozen=True)
class OllamaChatResult:
    content: str
    model: str
    done: bool
    raw: dict


class OllamaClient:
    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: float = 120.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client or httpx.Client(base_url=self.base_url, timeout=timeout)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def chat(
        self,
        messages: list[AssistantChatMessage],
        stream: bool = False,
    ) -> OllamaChatResult:
        payload = {
            "model": self.model,
            "messages": [self._message_payload(message) for message in messages],
            "stream": stream,
        }
        response = self._client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        return OllamaChatResult(
            content=str(data.get("message", {}).get("content", "")),
            model=str(data.get("model", self.model)),
            done=bool(data.get("done", False)),
            raw=data,
        )

    def _message_payload(self, message: AssistantChatMessage) -> dict:
        return {
            "role": message.role,
            "content": message.content,
        }
