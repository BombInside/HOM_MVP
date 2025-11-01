// Унифицированный axios-инстанс для проекта.
// ВАЖНО: публичные запросы (например /adminpanel/bootstrap GET) можно вызвать без токена:
// api.get(url, { headers: { Authorization: "" } })

import axios from "axios";

const baseURL =
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_URL) ||
  (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");

const api = axios.create({
  baseURL,
  withCredentials: false,
});

// Добавляем токен, если он есть в localStorage
api.interceptors.request.use((config) => {
  // если явно передали Authorization: "" — не подставляем токен
  if (config.headers && "Authorization" in config.headers && config.headers.Authorization === "") {
    return config;
  }

  const token = localStorage.getItem("token");
  if (token) {
    config.headers = {
      ...(config.headers || {}),
      Authorization: `Bearer ${token}`,
    };
  }
  return config;
});

export default api;
