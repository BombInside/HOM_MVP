import { FormEvent, useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../app/store";
import { login } from "../app/slices/authSlice";

const Login = () => {
  const dispatch = useAppDispatch();
  const nav = useNavigate();
  const loc = useLocation();
  const { loading, error } = useAppSelector((s) => s.auth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    // Вызываем thunk с объектом payload.
    const res = await dispatch(login({ email, password })); 
    // ИСПРАВЛЕНИЕ: Используем корректный тип res.
    if (res.meta.requestStatus === "fulfilled") { 
      const to = (loc.state as any)?.from || "/adminpanel";
      nav(to);
    }
  };

  return (
    <div className="min-h-screen flex items-start md:items-center justify-center bg-gray-100 dark:bg-gray-900 pt-10 md:pt-0">
      <div className="w-full max-w-lg bg-white dark:bg-gray-800 rounded-xl shadow p-6">
        <h1 className="text-xl font-semibold mb-4">Login</h1>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <input
            type="email"
            placeholder="Email"
            className="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            className="px-3 py-2 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? "..." : "Sign in"}
          </button>
          {error && <div className="text-red-500 text-sm">Login failed</div>}
        </form>
      </div>
    </div>
  );
};

export default Login;