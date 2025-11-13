import React from "react";
import {
    createBrowserRouter,
    RouterProvider,
    Outlet,
    Navigate,
} from "react-router-dom";

import Login from "./pages/Login";
import Dashboard from "./pages/Admin/Dashboard";
import AdminLayout from "./layouts/AdminLayout";
import UserManager from "./pages/Admin/UserManager";
import RoleEditor from "./pages/Admin/RoleEditor";

//import { useAppSelector } from "./app/hooks";
import { selectIsAuthenticated, selectIsAuthResolved } from "./app/slices/authSlice";

/* -------------------------------------------
   ProtectedRoute (✔️ FIXED FOR TS)
-------------------------------------------- */

interface ProtectedRouteProps {
    children: JSX.Element;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
    const isAuthenticated = useAppSelector(selectIsAuthenticated);
    const isAuthResolved = useAppSelector(selectIsAuthResolved);

    if (!isAuthResolved) return <div>Loading...</div>;

    if (!isAuthenticated) return <Navigate to="/login" replace />;

    return children;
};

/* -------------------------------------------
   Layout wrapper to allow nested routing
-------------------------------------------- */

const AdminWrapper: React.FC = () => {
    return (
        <ProtectedRoute>
            <AdminLayout />
        </ProtectedRoute>
    );
};

/* -------------------------------------------
   ROUTER CONFIG
-------------------------------------------- */

const router = createBrowserRouter([
    {
        path: "/login",
        element: <Login />,
    },
    {
        path: "/admin",
        element: <AdminWrapper />,
        children: [
            {
                path: "",
                element: <Dashboard />,
            },
            {
                path: "users",
                element: <UserManager />,
            },
            {
                path: "roles",
                element: <RoleEditor />,
            },
        ],
    },
    {
        path: "*",
        element: <Navigate to="/admin" replace />,
    },
]);

/* -------------------------------------------
   Export Provider
-------------------------------------------- */

export const AppRouter = () => <RouterProvider router={router} />;
