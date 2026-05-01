"""
FastAPI dependency injection providers.

Routes declare dependencies via Depends(...). FastAPI calls these
functions and passes the result into the route. This decouples routes
from how their dependencies are constructed and makes them easy to
override in tests.
"""

from typing import Annotated

from fastapi import Depends, Request

from app.providers.ollama_provider import OllamaProvider
from app.services.chat_service import ChatService


def get_ollama_provider(request: Request) -> OllamaProvider:
    """
    Retrieve the OllamaProvider instance attached at startup.

    The provider lives on app.state, set up by the lifespan handler.
    This function exposes it to routes via Depends.
    """
    return request.app.state.ollama


# Type alias for cleaner route signatures.
OllamaProviderDep = Annotated[OllamaProvider, Depends(get_ollama_provider)]


def get_chat_service(ollama: OllamaProviderDep) -> ChatService:
    """Construct a ChatService for a single request."""
    return ChatService(ollama=ollama)


# Type alias used in route signatures.
ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
