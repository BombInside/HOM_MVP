FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные пакеты
RUN apt-get update && apt-get install -y netcat-traditional dos2unix && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем весь backend код
COPY . /app

# 💡 Копируем шаблон Alembic script.py.mako из установленного пакета
RUN mkdir -p /app/alembic && \
    cp $(python -c "import alembic, os; print(os.path.join(os.path.dirname(alembic.__file__), 'script.py.mako'))") /app/alembic/script.py.mako || true

# Преобразуем entrypoint в UNIX-формат
RUN chmod +x /app/entrypoint.sh && dos2unix /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
