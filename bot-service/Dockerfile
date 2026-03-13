# ── Stage 1: base ─────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# Install system deps needed by asyncpg (C compiler, libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: dependencies ─────────────────────────────────────────────────────
FROM base AS deps

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 3: test ─────────────────────────────────────────────────────────────
FROM deps AS test
COPY app/ ./app/
COPY tests/ ./tests/
CMD ["pytest", "-v", "--tb=short"]

# ── Stage 4: runtime ──────────────────────────────────────────────────────────
FROM deps AS runtime

# Run as non-root user for security
RUN useradd -m appuser

COPY --chown=appuser:appuser app/ ./app/

USER appuser

EXPOSE 8000

# Uvicorn with multiple workers for concurrency
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]