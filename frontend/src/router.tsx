import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "./app/store";
import { fetchCurrentUser } from "./app/slices/authSlice";

import Login from "./pages/Login";
import AdminBootstrap from "./pages/Admin/AdminBootstrap";
import Dashboard from "./pages/Admin/Dashboard";
import RoleEditor from "./pages/Admin/RoleEditor";
import UserManager from "./pages/Admin/UserManager";

// Импорт макетов
import AdminLayout from "./layouts/AdminLayout";
import AuthLayout from "./layouts/AuthLayout"; // Используем AuthLayout для Login, если он существует

// НОВОЕ: Компонент загрузки
const AuthLoading = () => (
    <div className="min-h-screen flex items-center justify-center text-xl text-gray-500">Загрузка...</div>
);

// Защита: наличие токена
function ProtectedRoute({ children }: { children: JSX.Element }) {
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

// Защита: наличие прав администратора
function AdminRoute({ children }: { children: JSX.Element }) {
  const { user, isAuthResolved } = useAppSelector((s) => s.auth);

  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  if (!user?.is_admin) return <Navigate to="/login" replace />;
  return children;
}

function AppInner() {
  const dispatch = useAppDispatch();
  const { accessToken, isAuthResolved } = useAppSelector((s) => s.auth); 

  // тихий автологин по токену
  useEffect(() => {
    if (accessToken && !isAuthResolved) {
      dispatch(fetchCurrentUser());
    }
  }, [accessToken, isAuthResolved, dispatch]); 

  return (
    <Routes>
      
      {/* Публичные маршруты (обернуты в AuthLayout, если он нужен) */}
      <Route path="/login" element={<AuthLayout><Login /></AuthLayout>} />
      <Route path="/adminpanel/bootstrap" element={<AdminBootstrap />} />

      {/* Защищенный маршрут: требуется AdminLayout, ProtectedRoute, AdminRoute */}
      <Route 
        path="/" 
        element={
          <ProtectedRoute>
            <AdminRoute>
              <AdminLayout /> {/* Родительский макет */}
            </AdminRoute>
          </ProtectedRoute>
        }
      >
        {/* Вложенные маршруты для AdminLayout (Dashboard, Roles, Users) */}
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/machines" element={<div className="text-xl">Machines List</div>} />
        <Route path="/admin/roles" element={<RoleEditor />} />
        <Route path="/admin/users" element={<UserManager />} />
        
        {/* Главная страница админки по умолчанию */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Route>

      {/* Перенаправление всех остальных маршрутов на /login */}
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