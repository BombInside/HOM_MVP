import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useAppSelector, useAppDispatch } from "./app/store";
import { useEffect } from "react";
import { fetchCurrentUser } from "./app/slices/authSlice";

import Login from "./pages/Login";
import AdminBootstrap from "./pages/Admin/AdminBootstrap";
import Dashboard from "./pages/Admin/Dashboard";

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { accessToken, user } = useAppSelector((s) => s.auth);
  if (!accessToken) return <Navigate to="/login" replace />;
  if (user && !user.is_admin) return <Navigate to="/login" replace />;
  return children;
}

const AppRouter = () => {
  const dispatch = useAppDispatch();
  const { accessToken, user } = useAppSelector((s) => s.auth);

  useEffect(() => {
    if (accessToken && !user) {
      dispatch(fetchCurrentUser());
    }
  }, [accessToken, user, dispatch]);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/adminpanel/bootstrap" element={<AdminBootstrap />} />
        <Route
          path="/adminpanel"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </Router>
  );
};

export default AppRouter;
