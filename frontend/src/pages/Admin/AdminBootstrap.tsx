import { useEffect, useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";

/**
 * Страница первичного создания администратора.
 * Публичная: должна работать без токена.
 */
const AdminBootstrap = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [exists, setExists] = useState<boolean | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        // ВАЖНО: без Authorization — публичный запрос
        const { data } = await api.get("/adminpanel/bootstrap", {
          headers: { Authorization: "" },
        });
        if (!mounted) return;
        setExists(Boolean(data?.admin_exists));
      } catch {
        if (mounted) setExists(false);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (password !== confirm) {
      setError("Пароли не совпадают");
      return;
    }

    try {
      const { data } = await api.post("/adminpanel/bootstrap", {
        email,
        password,
        confirm_password: password,
      });
      if (data?.ok || data?.success) {
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

  if (exists === true)
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
        <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow p-6">
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
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
      <div className="w-full max-w-md bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h1 className="text-xl font-semibold mb-4 text-center">Создание администратора</h1>
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
