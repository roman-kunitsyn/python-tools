import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from voice_note.models.assistant_message import AssistantMessage


class AssistantMessageStore:
    def __init__(
        self,
        messages_file: Path,
        transcript_file: Path,
        session: str,
    ) -> None:
        self.messages_file = messages_file
        self.transcript_file = transcript_file
        self.session = session

    def load_messages(self) -> list[AssistantMessage]:
        payload = self._read_payload()
        data = payload.get("data", [])
        messages = [self._message_from_payload(item) for item in data]
        return sorted(messages, key=lambda message: message.created_at)

    def get_message(self, message_id: str) -> AssistantMessage | None:
        for message in self.load_messages():
            if message.message_id == message_id:
                return message

        return None

    def append_message(
        self,
        role: str,
        prompt: str,
        response: str = "",
        created_at: datetime | None = None,
        source_audio: Path | None = None,
        response_state: str = "draft",
    ) -> AssistantMessage:
        message = AssistantMessage(
            message_id=uuid4().hex,
            role=role.strip(),
            prompt=prompt.strip(),
            response=response.strip(),
            created_at=created_at or datetime.now(),
            source_audio=source_audio,
            response_state=response_state,
        )
        messages = self.load_messages()
        messages.append(message)
        self._write(messages)
        return message

    def update_message(
        self,
        message_id: str,
        prompt: str | None = None,
        response: str | None = None,
        response_state: str | None = None,
    ) -> AssistantMessage:
        messages = self.load_messages()
        updated_messages: list[AssistantMessage] = []
        updated_message: AssistantMessage | None = None

        for message in messages:
            if message.message_id == message_id:
                updated_message = AssistantMessage(
                    message_id=message.message_id,
                    role=message.role,
                    prompt=message.prompt if prompt is None else prompt.strip(),
                    response=message.response if response is None else response.strip(),
                    created_at=message.created_at,
                    source_audio=message.source_audio,
                    response_state=message.response_state
                    if response_state is None
                    else response_state,
                )
                updated_messages.append(updated_message)
            else:
                updated_messages.append(message)

        if updated_message is None:
            raise KeyError(f"Message not found: {message_id}")

        self._write(updated_messages)
        return updated_message

    def delete_message(self, message_id: str) -> None:
        messages = self.load_messages()
        filtered_messages = [message for message in messages if message.message_id != message_id]
        if len(filtered_messages) == len(messages):
            raise KeyError(f"Message not found: {message_id}")

        self._write(filtered_messages)

    def replace_messages(self, messages: list[AssistantMessage]) -> None:
        ordered_messages = sorted(messages, key=lambda message: message.created_at)
        self._write(ordered_messages)

    def _read_payload(self) -> dict:
        if not self.messages_file.exists():
            return {"session": self.session, "data": []}

        raw = self.messages_file.read_text().strip()
        if raw == "":
            return {"session": self.session, "data": []}

        return json.loads(raw)

    def _message_from_payload(self, payload: dict) -> AssistantMessage:
        created_at = datetime.fromisoformat(payload["created_at"])
        source_audio = payload.get("source_audio")
        return AssistantMessage(
            message_id=str(payload["id"]),
            role=str(payload["role"]),
            prompt=str(payload.get("prompt", "")),
            response=str(payload.get("response", "")),
            created_at=created_at,
            source_audio=Path(source_audio) if source_audio else None,
            response_state=str(payload.get("response_state", "draft")),
        )

    def _write(self, messages: list[AssistantMessage]) -> None:
        payload = {
            "session": self.session,
            "data": [self._payload_from_message(message) for message in messages],
        }
        self.messages_file.parent.mkdir(parents=True, exist_ok=True)
        self.messages_file.write_text(json.dumps(payload, indent=2) + "\n")
        self.transcript_file.parent.mkdir(parents=True, exist_ok=True)
        self.transcript_file.write_text(self._render_transcript(messages))

    def _payload_from_message(self, message: AssistantMessage) -> dict:
        payload = {
            "id": message.message_id,
            "role": message.role,
            "prompt": message.prompt,
            "response": message.response,
            "created_at": message.created_at.isoformat(),
            "response_state": message.response_state,
        }
        if message.source_audio is not None:
            payload["source_audio"] = str(message.source_audio)
        return payload

    def _render_transcript(self, messages: list[AssistantMessage]) -> str:
        if not messages:
            return ""

        return "\n\n".join(self._render_message(message) for message in messages) + "\n"

    def _render_message(self, message: AssistantMessage) -> str:
        parts = [f"[{message.created_at.strftime('%Y-%m-%d %H:%M:%S')}]", f"Role: {message.role}"]
        if message.prompt:
            parts.append(f"Prompt: {message.prompt}")
        if message.response:
            parts.append(f"Response: {message.response}")
        else:
            parts.append("Response:")
        parts.append(f"State: {message.response_state}")
        return "\n".join(parts)
