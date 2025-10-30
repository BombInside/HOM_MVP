# ==============================
# ⚡ FRONTEND DOCKERFILE
# ==============================

# 1️⃣ Базовый образ
FROM node:20-alpine AS build

# 2️⃣ Рабочая директория
WORKDIR /app

# 3️⃣ Копируем package.json и package-lock.json
COPY package*.json ./

# 4️⃣ Устанавливаем зависимости, включая framer-motion
RUN npm install --legacy-peer-deps && \
    npm install framer-motion

# 5️⃣ Копируем исходники проекта
COPY . .

# 6️⃣ Запускаем dev-сервер через Vite
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
