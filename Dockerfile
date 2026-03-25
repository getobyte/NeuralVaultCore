# ═══════════════════════════════════════════════════════════════
# Cyber-Draco Legacy — NeuralVaultCore v1.0
# Docker image — multi-stage (Node UI + Python backend)
# Copyright (c) 2025-2026 getobyte — MIT License
# ═══════════════════════════════════════════════════════════════

# Stage 1: Build React UI
FROM node:20-slim AS ui-builder
WORKDIR /ui
COPY NVC-BaseUI/package*.json ./
RUN npm ci --production=false
COPY NVC-BaseUI/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.12-slim

LABEL org.opencontainers.image.title="NeuralVaultCore"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 nvc

WORKDIR /app

COPY pyproject.toml .
COPY core/ ./core/
COPY server.py nvc.py webui.py install.py ./
COPY hooks/ ./hooks/

# Install from pyproject.toml
RUN pip install --no-cache-dir ".[full]"

# Pre-download semantic search model when available. Runtime still works without it.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || true

# Copy built UI from stage 1
COPY --from=ui-builder /webui-dist ./webui-dist/

RUN mkdir -p /data && chown -R nvc:nvc /data

USER nvc

ENV NVC_DB_PATH=/data/nvc.db
ENV NVC_PROFILE=remote-homelab
ENV NVC_PORT=9998

EXPOSE 9998 9999

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${NVC_PORT:-9998}/health || exit 1

CMD ["python", "nvc.py", "serve", "--transport", "sse", "--host", "0.0.0.0", "--port", "9998"]