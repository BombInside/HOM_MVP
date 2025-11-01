import React, { useEffect, useState } from "react";
import { getHealthStatus } from "../api/health";

/**
 * Компонент панели статусов сервисов.
 * Обновляет данные раз в 60 секунд.
 */
type ServiceState = Record<string, "ok" | "fail" | string>;

const dot = (ok: boolean) => (
  <span
    className={`inline-block w-2.5 h-2.5 rounded-full ${
      ok ? "bg-green-500" : "bg-red-500"
    }`}
  />
);

const ServiceStatus: React.FC = () => {
  const [status, setStatus] = useState<ServiceState | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const data = await getHealthStatus();
      setStatus(data);
    } catch (e) {
      // если не достучались — считаем все fail
      setStatus({ backend: "fail", database: "fail", redis: "fail" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const id = setInterval(fetchStatus, 60_000);
    return () => clearInterval(id);
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-500">Проверка сервисов…</div>;
  }

  if (!status) {
    return <div className="text-sm text-red-600">Не удалось получить статусы</div>;
  }

  return (
    <div className="p-4 border rounded dark:border-gray-700 bg-white dark:bg-gray-900">
      <div className="text-base font-semibold mb-3">Статусы сервисов</div>
      <div className="flex flex-col gap-2 text-sm">
        {Object.entries(status).map(([name, value]) => {
          const ok = value === "ok";
          return (
            <div key={name} className="flex items-center gap-2">
              {dot(ok)}
              <span className="capitalize">{name}</span>
              <span className={`ml-auto font-medium ${ok ? "text-green-600" : "text-red-600"}`}>
                {ok ? "работает" : "ошибка"}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ServiceStatus;
