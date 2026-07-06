"""
Pydantic schemas for chat-related API requests and responses.

These define the contract between LocalOps Assistant and its clients.
Everything HTTP-facing in the chat domain is shaped here.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming request to /api/v1/chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="User message to send to the model.",
    )
    model: str | None = Field(
        default=None,
        description="Override the default model. If null, uses OLLAMA_DEFAULT_MODEL.",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=10_000,
        description="Optional system prompt to guide the model's behavior.",
    )
    conversation_id: UUID | None = Field(
        default=None,
        description=(
            "Optional conversation ID for multi-turn context. "
            "Not used yet — reserved for Phase 2 when memory is added."
        ),
    )


class ChatResponse(BaseModel):
    """Response from /api/v1/chat."""

    conversation_id: UUID | None = Field(
        default=None,
        description="Conversation ID. Null in Phase 1 (no memory yet).",
    )
    message: str = Field(..., description="The model's response text.")
    model: str = Field(..., description="The model that generated this response.")
    duration_ms: int = Field(..., ge=0, description="Total time in milliseconds.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp when the response was produced.",
    )


class ChatRole(BaseModel):
    """A single message in Ollama's chat format. Used internally by the provider."""

    role: Literal["system", "user", "assistant"]
    content: str


class ModelInfo(BaseModel):
    """Information about a single model available in Ollama."""

    name: str
    size_bytes: int = Field(..., ge=0)
    modified_at: datetime


class ModelsResponse(BaseModel):
    """Response from /api/v1/models."""

    models: list[ModelInfo]
