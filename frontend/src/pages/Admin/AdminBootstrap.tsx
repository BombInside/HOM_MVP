import { useEffect, useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";

/**
 * Страница первичного создания администратора.
 * Отображается только если администратора ещё нет.
 */
const AdminBootstrap = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [exists, setExists] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    (async () => {
      try {
        // Backend возвращает: { ok: true, admin_exists: boolean } или { admin_exists: boolean }
        const { data } = await api.get("/adminpanel/bootstrap");
        const adminExists = !!(data?.admin_exists ?? data?.adminExists);
        if (!isMounted) return;
        setExists(adminExists);
      } catch (e) {
        // Если статус недоступен — всё равно позволим попытаться создать
        setExists(false);
      } finally {
        if (isMounted) setLoading(false);
      }
    })();
    return () => {
      isMounted = false;
    };
  }, [navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (password !== confirm) {
      setError("Пароли не совпадают");
      return;
    }

    try {
      // Backend ожидает: { email, password, confirm_password }
      const { data } = await api.post("/adminpanel/bootstrap", {
        email,
        password,
        confirm_password: password,
      });
      const ok = !!(data?.ok ?? data?.success ?? data?.message);
      if (ok) {
        setSuccess(data?.message || "Администратор успешно создан");
        setTimeout(() => navigate("/login"), 1200);
      } else {
        setError(data?.message || "Ошибка при создании администратора");
      }
    } catch (err: any) {
      const msg =
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        err?.message ||
        "Ошибка при создании администратора";
      setError(msg);
    }
  };

  if (loading) return <div className="p-6 text-center">Загрузка...</div>;

  if (exists)
    return (
      <div className="p-6">
        <div className="max-w-xl mx-auto bg-white dark:bg-gray-800 rounded shadow p-6">
          <h1 className="text-xl font-semibold mb-3">Администратор уже создан</h1>
          <p className="mb-4 text-sm text-gray-600 dark:text-gray-300">
            Перейдите на страницу входа, чтобы авторизоваться.
          </p>
          <button
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
            onClick={() => navigate("/login")}
          >
            Перейти к входу
          </button>
        </div>
      </div>
    );

  return (
    <div className="p-6">
      <div className="max-w-xl mx-auto bg-white dark:bg-gray-800 rounded shadow p-6">
        <h1 className="text-xl font-semibold mb-4">Создание администратора</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <input
            type="email"
            placeholder="Email"
            value={email}
            required
            onChange={(e) => setEmail(e.target.value)}
            className="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
          />
          <input
            type="password"
            placeholder="Пароль"
            value={password}
            required
            onChange={(e) => setPassword(e.target.value)}
            className="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
          />
          <input
            type="password"
            placeholder="Подтвердите пароль"
            value={confirm}
            required
            onChange={(e) => setConfirm(e.target.value)}
            className="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
          />

          <button
            type="submit"
            className="mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
          >
            Создать администратора
          </button>

          {error && <div className="text-red-500 text-sm text-center">{error}</div>}
          {success && <div className="text-green-500 text-sm text-center">{success}</div>}
        </form>
      </div>
    </div>
  );
};

export default AdminBootstrap;
