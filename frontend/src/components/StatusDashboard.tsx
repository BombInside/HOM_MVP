import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type Status = "loading" | "online" | "offline";

interface ServiceStatus {
  backend: Status;
  api: Status;
  db: Status;
  graphql: Status;
}

const getStatusColor = (status: Status): string => {
  switch (status) {
    case "online":
      return "bg-green-500";
    case "offline":
      return "bg-red-500";
    default:
      return "bg-yellow-400 animate-pulse";
  }
};

export default function StatusDashboard() {
  const [status, setStatus] = useState<ServiceStatus>({
    backend: "loading",
    api: "loading",
    db: "loading",
    graphql: "loading",
  });

  const [lastUpdate, setLastUpdate] = useState<string>("");
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  async function checkEndpoint(endpoint: string): Promise<Status> {
    try {
      const res = await fetch(endpoint, { method: "GET" });
      if (!res.ok) throw new Error("Failed");
      return "online";
    } catch {
      return "offline";
    }
  }

  async function refreshStatuses() {
    setStatus((s) => ({
      ...s,
      backend: "loading",
      api: "loading",
      db: "loading",
      graphql: "loading",
    }));

    const [backend, api, db, graphql] = await Promise.all([
      checkEndpoint(`${API_URL}/health`),
      checkEndpoint(`${API_URL}/api/ping`),
      checkEndpoint(`${API_URL}/db-check`),
      checkEndpoint(`${API_URL}/graphql`),
    ]);

    setStatus({ backend, api, db, graphql });
    setLastUpdate(new Date().toLocaleTimeString());
  }

  useEffect(() => {
    refreshStatuses();
    const interval = setInterval(refreshStatuses, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 bg-gray-900 text-white rounded-2xl shadow-2xl w-full max-w-xl mx-auto mt-8 border border-gray-700">
      <h2 className="text-2xl font-bold mb-4 text-center">
        🩺 System Health Dashboard
      </h2>
      <div className="grid grid-cols-2 gap-4 text-center">
        <AnimatedService name="Backend" status={status.backend} />
        <AnimatedService name="API" status={status.api} />
        <AnimatedService name="Database" status={status.db} />
        <AnimatedService name="GraphQL" status={status.graphql} />
      </div>
      <p className="text-gray-400 text-xs mt-3 text-center">
        Auto-refresh every 10s — Last update: {lastUpdate || "Loading..."}
      </p>
    </div>
  );
}

function AnimatedService({ name, status }: { name: string; status: Status }) {
  const color = getStatusColor(status);
  const label =
    status === "loading"
      ? "Checking..."
      : status === "online"
      ? "Online ✅"
      : "Offline ❌";

  return (
    <motion.div
      className={`flex flex-col items-center justify-center p-4 bg-gray-800 rounded-xl shadow-md transition-colors duration-500 border ${status === "offline"
          ? "border-red-400"
          : status === "online"
          ? "border-green-400"
          : "border-yellow-300"
        }`}
      animate={{
        scale: status === "loading" ? [1, 1.05, 1] : 1,
        opacity: status === "offline" ? [1, 0.7, 1] : 1,
      }}
      transition={{ duration: 0.6, repeat: status === "loading" ? Infinity : 0 }}
    >
      <div className={`w-3 h-3 rounded-full ${color} mb-2`} />
      <span className="text-base font-semibold">{name}</span>
      <span
        className={`text-xs mt-1 ${status === "offline"
            ? "text-red-300"
            : status === "online"
            ? "text-green-300"
            : "text-yellow-300"
          }`}
      >
        {label}
      </span>
    </motion.div>
  );
}
