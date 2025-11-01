import { useEffect, useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";  

/**
 * Страница первичного создания администратора.
 * Отображается только если администратора ещё нет.
 * После успешного создания — редирект на страницу входа.
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
    // Проверяем, существует ли администратор
    const checkStatus = async () => {
      try {
        const res = await api.get("/adminpanel/bootstrap/status");
        if (res.data?.admin_exists) {
          setExists(true);
          setLoading(false);
          setTimeout(() => {
            alert("Администратор уже создан. Вы будете перенаправлены на главную страницу.");
            navigate("/");
          }, 2000);
        } else {
          setExists(false);
          setLoading(false);
        }
      } catch {
        setError("Ошибка при проверке статуса администратора");
        setLoading(false);
      }
    };
    checkStatus();
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
      const res = await api.post("/adminpanel/bootstrap", { email, password });
      setSuccess(res.data?.message || "Администратор успешно создан");
      setTimeout(() => navigate("/login"), 1500);
    } catch (err: any) {
      const msg = err?.response?.data?.detail || "Ошибка при создании администратора";
      setError(msg);
    }
  };

  if (loading) return <div className="p-6 text-center">Загрузка...</div>;

  if (exists)
    return (
      <div className="p-6 text-center">
        <p className="text-lg">Администратор уже создан</p>
      </div>
    );

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-xl p-8 w-full max-w-md">
        <h1 className="text-2xl font-semibold mb-6 text-center">Создание администратора</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
