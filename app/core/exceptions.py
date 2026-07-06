"""
Custom exception types used across LocalOps Assistant.

Each exception type maps to a specific failure mode. Catching by type
lets us return the right HTTP status code without inspecting error messages.

Hierarchy:
    LocalOpsAssistantError          (base, never raised directly)
    ├── OllamaError                 (any Ollama-related failure)
    │   ├── OllamaUnreachableError  (network/connection failed)
    │   ├── OllamaTimeoutError      (request exceeded timeout)
    │   └── ModelNotFoundError      (requested model doesn't exist)
    └── ConfigurationError          (bad/missing config at runtime)
"""


class LocalOpsAssistantError(Exception):
    """Base exception for LocalOps Assistant errors."""


class OllamaError(LocalOpsAssistantError):
    """Base exception for any failure when talking to Ollama."""


class OllamaUnreachableError(OllamaError):
    """Could not connect to Ollama at all (network down, server stopped, etc.)."""


class OllamaTimeoutError(OllamaError):
    """Ollama responded too slowly. Often happens with large models on CPU."""


class ModelNotFoundError(OllamaError):
    """Requested a model that isn't installed in Ollama."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        super().__init__(
            f"Model '{model_name}' not found in Ollama. Pull it first: `ollama pull {model_name}`"
        )


class ConfigurationError(LocalOpsAssistantError):
    """Configuration is invalid or incomplete."""
