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

// НОВОЕ: Компонент загрузки
const AuthLoading = () => (
    <div className="min-h-screen flex items-center justify-center text-xl text-gray-500">Загрузка...</div>
);

// Защита: наличие токена (ПЕРЕИМЕНОВАНО: element -> component)
function ProtectedRoute({ component }: { component: JSX.Element }) {
  const { accessToken, isAuthResolved } = useAppSelector((s) => s.auth);
  const loc = useLocation();

  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }
  return component;
}

// Защита: наличие прав администратора (ПЕРЕИМЕНОВАНО: element -> component)
function AdminRoute({ component }: { component: JSX.Element }) {
  const { user, isAuthResolved } = useAppSelector((s) => s.auth);

  if (!isAuthResolved) {
    return <AuthLoading />;
  }

  // user?.is_admin проверяется только после того, как isAuthResolved === true
  if (!user?.is_admin) return <Navigate to="/login" replace />;
  return component;
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
        element={<ProtectedRoute component={<AdminLayout />} />} 
      >
        {/* Вложенные маршруты, доступные после аутентификации */}
        
        <Route index element={<Navigate to="/dashboard" replace />} />
        
        {/* Dashboard */}
        <Route 
            path="/dashboard" 
            element={<AdminRoute component={<Dashboard />} />} 
        />
        
        {/* Машины (требует AdminRoute) */}
        <Route 
            path="/machines" 
            element={<AdminRoute component={<div className="p-6 text-xl">Machines List (Coming Soon)</div>} />} 
        />
        
        {/* Роли (новый функционал) */}
        <Route 
            path="/admin/roles" 
            element={<AdminRoute component={<RoleEditor />} />} 
        />
        
        {/* Пользователи (требует AdminRoute) */}
        <Route 
            path="/admin/users" 
            element={<AdminRoute component={<UserManager />} />} 
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
```eof

---

## 2. `frontend/src/layouts/AdminLayout.tsx` (Подтверждение)

```typescript:Admin Layout:frontend/src/layouts/AdminLayout.tsx
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import { Outlet } from "react-router-dom";

const AdminLayout = () => {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Topbar />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          <Outlet /> {/* Здесь будут рендериться вложенные маршруты */}
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
```eof

---

## 3. `frontend/src/pages/Admin/Dashboard.tsx` (Подтверждение)

```typescript:Dashboard (удалена Topbar):frontend/src/pages/Admin/Dashboard.tsx
import ServiceStatus from "../../components/ServiceStatus";

const Dashboard = () => {
  return (
    // Удалена Topbar, так как она теперь в AdminLayout
    <div className="text-gray-900 dark:text-white">
      <h1 className="text-2xl font-semibold mb-4">Админ-панель</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Статусы сервисов */}
        <ServiceStatus />

        {/* Заглушки под будущие виджеты */}
        <div className="p-4 border rounded dark:border-gray-700 bg-white dark:bg-gray-900">
          Metrics (coming soon)
        </div>
        <div className="p-4 border rounded dark:border-gray-700 bg-white dark:bg-gray-900">
          Recent activity (coming soon)
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
