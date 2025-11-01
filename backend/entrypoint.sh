#!/bin/bash
set -e

echo "🚀 Checking Postgres and Redis readiness..."
until pg_isready -h postgres -U hom_user -d hom_db; do
  sleep 1
done
echo "✅ Postgres is ready."

until redis-cli -h redis ping | grep -q PONG; do
  sleep 1
done
echo "✅ Redis is ready."

# ВАЖНО: указываем PYTHONPATH, чтобы Alembic видел 'app'
export PYTHONPATH=/app

echo "📦 Applying Alembic migrations..."
alembic upgrade head || echo "⚠️ Alembic migration failed — proceeding anyway."

echo "🚀 Starting FastAPI app..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
