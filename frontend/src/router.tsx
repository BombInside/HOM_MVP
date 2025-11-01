import { createBrowserRouter, Navigate } from "react-router-dom";
import AdminLayout from "./layouts/AdminLayout";
import AuthLayout from "./layouts/AuthLayout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import RoleEditor from "./pages/Admin/RoleEditor";
import UserManager from "./pages/Admin/UserManager";
import { useAppSelector } from "./app/store";
import AdminBootstrap from "./pages/Admin/AdminBootstrap";

const RequireAuth = ({ children }: { children: JSX.Element }) => {
  const token = useAppSelector((s) => s.auth.accessToken);
  if (!token) return <Navigate to="/login" replace />;
  return children;
};


export const router = createBrowserRouter([
  {
    element: <AdminLayout />,
    children: [
      { path: "/", element: <Navigate to="/dashboard" replace /> },
      { path: "/dashboard", element: <RequireAuth><Dashboard /></RequireAuth> },
      { path: "/machines", element: <RequireAuth><div>Machines TBD</div></RequireAuth> },
      { path: "/admin/roles", element: <RequireAuth><RoleEditor /></RequireAuth> },
      { path: "/admin/users", element: <RequireAuth><UserManager /></RequireAuth> },
    ],
  },
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "/adminpanel/bootstrap", element: <AdminBootstrap /> }, // ✅
    ],
  },
  { path: "*", element: <div className="p-6">Not Found</div> },
]);
