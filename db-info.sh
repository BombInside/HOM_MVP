#!/usr/bin/env bash
set -e

echo "🔍 Checking Docker and Postgres connection info..."
echo "----------------------------------------------------"

# Проверяем, выполняется ли внутри контейнера
if grep -q docker /proc/1/cgroup 2>/dev/null; then
  echo "📦 Running INSIDE container"
  CONTEXT="container"
else
  echo "🖥️  Running OUTSIDE container (on host)"
  CONTEXT="host"
fi

# Имя контейнера Postgres
PG_CONTAINER=$(docker ps --format '{{.Names}}' | grep -E 'postgres' | head -n 1 || true)

if [ -z "$PG_CONTAINER" ]; then
  echo "❌ No Postgres container found."
  exit 1
fi

echo "🐘 Postgres container: $PG_CONTAINER"

# Получаем переменные окружения Postgres
PG_USER=$(docker exec -i "$PG_CONTAINER" printenv POSTGRES_USER 2>/dev/null || echo "unknown")
PG_PASS=$(docker exec -i "$PG_CONTAINER" printenv POSTGRES_PASSWORD 2>/dev/null || echo "unknown")
PG_DB=$(docker exec -i "$PG_CONTAINER" printenv POSTGRES_DB 2>/dev/null || echo "unknown")
PG_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$PG_CONTAINER" 2>/dev/null || echo "unknown")

# Определяем хост для подключения
if [ "$CONTEXT" = "container" ]; then
  HOST="postgres"
else
  if docker inspect "$PG_CONTAINER" | grep -q '"5432/tcp": {'; then
    HOST="localhost"
  else
    HOST="$PG_IP"
  fi
fi

echo
echo "🧩 Connection details:"
echo "--------------------------------"
echo "Host:       $HOST"
echo "Port:       5432"
echo "Database:   $PG_DB"
echo "User:       $PG_USER"
echo "Password:   $PG_PASS"
echo "Container IP: $PG_IP"
echo "--------------------------------"
echo

CONN_STR="postgresql://${PG_USER}:${PG_PASS}@${HOST}:5432/${PG_DB}"
echo "📋 Connection string:"
echo "$CONN_STR"
echo

# Проверим соединение, если установлен psql
if command -v psql >/dev/null 2>&1; then
  echo "🔗 Testing connection..."
  if PGPASSWORD="$PG_PASS" psql -h "$HOST" -U "$PG_USER" -d "$PG_DB" -c 'SELECT 1;' >/dev/null 2>&1; then
    echo "✅ Connection successful!"
  else
    echo "❌ Connection failed. Try checking docker network or port mapping."
  fi
else
  echo "⚠️  'psql' not installed; skipping connection test."
fi
