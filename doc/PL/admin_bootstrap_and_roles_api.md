# Admin Bootstrap i API ról

## 1. Cel
Dokument opisuje sposób inicjalizacji pierwszego administratora oraz zarządzania rolami i uprawnieniami użytkowników przez REST API.  
Endpointy dostępne są wyłącznie dla użytkowników z rolą **admin**.

---

## 2. Bootstrap administratora

**Endpoint:** `/adminpanel/bootstrap`

- **GET** — Zwraca formularz HTML do utworzenia pierwszego administratora.  
  Dostępny **tylko do momentu**, gdy istnieje administrator.
- **POST** — Wysyła formularz z `email` i `password`.  
  Tworzy:
  - Rolę `admin` (jeśli nie istnieje)
  - Pierwszego użytkownika z tą rolą
  - Przekierowuje na `/` i ustawia cookie `toast=Administrator created`

Po utworzeniu administratora każde kolejne żądanie przekierowuje na `/` z komunikatem „Administrator already exists”.

---

## 3. Edytor ról i uprawnień

| Metoda | Endpoint | Opis |
|---------|-----------|------|
| GET | `/adminpanel/roles` | Lista wszystkich ról i ich uprawnień |
| POST | `/adminpanel/roles` | Tworzy nową rolę |
| PUT | `/adminpanel/roles/{id}` | Aktualizuje istniejącą rolę |
| DELETE | `/adminpanel/roles/{id}` | Usuwa rolę |

Każde żądanie wymaga ważnego tokena JWT **Bearer** z uprawnieniami administratora.

---

## 4. Przykład użycia (curl)

*(Identyczny jak w wersji EN – patrz powyżej.)*
