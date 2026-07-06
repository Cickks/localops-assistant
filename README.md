# LocalOps Assistant

[![CI](https://github.com/Cickks/localops-assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/Cickks/localops-assistant/actions/workflows/ci.yml)

LocalOps Assistant is a local-first FastAPI service that provides a simple HTTP API for chatting with
a local Ollama model. The project is built as a portfolio-grade backend service with typed request
models, structured logging, request ID tracing, health checks, Docker support, and automated tests.

The current implementation is intentionally small. It does not include memory, RAG, voice control,
monitoring integrations, command execution, or a frontend dashboard yet.

## Master Plan Alignment: Phase 22

LocalOps Assistant maps to **Phase 22: LocalOps Assistant / AI Operations Platform** in the homelab
master plan. Phase 22 is planned for later in the roadmap, after the Windows, Linux, networking,
cybersecurity, monitoring, cloud, automation, and DevOps foundation is documented and stable.

The Phase 22 goal is not to bolt AI onto unfinished infrastructure. The goal is to build a local AI
operations platform that can safely read from, summarize, and eventually assist with documented
services, health checks, logs, inventories, SOPs, incidents, and change records.

Current Phase 22 scope from the master plan:

- Prompt and versioning standards
- Provider abstraction
- Operations automation patterns
- Read-only visibility into documented services first
- Approval gates before any write or command-execution workflow
- Rollback plans before the assistant affects infrastructure

Homelab sequencing matters:

- Phase 14 adds monitoring and dashboard visibility.
- Phase 18 promotes `INFRA01` into a real always-on container/services node after SSD readiness.
- Phase 22 allows LocalOps Assistant to observe or manage `INFRA01` only after services are
  documented, monitored, and backed up.

This repository is the early API foundation for that future Phase 22 platform. It should stay honest
about what exists today and should not claim production operations features until they are built,
tested, and documented.

## Features

- FastAPI application with OpenAPI documentation at `/docs`
- Non-streaming chat endpoint backed by Ollama
- Server-Sent Events streaming endpoint
- Model listing endpoint
- Liveness and readiness checks
- Structured logging with request IDs
- Environment-based configuration with Pydantic Settings
- Unit and integration tests with coverage enforcement
- Dockerfile and Docker Compose setup for local container testing

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pydantic and pydantic-settings
- httpx
- structlog
- pytest, pytest-cov, pytest-asyncio
- Ruff
- uv
- Docker and Docker Compose
- Ollama

## Folder Structure

```text
app/
  api/          HTTP routes, middleware, and FastAPI dependencies
  core/         Settings, logging, and shared exceptions
  providers/   Ollama integration
  schemas/     Pydantic request and response models
  services/    Application logic
docs/           Product and homelab alignment notes
tests/
  integration/ End-to-end route tests using FastAPI TestClient
  unit/        Service and provider tests
```

## API Endpoints

| Method | Path                  | Purpose                                               |
| ------ | --------------------- | ----------------------------------------------------- |
| `GET`  | `/health`             | Liveness check                                        |
| `GET`  | `/ready`              | Readiness check that verifies Ollama connectivity     |
| `POST` | `/api/v1/chat`        | Send a message and receive one complete response      |
| `POST` | `/api/v1/chat/stream` | Stream assistant output as Server-Sent Events         |
| `GET`  | `/api/v1/models`      | List models available from the configured Ollama host |

## Setup

Prerequisites:

- Python 3.11+
- [uv](https://github.com/astral-sh/uv)
- [Ollama](https://ollama.com)
- A local Ollama model such as `llama3.1:8b`

```bash
git clone git@github.com:Cickks/localops-assistant.git
cd localops-assistant
cp .env.example .env
uv sync
ollama pull llama3.1:8b
uv run uvicorn app.main:app --reload
```

Open:

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Readiness check: http://localhost:8000/ready

## Example Request

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain what a readiness probe is."}'
```

Streaming:

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "List three Linux service troubleshooting commands."}'
```

## Docker

Run the API and Ollama on a private Docker network:

```bash
docker compose up --build
```

Pull the default model into the Ollama container the first time:

```bash
docker exec localops-assistant-ollama ollama pull llama3.1:8b
```

The API listens on http://localhost:8000.

## Environment Variables

Configuration is loaded from `.env`. Start with `.env.example`.

| Variable                 | Default                                             | Purpose                                 |
| ------------------------ | --------------------------------------------------- | --------------------------------------- |
| `APP_ENV`                | `development`                                       | Runtime environment                     |
| `LOG_LEVEL`              | `INFO`                                              | Application log level                   |
| `HOST`                   | `0.0.0.0`                                           | Bind address                            |
| `PORT`                   | `8000`                                              | API port                                |
| `OLLAMA_BASE_URL`        | `http://localhost:11434`                            | Ollama API URL                          |
| `OLLAMA_DEFAULT_MODEL`   | `llama3.1:8b`                                       | Default model for chat requests         |
| `OLLAMA_TIMEOUT_SECONDS` | `300`                                               | Timeout for model responses             |
| `CORS_ALLOWED_ORIGINS`   | `["http://localhost:3000","http://localhost:5173"]` | Browser origins allowed to call the API |
| `CORS_ALLOW_CREDENTIALS` | `true`                                              | Whether CORS allows credentials         |

Do not commit `.env` files.

## Development Workflow

`main` is the stable branch. Active work should happen on `dev` or short-lived feature branches
created from `dev`.

Recommended flow:

```bash
git switch dev
git pull
git switch -c feature/short-description
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Merge feature work into `dev` first. Merge `dev` into `main` only after tests pass and the README,
configuration, and deployment notes still match the code.

## Verification Commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
docker compose config
```

## Deployment Notes

This project is ready for local development and container testing. A production deployment still
needs a documented host, persistent storage plan, reverse proxy/TLS decision, monitoring, backup and
restore steps, and rollback procedure.

## Known Limitations

- No persistent conversation memory yet
- No RAG or document ingestion
- No authentication or authorization
- No frontend dashboard
- No safe command execution
- Docker Compose uses the latest Ollama image tag for local testing

## Related Documentation

- [Product vision](docs/PRODUCT_VISION.md)
- [Homelab alignment](docs/HOMELAB_ALIGNMENT.md)
