markdown
# API / GraphQL Документация

## REST

### `GET /health`
Проверка живости сервиса. Ответ:
```json
{"status":"ok"}
```

### Аутентификация

#### `POST /auth/login`
Форма (`application/x-www-form-urlencoded`):
- `username` — email
- `password` — пароль

Ответ:
```json
{"access_token":"...", "refresh_token":"...", "token_type":"bearer"}
```

#### `POST /auth/refresh`
Заголовок:
- `X-Refresh-Token: <refresh>`

Ответ:
```json
{"access_token":"...", "refresh_token":"...", "token_type":"bearer"}
```

#### `POST /auth/logout`
Заголовки:
- `Authorization: Bearer <access>`
- `X-Refresh-Token: <refresh>`

Ответ:
```json
{"status":"ok"}
```

## GraphQL

Эндпоинт: `/graphql`

### Авторизация
Передавайте `Authorization: Bearer <access>`.

### Пример запроса
```graphql
query Machines($lineId: Int!) {
  machines(lineId: $lineId) {
    id
    name
  }
}
```

### Пример мутации
```graphql
mutation CreateRepair($input: CreateRepairInput!) {
  createRepair(data: $input) {
    id
    description
    startedAt
  }
}
```
