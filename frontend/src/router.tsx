import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "./app/store";
import { fetchCurrentUser } from "./app/slices/authSlice";

import Login from "./pages/Login";
import AdminBootstrap from "./pages/Admin/AdminBootstrap";
import Dashboard from "./pages/Admin/Dashboard";

// НОВОЕ: Компонент загрузки
const AuthLoading = () => (
    <div className="min-h-screen flex items-center justify-center text-xl text-gray-500">Загрузка...</div>
);

function ProtectedRoute({ children }: { children: JSX.Element }) {
  // ИЗМЕНЕНО: используем isAuthResolved
  const { accessToken, isAuthResolved } = useAppSelector((s) => s.auth);
  const loc = useLocation();

  // НОВОЕ: Ждем разрешения статуса, чтобы избежать гонки
  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }
  return children;
}

function AdminRoute({ children }: { children: JSX.Element }) {
  // ИЗМЕНЕНО: используем isAuthResolved
  const { user, isAuthResolved } = useAppSelector((s) => s.auth);

  // НОВОЕ: Ждем разрешения статуса, чтобы избежать гонки
  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  // Теперь эта проверка сработает только после загрузки объекта user
  if (!user?.is_admin) return <Navigate to="/login" replace />;
  return children;
}

function AppInner() {
  const dispatch = useAppDispatch();
  // ИЗМЕНЕНО: используем isAuthResolved
  const { accessToken, isAuthResolved } = useAppSelector((s) => s.auth); 

  // тихий автологин по токену
  useEffect(() => {
    // ИЗМЕНЕНО: Запускаем только если есть токен и статус не разрешен
    if (accessToken && !isAuthResolved) {
      dispatch(fetchCurrentUser());
    }
  }, [accessToken, isAuthResolved, dispatch]); // ИЗМЕНЕНО: Зависимость от isAuthResolved

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      {/* bootstrap публичный */}
      <Route path="/adminpanel/bootstrap" element={<AdminBootstrap />} />
      {/* админ только для авторизованных и is_admin */}
      <Route
        path="/adminpanel"
        element={
          <ProtectedRoute>
            <AdminRoute>
              <Dashboard />
            </AdminRoute>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default function AppRouter() {
  return (
    <Router>
      <AppInner />
    </Router>
  );
}