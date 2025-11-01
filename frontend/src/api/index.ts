import axios from "axios";

/**
 * Нормализация базового URL для API.
 * Поддерживает:
 *  - абсолютный URL в переменной окружения (http://1.2.3.4:8000 или https://api.example.com)
 *  - относительный путь "/api" (будет склеен с window.location.origin)
 *  - fallback по умолчанию:
 *      - в браузере -> `${window.location.origin}/api` (через nginx proxy_pass)
 *      - вне браузера -> "http://localhost:8000"
 */
function resolveBaseURL(): string {
  // 1) приоритет — новая переменная
  const env = (import.meta.env.VITE_API_URL ?? "").toString().trim();

  // 2) совместимость со старой переменной, если вдруг осталась в окружении
  const legacy = (import.meta.env.VITE_API_DOMAIN ?? "").toString().trim();

  const candidate = env || legacy;

  if (candidate) {
    // если начинается с "http://" или "https://" — это абсолютный URL
    if (/^https?:\/\//i.test(candidate)) {
      return stripTrailingSlash(candidate);
    }
    // если начинается с "/" — это относительный путь (например, "/api")
    if (candidate.startsWith("/")) {
      if (typeof window !== "undefined" && window.location?.origin) {
        return stripTrailingSlash(`${window.location.origin}${candidate}`);
      }
    }
    // любой другой случай считаем доменом без схемы — добавим http://
    return stripTrailingSlash(`http://${candidate}`);
  }

  // 3) fallback: через nginx-прокси на /api
  if (typeof window !== "undefined" && window.location?.origin) {
    return `${window.location.origin}/api`;
  }

  // 4) последний fallback: локальный бэкенд
  return "http://localhost:8000";
}

/** Убирает завершающий слэш, чтобы запросы вида api.get("/path") не давали двойной слэш */
function stripTrailingSlash(url: string): string {
  return url.endsWith("/") ? url.slice(0, -1) : url;
}

const api = axios.create({
  baseURL: resolveBaseURL(),
  withCredentials: false,
});

// Подмешиваем Bearer-токен автоматически (если он есть в localStorage)
api.interceptors.request.use((config) => {
  if (config.headers && (config.headers as any).Authorization === "") {
    return config;
  }
  const token = localStorage.getItem("token");
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any)["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

export default api;
