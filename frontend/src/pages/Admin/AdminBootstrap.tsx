import { useEffect, useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import api from "../../api";

const AdminBootstrap = () => {
  const [loading, setLoading] = useState(true);
  const [exists, setExists] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const nav = useNavigate();

  useEffect(() => {
    const checkAdmin = async () => {
      try {
        const res = await api.get("/adminpanel/bootstrap/status");
        if (res.data.admin_exists) {
          setExists(true);
          setLoading(false);
          // редирект через 2 секунды с сообщением
          setTimeout(() => {
            alert("Администратор уже создан, вы будете перенаправлены на главную страницу");
            nav("/");
          }, 2000);
        } else {
          setExists(false);
          setLoading(false);
        }
      } catch (e: any) {
        setError("Ошибка при проверке статуса администратора");
        setLoading(false);
      }
    };
    checkAdmin();
  }, [nav]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    if (password !== confirm) {
      setError("Пароли не совпадают");
      return;
    }

    try {
      const res = await api.post("/adminpanel/bootstrap", {
        email,
        password,
      });
      setSuccess(res.data?.message || "Администратор создан");
      setTimeout(() => nav("/login"), 2000);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "Ошибка при создании администратора");
    }
  };

  if (loading) {
    return <div className="p-6">Загрузка...</div>;
  }

  if (exists) {
    return (
      <div className="p-6 text-center">
        <p className="text-lg">Администратор уже создан</p>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto mt-10 bg-white dark:bg-gray-800 border rounded shadow p-6">
      <h1 className="text-xl font-semibold mb-4">Создание администратора</h1>

      <form onSubmit={submit} className="flex flex-col gap-3">
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
          className="mt-2 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Создать администратора
        </button>

        {error && <div className="text-red-500 text-sm">{error}</div>}
        {success && <div className="text-green-500 text-sm">{success}</div>}
      </form>
    </div>
  );
};

export default AdminBootstrap;
