from __future__ import annotations

from dataclasses import dataclass

from voice_note.models.assistant_message import AssistantMessage
from voice_note.models.session import VoiceNoteSession
from voice_note.output.assistant_store import AssistantMessageStore
from voice_note.output.session_store import SessionNoteStore
from voice_note.services.assistant_context import AssistantContextBuilder
from voice_note.services.ollama_client import OllamaClient


@dataclass(frozen=True)
class AssistantGenerationResult:
    prompt_message: AssistantMessage
    response_message: AssistantMessage
    response_text: str


class AssistantService:
    def __init__(
        self,
        session: VoiceNoteSession,
        notes_store: SessionNoteStore,
        assistant_store: AssistantMessageStore,
        ollama_client: OllamaClient,
        context_builder: AssistantContextBuilder | None = None,
    ) -> None:
        self.session = session
        self.notes_store = notes_store
        self.assistant_store = assistant_store
        self.ollama_client = ollama_client
        self.context_builder = context_builder or AssistantContextBuilder()

    def generate_response(self, prompt: str) -> AssistantGenerationResult:
        notes = self.notes_store.load_notes()
        context = self.context_builder.build(
            notes=notes,
            prompt=prompt,
            session_title=self.session.title,
        )
        ollama_result = self.ollama_client.chat(context.messages, stream=False)

        prompt_message = self.assistant_store.append_message(
            role="user",
            prompt=prompt,
            response="",
            response_state="sent",
        )
        response_message = self.assistant_store.append_message(
            role="assistant",
            prompt=prompt,
            response=ollama_result.content,
            response_state="complete" if ollama_result.done else "partial",
        )
        return AssistantGenerationResult(
            prompt_message=prompt_message,
            response_message=response_message,
            response_text=ollama_result.content,
        )
