import Dashboard from "./Dashboard";

export default function AdminPanel() {
  // в будущем можно добавить проверку логина администратора (cookie/JWT)
  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white border-b shadow-sm p-4 flex justify-between items-center">
        <h2 className="text-xl font-semibold text-gray-700">Админ-панель</h2>
        <a
          href="/"
          className="text-sm text-sky-600 hover:underline font-medium"
        >
          Выйти
        </a>
      </header>

      <main className="p-6">
        <Dashboard />
      </main>
    </div>
  );
}
