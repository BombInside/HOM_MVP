# Admin Bootstrap & Roles API

## 1. Purpose
This document describes how to initialize the first administrator and manage user roles and permissions via REST API.  
All endpoints are available only to users with the **admin** role.

---

## 2. Administrator Bootstrap

**Endpoint:** `/adminpanel/bootstrap`

- **GET** — Returns an HTML form to create the very first administrator.  
  Accessible **only until** an admin user exists.
- **POST** — Submits the form with `email` and `password`.  
  Creates:
  - `admin` role (if missing)
  - First user with that role
  - Redirects to `/` and sets cookie `toast=Administrator created`

After an admin is created, all further requests redirect to `/` with message *“Administrator already exists”*.

---

## 3. Role & Permission Editor

| Method | Endpoint | Description |
|---------|-----------|-------------|
| GET | `/adminpanel/roles` | List all roles and their permissions |
| POST | `/adminpanel/roles` | Create a new role |
| PUT | `/adminpanel/roles/{id}` | Update an existing role |
| DELETE | `/adminpanel/roles/{id}` | Delete a role |

Each request requires a valid JWT **Bearer token** with admin privileges.

---

## 4. Example Usage (curl)

```bash
# 1) Login (obtain JWT)
curl -s -X POST https://site.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@site.com","password":"secret"}'

# 2) List roles
curl -s https://site.com/adminpanel/roles \
  -H "Authorization: Bearer <JWT>"

# 3) Create role
curl -s -X POST https://site.com/adminpanel/roles \
  -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"name":"editor","description":"Content editor","permissions":["machines.read","machines.write"]}'

# 4) Update role
curl -s -X PUT https://site.com/adminpanel/roles/3 \
  -H "Authorization: Bearer <JWT>" -H "Content-Type: application/json" \
  -d '{"name":"editor","description":"Advanced editor","permissions":["machines.read"]}'

# 5) Delete role
curl -s -X DELETE https://site.com/adminpanel/roles/3 \
  -H "Authorization: Bearer <JWT>"
```