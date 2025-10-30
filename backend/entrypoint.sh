#!/bin/sh
set -e

echo "🔍 Checking Postgres and Redis readiness..."

# Ждём Postgres
until nc -z ${POSTGRES_HOST:-postgres} 5432; do
  echo "⏳ Waiting for Postgres..."
  sleep 1
done
echo "✅ Postgres is ready!"

# Ждём Redis
until nc -z ${REDIS_HOST:-redis} 6379; do
  echo "⏳ Waiting for Redis..."
  sleep 1
done
echo "✅ Redis is ready!"

echo "🚀 Postgres and Redis are ready. Applying Alembic migrations..."

# 💡 Автоматический merge всех heads (если есть более одного)
HEADS_COUNT=$(alembic heads | grep -c "(head)" || true)
if [ "$HEADS_COUNT" -gt 1 ]; then
  echo "⚙️  Multiple Alembic heads detected. Merging..."
  alembic merge heads -m "auto merge heads"
fi

# ✅ Применяем миграции
alembic upgrade head || {
  echo "❌ Alembic migration failed!"
  exit 1
}

echo "✅ Database migration complete!"
echo "🧩 Starting FastAPI app..."

# 🚀 Запуск FastAPI
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
