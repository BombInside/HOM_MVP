import Topbar from "../../components/Topbar";

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white">
      <Topbar />
      <div className="p-6">
        <h1 className="text-2xl font-semibold mb-4">Админ-панель</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border rounded dark:border-gray-700">Metrics (coming soon)</div>
          <div className="p-4 border rounded dark:border-gray-700">Recent activity (coming soon)</div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
