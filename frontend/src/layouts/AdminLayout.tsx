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