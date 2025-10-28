# ----------------------------------------------------
# EN: Stage 1: Build Stage (Dependency compilation)
# RU: Этап 1: Сборка (Компиляция зависимостей)
# ----------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# EN: Install tools required ONLY for compilation (e.g., for psycopg/asyncpg)
# RU: Устанавливаем инструменты, необходимые ТОЛЬКО для компиляции
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# ----------------------------------------------------
# EN: Stage 2: Final Stage (Runtime image)
# RU: Этап 2: Финальный образ (для запуска)
# ----------------------------------------------------
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# EN: Install necessary runtime dependencies
# RU: Устанавливаем необходимые runtime зависимости
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# EN: Copy compiled Python packages from the builder stage
# RU: Копируем скомпилированные пакеты Python с этапа сборки
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# EN: Copy application code and configs
# RU: Копируем код приложения и конфигурации
COPY app ./app
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY requirements.txt ./requirements.txt

# EN: Command to run bootstrap, migration, and start the Uvicorn server
# RU: Команда для запуска bootstrap, миграции и старта сервера Uvicorn
CMD bash -lc "python -m app.bootstrap && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"