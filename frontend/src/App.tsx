import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Server,
  Database,
  Network,
  Cloud,
  CheckCircle2,
  XCircle,
  Loader2,
  X,
  BarChart3,
  Code2,
  Clock,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

type StatusMap = "ok" | "error" | "loading";
type ServiceKey = "backend" | "db" | "redis" | "graphql";

interface HealthData {
  [key: string]: any;
  _ping?: number;
}

export default function App() {
  const [status, setStatus] = useState<Record<ServiceKey, StatusMap>>({
    backend: "loading",
    db: "loading",
    redis: "loading",
    graphql: "loading",
  });

  const [responses, setResponses] = useState<Record<ServiceKey, HealthData>>({
    backend: {},
    db: {},
    redis: {},
    graphql: {},
  });

  const [selected, setSelected] = useState<ServiceKey | null>(null);
  const [activeTab, setActiveTab] = useState<"raw" | "formatted" | "ping">("raw");

  useEffect(() => {
    const checkStatuses = async () => {
      const newStatus = { ...status };
      const newResponses = { ...responses };

      const timedFetch = async (key: ServiceKey, url: string, options?: any) => {
        const start = performance.now();
        const res = await fetch(url, options);
        const json = await res.json();
        const end = performance.now();
        return { json, time: Math.round(end - start) };
      };

      try {
        const backendData = await timedFetch("backend", `${API_URL}/health`);
        newResponses.backend = { ...backendData.json, _ping: backendData.time };
        newStatus.backend = backendData.json?.status === "ok" ? "ok" : "error";
        newStatus.db = backendData.json?.db_status === "ok" ? "ok" : "error";
      } catch {
        newStatus.backend = "error";
        newStatus.db = "error";
      }

      try {
        const redisData = await timedFetch("redis", `${API_URL}/redis-health`);
        newResponses.redis = { ...redisData.json, _ping: redisData.time };
        newStatus.redis = redisData.json?.status === "ok" ? "ok" : "error";
      } catch {
        newStatus.redis = "error";
      }

      try {
        const gqlData = await timedFetch("graphql", `${API_URL}/graphql`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: "{ __typename }" }),
        });
        newResponses.graphql = { ...gqlData.json, _ping: gqlData.time };
        newStatus.graphql = gqlData.json?.data ? "ok" : "error";
      } catch {
        newStatus.graphql = "error";
      }

      setStatus(newStatus);
      setResponses(newResponses);
    };

    checkStatuses();
    const interval = setInterval(checkStatuses, 10000);
    return () => clearInterval(interval);
  }, []);

  const icons: Record<ServiceKey, JSX.Element> = {
    backend: <Server className="w-8 h-8 text-gray-700" />,
    db: <Database className="w-8 h-8 text-gray-700" />,
    redis: <Network className="w-8 h-8 text-gray-700" />,
    graphql: <Cloud className="w-8 h-8 text-gray-700" />,
  };

  const labels: Record<ServiceKey, string> = {
    backend: "Backend API",
    db: "Database",
    redis: "Redis / Cache",
    graphql: "GraphQL API",
  };

  const getStatusIcon = (value: StatusMap) => {
    if (value === "ok") return <CheckCircle2 className="text-green-500 w-5 h-5" />;
    if (value === "error") return <XCircle className="text-red-500 w-5 h-5" />;
    return <Loader2 className="text-gray-400 w-5 h-5 animate-spin" />;
  };

  const getStatusColor = (value: StatusMap) => {
    if (value === "ok") return "text-green-600";
    if (value === "error") return "text-red-600";
    return "text-gray-500";
  };

  const StatusCard = ({ name, value }: { name: ServiceKey; value: StatusMap }) => {
    const isSelected = selected === name;

    return (
      <motion.div
        onClick={() => {
          setSelected(name);
          setActiveTab("raw");
        }}
        whileHover={{ scale: 1.05 }}
        animate={{
          boxShadow: isSelected
            ? "0px 0px 25px rgba(56, 189, 248, 0.8)"
            : "0px 0px 8px rgba(0,0,0,0.05)",
        }}
        transition={{ duration: 0.3 }}
        className={`cursor-pointer select-none p-6 bg-white rounded-2xl border flex flex-col items-center justify-center gap-3 transition-all relative ${
          isSelected
            ? "border-sky-400 animate-pulse-glow"
            : "border-gray-100 hover:border-sky-200"
        }`}
      >
        {icons[name]}
        <div className="text-sm font-medium text-gray-800">{labels[name]}</div>
        <div className="flex items-center gap-2">
          {getStatusIcon(value)}
          <span className={`text-sm font-mono ${getStatusColor(value)}`}>{value}</span>
        </div>
      </motion.div>
    );
  };

  const TabButton = ({
    icon: Icon,
    label,
    value,
  }: {
    icon: any;
    label: string;
    value: "raw" | "formatted" | "ping";
  }) => (
    <button
      onClick={() => setActiveTab(value)}
      className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
        activeTab === value
          ? "bg-sky-100 text-sky-700"
          : "text-gray-500 hover:text-gray-700"
      }`}
    >
      <Icon size={16} />
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-8">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="max-w-4xl mx-auto space-y-10"
      >
        <header className="flex items-center justify-between border-b pb-4">
          <h1 className="text-3xl font-bold">H.O.M – Service Monitor</h1>
        </header>

        <section className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <StatusCard name="backend" value={status.backend} />
          <StatusCard name="db" value={status.db} />
          <StatusCard name="redis" value={status.redis} />
          <StatusCard name="graphql" value={status.graphql} />
        </section>

        <footer className="pt-6 text-center text-gray-500 text-sm">
          Auto-refresh every 10s • Click card for details
        </footer>
      </motion.div>

      {/* 💬 Modal */}
      <AnimatePresence>
        {selected && (
          <motion.div
            className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-white rounded-2xl shadow-2xl p-6 max-w-3xl w-full relative"
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              transition={{ duration: 0.25, ease: "easeOut" }}
            >
              <button
                onClick={() => setSelected(null)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X size={22} />
              </button>
              <div className="flex items-center gap-3 mb-4">
                {icons[selected]}
                <h2 className="text-xl font-semibold capitalize">
                  {labels[selected]} – API Response
                </h2>
              </div>

              {/* Tabs */}
              <div className="flex gap-3 mb-4 border-b pb-2">
                <TabButton icon={Code2} label="Raw JSON" value="raw" />
                <TabButton icon={BarChart3} label="Formatted" value="formatted" />
                <TabButton icon={Clock} label="Ping Info" value="ping" />
              </div>

              <div className="bg-gray-100 p-4 rounded-xl overflow-x-auto max-h-[400px]">
                {activeTab === "raw" && (
                  <pre className="text-xs font-mono text-gray-700">
                    {JSON.stringify(responses[selected], null, 2)}
                  </pre>
                )}
                {activeTab === "formatted" && (
                  <div className="space-y-2 text-sm text-gray-800">
                    {Object.entries(responses[selected] || {}).map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-gray-200 pb-1">
                        <span className="font-medium">{k}</span>
                        <span className="text-gray-600">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
                {activeTab === "ping" && (
                  <div className="text-sm text-gray-700">
                    ⏱ Response Time:{" "}
                    <span className="font-bold text-sky-600">
                      {responses[selected]?._ping ?? "—"} ms
                    </span>
                    <p className="text-xs text-gray-500 mt-1">
                      Measured via fetch() round-trip timing
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`
        @keyframes glow {
          0%, 100% { box-shadow: 0 0 20px rgba(56, 189, 248, 0.5); }
          50% { box-shadow: 0 0 35px rgba(56, 189, 248, 0.9); }
        }
        .animate-pulse-glow {
          animation: glow 1.8s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
