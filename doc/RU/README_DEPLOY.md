markdown
# H.O.M — Руководство по развёртыванию и эксплуатация (FastAPI + PostgreSQL + Redis + GraphQL)

## TL;DR
- Локально: `docker compose up --build` → API `http://localhost:8000`, GraphQL `http://localhost:8000/graphql`, фронт `http://localhost:5173`
- Staging/Prod: используйте готовые образы из GHCR и `docker-compose.stage.yml`
- Токены JWT с JTI и отзывом через Redis, `X-Refresh-Token` для ротации

---

## 1. Конфигурация окружений

### Переменные окружения
| var | пример | назначение |
|---|---|---|
| `APP_ENV` | `dev` \| `staging` \| `prod` | режим работы |
| `DB_URL` | `postgresql+asyncpg://user:pass@postgres:5432/db` | DSN БД |
| `REDIS_URL` | `redis://redis:6379` | Redis для отзыва токенов |
| `JWT_SECRET` | `<32+ символов>` | ключ подписи JWT |
| `JWT_EXPIRE_MIN` | `60` | время жизни access-токена |
| `CORS_ORIGINS` | `http://localhost:5173` | список доменов через запятую |
| `VITE_API_URL` | `http://localhost:8000` | URL API для фронтенда |

> **Важно:** `JWT_SECRET` храните в секретах CI/CD, не коммитьте в репозиторий.

---

## 2. Локальный запуск

```bash
docker compose up --build
# Откроется:
# - API:       http://localhost:8000
# - GraphQL:   http://localhost:8000/graphql
# - Frontend:  http://localhost:5173
```

Проверка статуса:
```bash
curl http://localhost:8000/health
```

---

## 3. Staging

1. Скопируйте `docker-compose.stage.yml` и `stage.env` на сервер (или используйте CI для заливки).
2. В `stage.env` пропишите реальные значения и образы из GHCR:
   ```env
   BACKEND_IMAGE=ghcr.io/ORG/REPO/hom-backend:main
   FRONTEND_IMAGE=ghcr.io/ORG/REPO/hom-frontend:main
   ```
3. Запуск:
   ```bash
   docker compose -f docker-compose.stage.yml --env-file stage.env up -d
   ```

---

## 4. Production (рекомендации)

- Обратный прокси (Caddy/Nginx) с TLS:
  - `api.example.com` → backend:8000
  - `app.example.com` → frontend:5173
- Настройте логирование в JSON, трассировку (OpenTelemetry), метрики `/metrics`
- Бэкап БД и Redis snapshots
- Обновления через blue/green или канареечный деплой

---

## 5. Аутентификация и безопасность

- `POST /auth/login` — формные креды; ответ: `{access_token, refresh_token}`
- `POST /auth/refresh` — заголовок `X-Refresh-Token: <token>`; получает новую пару токенов
- `POST /auth/logout` — заголовки: `Authorization: Bearer <access>`, `X-Refresh-Token: <refresh>`; отзывает оба
- Верификация токена: проверка подписи, срока, blacklist по `jti`

---

## 6. Тестирование

- `pytest`, `pytest-asyncio`, `httpx[http2]`
- Тесткейсы:
  - логин/рефреш/логаут (revocation в Redis)
  - RBAC (403 при нехватке роли)
  - основные GraphQL запросы/мутации со снапшотами

---

## 7. CI/CD (скелет)

- Линтеры/тесты до сборки образов
- Сборка и пуш в GHCR
- SSH на staging-сервер, выкатывание `docker-compose.stage.yml`

---

## 8. Миграции Alembic

**Важно:** не используйте `SQLModel.metadata.create_all` в миграциях.
В `alembic/env.py`:

```python
from sqlmodel import SQLModel
target_metadata = SQLModel.metadata
# context.configure(..., target_metadata=target_metadata, compare_type=True)
```

Первая ревизия:
```bash
alembic revision -m "init"
```
И затем руками опишите таблицы через `op.create_table` и `op.add_column` на основе моделей.

---

## 9. Наблюдаемость

- Стандартный middleware ошибок (пример в `error_middleware.py`), логируйте исключения
- Экспонируйте `/metrics` (Prometheus) и включите трассировку OTEL
- Centralized logs (Loki/ELK), уникальный `request_id`

---

## 10. Чек-лист продакшна

- [ ] Секреты в безопасном хранилище
- [ ] TLS включён, HSTS на прокси
- [ ] Логи и метрики подключены
- [ ] Бэкапы и мониторинг БД/Redis
- [ ] Эндпоинты аутентификации протестированы
```

