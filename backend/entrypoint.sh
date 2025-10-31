#!/usr/bin/env bash
set -e

echo "🔍 Checking Postgres and Redis readiness..."
until nc -z postgres 5432; do echo "⏳ Waiting for Postgres..."; sleep 1; done
until nc -z redis 6379; do echo "⏳ Waiting for Redis..."; sleep 1; done
echo "✅ Postgres and Redis are ready. Applying Alembic migrations..."

alembic upgrade head || { echo "❌ Alembic migration failed!"; exit 1; }

echo "🧩 Starting FastAPI app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
