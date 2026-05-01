# AISteve

> A local-first AI homelab assistant — Jarvis-inspired, but grounded in real engineering.

AISteve is a self-hosted AI assistant designed to run on a homelab. It uses a local LLM (via [Ollama](https://ollama.com)), exposes a clean HTTP API, and is built to grow into a full system-aware assistant — RAG over personal notes, voice input, system monitoring, and safe command execution.

This repo is a **portfolio project** built in public, in phases, with a focus on clean architecture and real-world production patterns.

---

## Why this project exists

Most "AI chatbot" tutorials skip the engineering. AISteve is the opposite: the LLM is just one component. The interesting parts are the architecture, the layered codebase, the operational concerns (logging, health checks, configuration), and the path to running this on real homelab hardware.

Engineering goals:

- **Local-first** — no cloud LLM dependency. Everything runs on your hardware.
- **Phased** — small, working increments. No big-bang rewrites.
- **Production-style** — structured logging, environment config, typed APIs, separated layers.
- **Portable** — runs on a laptop today, migrates to a mini PC tomorrow.

---

## Phase status

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Core Brain | 🚧 In progress | FastAPI service, Ollama integration, structured logging |
| 2. Memory & RAG | ⏳ Planned | ChromaDB, conversation persistence |
| 3. Voice Node | ⏳ Planned | Raspberry Pi + Whisper STT |
| 4. System Awareness | ⏳ Planned | Prometheus metrics, log analysis |
| 5. Safe Command Execution | ⏳ Planned | Whitelisted command runner |
| 6. Dashboard | ⏳ Planned | React frontend |
| 7. Production Migration | ⏳ Planned | Mini PC deployment, reverse proxy, TLS |

---

## Architecture (Phase 1)
┌─────────────────────┐         ┌─────────────────────┐
│  HTTP Client        │◄───────►│  AISteve API        │
│  (curl, browser,    │         │  (FastAPI)          │
│  future dashboard)  │         │                     │
└─────────────────────┘         │  - /health          │
│  - /ready           │
│  - /api/v1/chat     │
└──────────┬──────────┘
│
▼
┌─────────────────────┐
│  Ollama             │
│  (local LLM server) │
└─────────────────────┘
Code is organized in layers:

- `app/api/` — HTTP routes (request/response shapes only)
- `app/services/` — Business logic ("what should AISteve do?")
- `app/providers/` — External integrations (Ollama today, ChromaDB later)
- `app/core/` — Config, logging, shared utilities
- `app/schemas/` — Pydantic request/response models

---

## Getting started

### Prerequisites

- Linux (Ubuntu 22.04+ recommended) or macOS
- Python 3.11+
- [Ollama](https://ollama.com) installed and running
- [uv](https://github.com/astral-sh/uv) (modern Python package manager)
- A pulled model (default: `llama3.1:8b`)

### Install Ollama and pull a model

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

### Clone and set up

```bash
git clone git@github.com:Cickks/AISTEVE.git
cd AISTEVE

# Create environment config
cp .env.example .env

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

---

## Development

| Command | Purpose |
|---------|---------|
| `uv run uvicorn app.main:app --reload` | Run dev server with hot reload |
| `uv run pytest` | Run tests |
| `uv run ruff check .` | Lint code |
| `uv run ruff format .` | Format code |

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
| `OLLAMA_TIMEOUT_SECONDS` | `120` | HTTP timeout when calling Ollama |

---

## License

MIT
