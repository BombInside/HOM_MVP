import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useAppDispatch, useAppSelector } from "./app/store";
import { fetchCurrentUser } from "./app/slices/authSlice";

import Login from "./pages/Login";
import AdminBootstrap from "./pages/Admin/AdminBootstrap";
import Dashboard from "./pages/Admin/Dashboard";

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { accessToken } = useAppSelector((s) => s.auth);
  const loc = useLocation();
  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: loc.pathname }} />;
  }
  return children;
}

function AdminRoute({ children }: { children: JSX.Element }) {
  const { user } = useAppSelector((s) => s.auth);
  if (!user?.is_admin) return <Navigate to="/login" replace />;
  return children;
}

function AppInner() {
  const dispatch = useAppDispatch();
  const { accessToken, user } = useAppSelector((s) => s.auth);

  // тихий автологин по токену
  useEffect(() => {
    if (accessToken && !user) {
      dispatch(fetchCurrentUser());
    }
  }, [accessToken, user, dispatch]);

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
