import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, Outlet } from "react-router-dom";
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
import AuthLayout from "./layouts/AuthLayout";

// Компонент загрузки
const AuthLoading = () => (
    <div className="min-h-screen flex items-center justify-center text-xl text-gray-500">Загрузка...</div>
);

// Защита: наличие токена (ПЕРЕИМЕНОВАНО: component -> componentToRender)
function ProtectedRoute({ componentToRender }: { componentToRender: JSX.Element }) {
  const { accessToken, isAuthResolved } = useAppSelector((s) => s.auth);
  const loc = useLocation();

  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }
  return componentToRender;
}

// Защита: наличие прав администратора (ПЕРЕИМЕНОВАНО: component -> componentToRender)
function AdminRoute({ componentToRender }: { componentToRender: JSX.Element }) {
  const { user, isAuthResolved } = useAppSelector((s) => s.auth);

  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  // user?.is_admin проверяется только после того, как isAuthResolved === true
  if (!user?.is_admin) return <Navigate to="/login" replace />;
  return componentToRender;
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
      
      {/* Публичные маршруты */}
      <Route path="/login" element={<AuthLayout><Login /></AuthLayout>} />
      <Route path="/adminpanel/bootstrap" element={<AdminBootstrap />} />

      {/* Родительский защищенный маршрут. Использует AdminLayout (с Sidebar) как обертку для всех дочерних элементов. */}
      <Route 
        path="/" 
        element={<ProtectedRoute componentToRender={<AdminLayout />} />} 
      >
        
        {/* Вложенные маршруты, доступные после аутентификации */}
        
        <Route index element={<Navigate to="/dashboard" replace />} />
        
        {/* Dashboard */}
        <Route 
            path="/dashboard" 
            element={<AdminRoute componentToRender={<Dashboard />} />} 
        />
        
        {/* Машины (требует AdminRoute) */}
        <Route 
            path="/machines" 
            element={<AdminRoute componentToRender={<div className="p-6 text-xl">Machines List (Coming Soon)</div>} />} 
        />
        
        {/* Роли (новый функционал) */}
        <Route 
            path="/admin/roles" 
            element={<AdminRoute componentToRender={<RoleEditor />} />} 
        />
        
        {/* Пользователи (требует AdminRoute) */}
        <Route 
            path="/admin/users" 
            element={<AdminRoute componentToRender={<UserManager />} />} 
        />
        
      </Route>

      {/* Перенаправление всех остальных маршрутов на /login, если не аутентифицирован */}
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