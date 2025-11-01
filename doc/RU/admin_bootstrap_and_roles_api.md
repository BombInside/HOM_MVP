# Bootstrap администратора и API ролей

## 1. Назначение
Данный документ описывает процесс создания первого администратора и управление ролями / правами пользователей через REST API.  
Эндпоинты доступны только пользователям с ролью **admin**.

---

## 2. Bootstrap администратора

**Эндпоинт:** `/adminpanel/bootstrap`

- **GET** — Возвращает HTML-форму для создания первого администратора.  
  Доступна **только пока** админ не создан.
- **POST** — Принимает `email` и `password`, создаёт:  
  - Роль `admin` (если отсутствует)  
  - Первого пользователя с этой ролью  
  - Делает редирект на `/` и устанавливает cookie `toast=Администратор создан`

После создания администратора все последующие обращения перенаправляются на `/` с сообщением «Администратор уже существует».

---

## 3. Редактор ролей и прав

| Метод | Эндпоинт | Описание |
|--------|-----------|----------|
| GET | `/adminpanel/roles` | Список всех ролей и их прав |
| POST | `/adminpanel/roles` | Создать новую роль |
| PUT | `/adminpanel/roles/{id}` | Обновить роль |
| DELETE | `/adminpanel/roles/{id}` | Удалить роль |

Все запросы требуют действительный JWT-токен (**Bearer**) с правами администратора.

---

## 4. Пример использования (curl)

```bash
# 1) Логин (получить токен)
curl -s -X POST https://site.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@site.com","password":"secret"}'

# 2) Список ролей
curl -s https://site.com/adminpanel/roles \
  -H "Authorization: Bearer <JWT>"

# 3) Создать роль
curl -s -X POST https://site.com/adminpanel/roles \
  -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"name":"editor","description":"Редактор контента","permissions":["machines.read","machines.write"]}'

# 4) Обновить роль
curl -s -X PUT https://site.com/adminpanel/roles/3 \
  -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"name":"editor","description":"Расширенный редактор","permissions":["machines.read"]}'

# 5) Удалить роль
curl -s -X DELETE https://site.com/adminpanel/roles/3 \
  -H "Authorization: Bearer <JWT>"
```