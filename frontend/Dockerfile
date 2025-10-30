# --- Stage 1: Install dependencies ---
FROM node:18-alpine AS deps

WORKDIR /usr/src/app

# Устанавливаем vite и зависимости проекта
COPY package*.json ./
RUN npm install -g vite && npm install

# Копируем код приложения
COPY . .

# --- Stage 2: Runtime container ---
FROM node:18-alpine

WORKDIR /usr/src/app
COPY --from=deps /usr/src/app /usr/src/app

EXPOSE 5173

# Запускаем Vite dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
