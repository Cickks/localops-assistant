"""
Integration tests for the chat routes.

These exercise the full request lifecycle: middleware → route → service →
fake provider → back through middleware. The only thing not real is the
LLM provider, which is replaced via FastAPI's dependency_overrides.

We use FastAPI's TestClient, which runs the real app in-process — no
network, no port binding, no Ollama. Real middleware (CORS, request ID),
real Pydantic validation, real exception-to-status-code mapping.
"""

import json
import re

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_ollama_provider
from app.core.exceptions import (
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnreachableError,
)
from app.main import app
from tests.conftest import FakeOllamaProvider


@pytest.fixture
def fake_provider() -> FakeOllamaProvider:
    """A fresh fake provider, registered as the app's Ollama dependency."""
    fake = FakeOllamaProvider()
    app.dependency_overrides[get_ollama_provider] = lambda: fake
    yield fake
    # Clean up after each test so overrides don't leak between tests.
    app.dependency_overrides.clear()


@pytest.fixture
def client(fake_provider: FakeOllamaProvider) -> TestClient:
    """
    TestClient with our fake provider wired in.

    The fake_provider fixture installs the override; this fixture
    just gives the test a TestClient to use.

    Note: we do NOT use TestClient as a context manager here, which
    means the lifespan handler does NOT run. That's intentional — the
    real lifespan would try to connect to Ollama. Skipping it works
    because we override the only dependency that needs the lifespan
    artifact (app.state.ollama).
    """
    return TestClient(app)


# ---------------------------------------------------------------------------
# /health and /ready
# ---------------------------------------------------------------------------


class TestHealthEndpoints:
    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_includes_request_id_header(self, client: TestClient) -> None:
        response = client.get("/health")
        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        # Generated request IDs are UUIDs.
        assert re.match(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            request_id,
        )

    def test_health_honors_incoming_request_id(self, client: TestClient) -> None:
        custom_id = "my-trace-id-12345"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.headers.get("X-Request-ID") == custom_id

    def test_ready_returns_200_when_ollama_healthy(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.canned_health = True
        response = client.get("/ready")
        assert response.status_code == 200

    def test_ready_returns_503_when_ollama_unhealthy(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.canned_health = False
        response = client.get("/ready")
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# POST /api/v1/chat — happy path and error mapping
# ---------------------------------------------------------------------------


class TestChatEndpoint:
    def test_returns_200_with_response_body(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.canned_chat_response = "Hello from the fake provider"
        response = client.post("/api/v1/chat", json={"message": "hi"})

        assert response.status_code == 200
        body = response.json()
        assert body["message"] == "Hello from the fake provider"
        assert body["model"] == "llama3.1:8b"
        assert body["duration_ms"] >= 0
        assert "created_at" in body

    def test_returns_400_on_unknown_model(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.raise_on_chat = ModelNotFoundError("missing:model")
        response = client.post(
            "/api/v1/chat",
            json={"message": "hi", "model": "missing:model"},
        )
        assert response.status_code == 400
        assert "missing:model" in response.json()["detail"]

    def test_returns_503_when_ollama_unreachable(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.raise_on_chat = OllamaUnreachableError("down")
        response = client.post("/api/v1/chat", json={"message": "hi"})
        assert response.status_code == 503

    def test_returns_504_on_timeout(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.raise_on_chat = OllamaTimeoutError("slow")
        response = client.post("/api/v1/chat", json={"message": "hi"})
        assert response.status_code == 504

    def test_returns_422_on_missing_message(self, client: TestClient) -> None:
        # No `message` field -- Pydantic should reject before reaching the route.
        response = client.post("/api/v1/chat", json={})
        assert response.status_code == 422

    def test_returns_422_on_empty_message(self, client: TestClient) -> None:
        # ChatRequest.message has min_length=1.
        response = client.post("/api/v1/chat", json={"message": ""})
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/chat/stream — SSE streaming
# ---------------------------------------------------------------------------


def _parse_sse(raw: str) -> list[dict]:
    """Parse an SSE response body into a list of decoded JSON events."""
    events: list[dict] = []
    for line in raw.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[len("data: ") :]))
    return events


class TestChatStreamEndpoint:
    def test_streams_chunks_then_done_sentinel(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.canned_chunks = ["Hello", " ", "world", "!"]
        response = client.post("/api/v1/chat/stream", json={"message": "hi"})

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")

        events = _parse_sse(response.text)
        # Four chunks plus a {"done": true} sentinel.
        assert events == [
            {"chunk": "Hello"},
            {"chunk": " "},
            {"chunk": "world"},
            {"chunk": "!"},
            {"done": True},
        ]

    def test_emits_error_event_on_model_not_found(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.raise_on_stream = ModelNotFoundError("missing:model")
        response = client.post(
            "/api/v1/chat/stream",
            json={"message": "hi", "model": "missing:model"},
        )

        # Status is still 200 — headers are sent before the error fires.
        assert response.status_code == 200
        events = _parse_sse(response.text)

        # Single error event, no chunks, no done sentinel.
        assert len(events) == 1
        assert events[0]["code"] == "model_not_found"

    def test_emits_error_event_on_timeout(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.raise_on_stream = OllamaTimeoutError("slow")
        response = client.post("/api/v1/chat/stream", json={"message": "hi"})

        assert response.status_code == 200
        events = _parse_sse(response.text)
        assert len(events) == 1
        assert events[0]["code"] == "timeout"

    def test_emits_error_event_on_unreachable(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.raise_on_stream = OllamaUnreachableError("down")
        response = client.post("/api/v1/chat/stream", json={"message": "hi"})

        assert response.status_code == 200
        events = _parse_sse(response.text)
        assert len(events) == 1
        assert events[0]["code"] == "unreachable"


# ---------------------------------------------------------------------------
# GET /api/v1/models
# ---------------------------------------------------------------------------


class TestModelsEndpoint:
    def test_returns_model_list(
        self,
        client: TestClient,
        fake_provider: FakeOllamaProvider,
        sample_model_info,
    ) -> None:
        fake_provider.canned_models = [sample_model_info]
        response = client.get("/api/v1/models")

        assert response.status_code == 200
        body = response.json()
        assert len(body["models"]) == 1
        assert body["models"][0]["name"] == "llama3.1:8b"

    def test_returns_503_when_unreachable(
        self, client: TestClient, fake_provider: FakeOllamaProvider
    ) -> None:
        fake_provider.raise_on_list = OllamaUnreachableError("down")
        response = client.get("/api/v1/models")
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# CORS preflight
# ---------------------------------------------------------------------------


class TestCors:
    def test_allowed_origin_gets_cors_headers(self, client: TestClient) -> None:
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
        assert response.headers.get("access-control-allow-credentials") == "true"

    def test_disallowed_origin_omits_allow_origin(self, client: TestClient) -> None:
        response = client.options(
            "/api/v1/chat",
            headers={
                "Origin": "http://evil.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        # Either no header at all, or a header that isn't echoing the evil origin.
        allow_origin = response.headers.get("access-control-allow-origin")
        assert allow_origin != "http://evil.example.com"
