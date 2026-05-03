# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: builder — installs uv and resolves dependencies into a local venv.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Install uv — a fast, modern Python package manager.
# We install it via pip into the builder stage; the final stage will get
# the resolved venv directly and won't need uv at all.
RUN pip install --no-cache-dir uv==0.4.27

WORKDIR /app

# Copy only the files needed to resolve dependencies first.
# This lets Docker cache the dependency layer separately from app code,
# so changing a Python file doesn't trigger a re-install of all deps.
COPY pyproject.toml uv.lock ./

# Sync production dependencies (no dev group) into a local .venv.
# --frozen ensures we use exactly what's in uv.lock — no re-resolving.
RUN uv sync --frozen --no-dev


# ---------------------------------------------------------------------------
# Stage 2: runtime — minimal image with just Python, the venv, and the app.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# Create an unprivileged user. Containers running as root are an
# unnecessary security risk — costs nothing to run as a regular user.
RUN groupadd --system --gid 1000 aisteve \
 && useradd --system --uid 1000 --gid aisteve --create-home aisteve

WORKDIR /app

# Copy the resolved venv from the builder. This is the only thing we need
# from the builder stage — no uv, no build artifacts, no apt cache.
COPY --from=builder --chown=aisteve:aisteve /app/.venv /app/.venv

# Copy application source. .dockerignore prevents tests, .env, etc.
# from being included.
COPY --chown=aisteve:aisteve app ./app
COPY --chown=aisteve:aisteve pyproject.toml ./pyproject.toml

# Put the venv on PATH so `python` and `uvicorn` resolve from it without
# needing `uv run` (which we don't have in this stage).
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER aisteve

EXPOSE 8000

# Healthcheck so Docker (and orchestrators like compose, k8s) know when
# the container is actually ready to serve traffic, not just running.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

# In production we don't use --reload. Single worker is fine for a
# personal homelab; scale with --workers N if needed later.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]