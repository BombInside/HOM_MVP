import Topbar from "../components/Topbar";
import { Outlet } from "react-router-dom";

const AuthLayout = () => {
  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <Topbar />
      <main className="max-w-md mx-auto p-6">
        <Outlet />
      </main>
    </div>
  );
};

export default AuthLayout;
