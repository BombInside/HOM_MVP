import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import { useEffect, ReactNode } from "react";
import { useAppDispatch, useAppSelector } from "./app/store";
import { fetchCurrentUser } from "./app/slices/authSlice";

import Login from "./pages/Login";
import AdminBootstrap from "./pages/Admin/AdminBootstrap";
import Dashboard from "./pages/Admin/Dashboard";
import RoleEditor from "./pages/Admin/RoleEditor";
import UserManager from "./pages/Admin/UserManager";

import AdminLayout from "./layouts/AdminLayout";
import AuthLayout from "./layouts/AuthLayout";

// Экран загрузки авторизации
const AuthLoading = () => (
  <div className="min-h-screen flex items-center justify-center text-xl text-gray-500">
    Загрузка...
  </div>
);

// ===== Защищённые маршруты =====

type GuardProps = {
  children: JSX.Element;
};

// Проверка: пользователь залогинен (по accessToken)
function ProtectedRoute({ children }: GuardProps) {
  const { accessToken, isAuthResolved } = useAppSelector((s) => s.auth);
  const loc = useLocation();

  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }

  return children;
}

// Проверка: пользователь — админ
function AdminRoute({ children }: GuardProps) {
  const { user, isAuthResolved } = useAppSelector((s) => s.auth);

  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  if (!user?.is_admin) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AppInner() {
  const dispatch = useAppDispatch();
  const { accessToken, isAuthResolved } = useAppSelector((s) => s.auth);

  // Тихий автологин по токену при загрузке приложения
  useEffect(() => {
    if (accessToken && !isAuthResolved) {
      dispatch(fetchCurrentUser());
    }
  }, [accessToken, isAuthResolved, dispatch]);

  return (
    <Routes>
      {/* Публичные маршруты */}
      <Route
        path="/login"
        element={
          <AuthLayout>
            <Login />
          </AuthLayout>
        }
      />
      {/* Bootstrap админа — публичный, но одноразовый сценарий */}
      <Route path="/adminpanel/bootstrap" element={<AdminBootstrap />} />

      {/* Защищённый корневой маршрут с общим AdminLayout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        {/* Редирект с "/" на "/dashboard" */}
        <Route index element={<Navigate to="/dashboard" replace />} />

        {/* Dashboard (любой залогиненный пользователь) */}
        <Route
          path="/dashboard"
          element={
            <AdminRoute>
              <Dashboard />
            </AdminRoute>
          }
        />

        {/* Машины (пока заглушка, доступ только админу) */}
        <Route
          path="/machines"
          element={
            <AdminRoute>
              <div className="p-6 text-xl">Machines List (Coming Soon)</div>
            </AdminRoute>
          }
        />

        {/* Роли (только админ) */}
        <Route
          path="/admin/roles"
          element={
            <AdminRoute>
              <RoleEditor />
            </AdminRoute>
          }
        />

        {/* Пользователи (только админ) */}
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <UserManager />
            </AdminRoute>
          }
        />
      </Route>

      {/* Фолбэк: всё неизвестное отправляем на /login */}
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
