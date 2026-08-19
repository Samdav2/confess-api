#!/usr/bin/env bash
set -e

echo "🚀 Starting Confess API Backend..."

# Run database migrations if alembic is configured
if [ -f "alembic.ini" ]; then
    echo "📦 Running Alembic database migrations..."
    alembic upgrade head || echo "⚠️ Alembic migration step failed or already up to date. Continuing..."
fi

# Execute start command passed to container or default uvicorn runner
PORT="${PORT:-8000}"
if [ $# -eq 0 ]; then
    echo "⚡ Booting FastAPI server on 0.0.0.0:${PORT}..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
else
    exec "$@"
fi
