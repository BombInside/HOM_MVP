import api from "./index";

/**
 * Получение статусов сервисов с backend.
 * Возвращает объект вида:
 * { backend: "ok"|"fail", database: "ok"|"fail", redis: "ok"|"fail" }
 */
export async function getHealthStatus(): Promise<Record<string, string>> {
  const res = await api.get("/health/");
  return res.data;
}
