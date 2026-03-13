# ── Stage 1: dependencies ─────────────────────────────────────────────────────
FROM node:20-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# ── Stage 2: production deps ──────────────────────────────────────────────────
FROM node:20-slim AS prod-deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

# ── Stage 3: test ─────────────────────────────────────────────────────────────
FROM deps AS test
COPY src/ ./src/
COPY tests/ ./tests/
CMD ["npm", "test"]

# ── Stage 4: runtime ──────────────────────────────────────────────────────────
FROM node:20-slim AS runtime
WORKDIR /app

# Run as non-root user
RUN useradd -m appuser

# Copy installed deps and source code
COPY --chown=appuser:appuser --from=prod-deps /app/node_modules ./node_modules
COPY --chown=appuser:appuser package.json ./
COPY --chown=appuser:appuser src/ ./src/

USER appuser
CMD ["node", "src/index.js"]