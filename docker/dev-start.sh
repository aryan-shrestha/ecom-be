#!/bin/sh
set -eu

echo "[dev] Syncing dependencies..."
uv sync --locked --no-install-project --extra dev

echo "[dev] Ensuring JWT keys exist..."
if [ ! -f "${JWT_PRIVATE_KEY_PATH:-keys/jwtRS256.key}" ] || [ ! -f "${JWT_PUBLIC_KEY_PATH:-keys/jwtRS256.key.pub}" ]; then
  echo "[dev] JWT keys not found; generating..."
  python scripts/generate_keys.py
fi

echo "[dev] Running Alembic migrations..."
alembic upgrade head

echo "[dev] Starting FastAPI with hot reload..."
exec uvicorn app.presentation.api.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir /app