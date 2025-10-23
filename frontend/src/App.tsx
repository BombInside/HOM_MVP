import { useEffect, useState } from "react";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
export default function App() {
  const [health, setHealth] = useState<any>(null);
  useEffect(() => { fetch(`${API_URL}/health`).then(r => r.json()).then(setHealth).catch(console.error); }, []);
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">H.O.M – MVP</h1>
          <span className="text-sm">Backend health: {health?.status ?? "unknown"}</span>
        </header>
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-white rounded-2xl shadow">
            <h2 className="font-semibold mb-2">Auth</h2>
            <p className="text-sm text-gray-600">Эндпоинты: <code>/auth/login</code>, <code>/auth/refresh</code></p>
          </div>
          <div className="p-4 bg-white rounded-2xl shadow">
            <h2 className="font-semibold mb-2">GraphQL</h2>
            <p className="text-sm text-gray-600">Запросы: <code>lines</code>, <code>machines</code> на <code>/graphql</code></p>
          </div>
        </section>
      </div>
    </div>
  );
}
