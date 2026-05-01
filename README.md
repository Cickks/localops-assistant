# AISteve

> A local-first AI homelab assistant — Jarvis-inspired, but grounded in real engineering.

AISteve is a self-hosted AI assistant designed to run on a homelab. It uses a local LLM (via [Ollama](https://ollama.com)), exposes a clean HTTP API with streaming support, and is built to grow into a full system-aware assistant — RAG over personal notes, voice input, system monitoring, and safe command execution.

This repo is a **portfolio project** built in public, in phases, with a focus on clean architecture and real-world production patterns.

---

## Why this project exists

Most "AI chatbot" tutorials skip the engineering. AISteve is the opposite: the LLM is just one component. The interesting parts are the architecture, the layered codebase, the operational concerns (logging, request tracing, health checks, configuration), and the path to running this on real homelab hardware.

Engineering goals:

- **Local-first** — no cloud LLM dependency. Everything runs on your hardware.
- **Phased** — small, working increments. No big-bang rewrites.
- **Production-style** — structured logging, request ID tracing, environment config, typed APIs, separated layers.
- **Portable** — runs on a laptop today, migrates to a mini PC tomorrow. Verified on Linux and Windows.

---

## Phase status

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Core Brain | 🚧 In progress (Parts 1–3 done) | FastAPI service, Ollama integration, streaming, request tracing, CORS |
| 2. Memory & RAG | ⏳ Planned | ChromaDB, conversation persistence |
| 3. Voice Node | ⏳ Planned | Raspberry Pi + Whisper STT |
| 4. System Awareness | ⏳ Planned | Prometheus metrics, log analysis |
| 5. Safe Command Execution | ⏳ Planned | Whitelisted command runner |
| 6. Dashboard | ⏳ Planned | React frontend |
| 7. Production Migration | ⏳ Planned | Mini PC deployment, reverse proxy, TLS |

---

## Architecture (Phase 1)

```
┌─────────────────────┐         ┌─────────────────────┐
│  HTTP Client        │ ──────▶ │  AISteve API        │
│  (curl, browser,    │         │  (FastAPI/uvicorn)  │
│  future dashboard)  │ ◀────── │                     │
└─────────────────────┘   SSE   │  - /health          │
                                │  - /ready           │
                                │  - /api/v1/chat     │
                                │  - /api/v1/chat/    │
                                │      stream         │
                                │  - /api/v1/models   │
                                └──────────┬──────────┘
                                           │
                                           ▼
                                ┌─────────────────────┐
                                │  Ollama             │
                                │  (local LLM server) │
                                └─────────────────────┘
```

Code is organized in layers:

- `app/api/` — HTTP routes, middleware, FastAPI dependencies (request/response shapes only)
- `app/services/` — Business logic ("what should AISteve do?")
- `app/providers/` — External integrations (Ollama today, ChromaDB later)
- `app/core/` — Config, logging, exceptions, shared utilities
- `app/schemas/` — Pydantic request/response models

The service layer doesn't know about HTTP. The provider layer doesn't know about FastAPI. This separation is what lets future phases add new components (RAG, monitoring, voice) without rewrites.

---

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | Liveness probe (always returns 200 if the process is up) |
| `GET`  | `/ready` | Readiness probe (returns 503 if Ollama is unreachable) |
| `POST` | `/api/v1/chat` | Send a message, receive the complete response |
| `POST` | `/api/v1/chat/stream` | Send a message, stream tokens as Server-Sent Events |
| `GET`  | `/api/v1/models` | List models installed in Ollama |

Every response carries an `X-Request-ID` header. The same ID appears on every log line emitted while handling that request, making issues straightforward to trace through the layers.

Full interactive API docs are auto-generated at [`/docs`](http://localhost:8000/docs) when the server is running.

---

## Getting started

### Prerequisites

- Linux (Ubuntu 22.04+), macOS, or Windows 10/11
- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- [uv](https://github.com/astral-sh/uv) (modern Python package manager)
- A pulled model (default: `llama3.1:8b`)

### Install Ollama and pull a model

**Linux / macOS:**

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

**Windows:** download the installer from [ollama.com/download/windows](https://ollama.com/download/windows), then:

```powershell
ollama pull llama3.1:8b
```

### Clone and set up

```bash
git clone git@github.com:Cickks/AISTEVE.git
cd AISTEVE

# Create environment config
cp .env.example .env       # On Windows: Copy-Item .env.example .env

# Create venv and install dependencies
uv sync
```

### Run the API

```bash
uv run uvicorn app.main:app --reload
```

Then visit:

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Try a chat request

Non-streaming:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is a REST API?"}'
```

Streaming (Server-Sent Events):

```bash
curl -N -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Count from 1 to 10 with a comment about each."}'
```

The `-N` flag disables curl's output buffering so chunks appear as they arrive.

---

## Development

| Command | Purpose |
|---------|---------|
| `uv run uvicorn app.main:app --reload` | Run dev server with hot reload |
| `uv run pytest` | Run tests |
| `uv run ruff check .` | Lint code |
| `uv run ruff format .` | Format code |
| `uv run ruff check --fix .` | Auto-fix lint issues |

---

## Configuration

All configuration is loaded from `.env`. See `.env.example` for all variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `LOG_LEVEL` | `INFO` | Log verbosity |
| `HOST` | `0.0.0.0` | Network interface to bind |
| `PORT` | `8000` | TCP port |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is reachable |
| `OLLAMA_DEFAULT_MODEL` | `llama3.1:8b` | Model used when not specified per-request |
| `OLLAMA_TIMEOUT_SECONDS` | `300` | HTTP timeout when calling Ollama (CPU inference can be slow) |
| `CORS_ALLOWED_ORIGINS` | `["http://localhost:3000","http://localhost:5173"]` | Origins permitted to call the API from a browser |
| `CORS_ALLOW_CREDENTIALS` | `true` | Whether to allow cookies/auth headers in CORS requests |

---

## License

MIT