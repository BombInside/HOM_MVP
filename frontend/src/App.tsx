import { useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Server,
  Database,
  Network,
  Cloud,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
  X,
  BarChart3,
  Code2,
  Clock,
  Activity,
  RefreshCcw,
} from "lucide-react";

/**
 * CONFIG
 */
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const REFRESH_MS_DEFAULT = 5000; // 5s
const HISTORY_LEN = 40;
const DEGRADED_PING_MS = 800;
const OFFLINE_GRACE_MS = 30000;

type StatusMap = "ok" | "error" | "loading";
type ServiceKey = "backend" | "db" | "redis" | "graphql";

interface HealthData {
  [key: string]: any;
  _ping?: number;
  _ts?: number;
}

type PingPoint = { t: number; v: number | null; ok: boolean };

type ServiceState = {
  status: StatusMap;
  data: HealthData | null;
  history: PingPoint[];
  lastOkAt?: number;
};

const SERVICE_META: Record<
  ServiceKey,
  { label: string; icon: JSX.Element; color: string }
> = {
  backend: {
    label: "Backend API",
    icon: <Server className="w-6 h-6" />,
    color: "sky",
  },
  db: {
    label: "Database",
    icon: <Database className="w-6 h-6" />,
    color: "emerald",
  },
  redis: {
    label: "Redis / Cache",
    icon: <Network className="w-6 h-6" />,
    color: "orange",
  },
  graphql: {
    label: "GraphQL API",
    icon: <Cloud className="w-6 h-6" />,
    color: "fuchsia",
  },
};

const badgeClass = (level: "online" | "degraded" | "offline") => {
  const map: Record<string, string> = {
    online:
      "bg-emerald-100 text-emerald-700 ring-1 ring-inset ring-emerald-200",
    degraded: "bg-amber-100 text-amber-700 ring-1 ring-inset ring-amber-200",
    offline: "bg-rose-100 text-rose-700 ring-1 ring-inset ring-rose-200",
  };
  return `inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-semibold ${map[level]}`;
};

function classifyLevel(s: ServiceState): "online" | "degraded" | "offline" {
  if (s.status === "error") return "offline";
  if (s.status === "loading") return "degraded";

  const ping = s.data?._ping ?? null;
  if (ping === null) return "degraded";
  if (ping >= DEGRADED_PING_MS) return "degraded";
  if (s.lastOkAt && Date.now() - s.lastOkAt > OFFLINE_GRACE_MS) return "offline";
  return "online";
}

function statusIcon(level: "online" | "degraded" | "offline") {
  if (level === "online")
    return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
  if (level === "degraded")
    return <AlertTriangle className="w-4 h-4 text-amber-600" />;
  return <XCircle className="w-4 h-4 text-rose-600" />;
}

function statusText(level: "online" | "degraded" | "offline") {
  if (level === "online") return "Online";
  if (level === "degraded") return "Degraded";
  return "Offline";
}

/**
 * Мини-график
 */
function Sparkline({ points }: { points: PingPoint[] }) {
  const width = 160;
  const height = 40;
  const pad = 4;
  const filtered = points.slice(-HISTORY_LEN);
  const vals = filtered.map((p) => p.v ?? 0);
  const vmin = Math.min(...vals, 0);
  const vmax = Math.max(...vals, 1);

  const x = (i: number) =>
    pad + (i * (width - pad * 2)) / Math.max(filtered.length - 1, 1);
  const y = (v: number) =>
    height - pad - ((v - vmin) / Math.max(vmax - vmin, 1)) * (height - pad * 2);

  const d =
    filtered.length > 0
      ? filtered.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)},${y(p.v ?? 0)}`).join(" ")
      : "";

  const area =
    filtered.length > 1
      ? `${filtered
          .map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)},${y(p.v ?? 0)}`)
          .join(" ")} L ${x(filtered.length - 1)},${height - pad} L ${x(0)},${
          height - pad
        } Z`
      : "";

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-[160px] h-[40px]">
      <path d={area} fill="currentColor" opacity={0.1} />
      <path d={d} fill="none" stroke="currentColor" strokeWidth={2} />
    </svg>
  );
}

/**
 * Основное приложение
 */
export default function App() {
  const [services, setServices] = useState<Record<ServiceKey, ServiceState>>({
    backend: { status: "loading", data: null, history: [] },
    db: { status: "loading", data: null, history: [] },
    redis: { status: "loading", data: null, history: [] },
    graphql: { status: "loading", data: null, history: [] },
  });
  const [refreshMs, setRefreshMs] = useState<number>(REFRESH_MS_DEFAULT);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const poll = async () => {
    setIsRefreshing(true);
    const now = Date.now();
    const timedFetch = async (url: string) => {
      const t0 = performance.now();
      const res = await fetch(url);
      const isJSON = (res.headers.get("content-type") || "").includes("json");
      const json = isJSON ? await res.json() : {};
      const t1 = performance.now();
      return { ok: res.ok, json, ping: Math.round(t1 - t0) };
    };

    const next = structuredClone(services);

    try {
      const r = await timedFetch(`${API_URL}/health`);
      next.backend.status = r.ok ? "ok" : "error";
      next.backend.data = { ...r.json, _ping: r.ping, _ts: now };
      next.backend.history.push({ t: now, v: r.ping, ok: r.ok });
      next.backend.history = next.backend.history.slice(-HISTORY_LEN);
      if (r.ok) next.backend.lastOkAt = now;
    } catch {
      next.backend.status = "error";
    }

    setServices(next);
    setIsRefreshing(false);
  };

  useEffect(() => {
    poll();
  }, []);

  useEffect(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    timerRef.current = setInterval(poll, refreshMs);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [refreshMs]);

  const overall = useMemo(() => {
    const arr = Object.values(services);
    if (arr.some((s) => s.status === "error")) return "offline";
    if (arr.some((s) => s.status !== "ok")) return "degraded";
    return "online";
  }, [services]) as "online" | "degraded" | "offline";

  const overallColor =
    overall === "online"
      ? "text-emerald-600"
      : overall === "degraded"
      ? "text-amber-600"
      : "text-rose-600";

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto max-w-5xl space-y-8"
      >
        <div className="flex items-center gap-3">
          <Activity className={`h-6 w-6 ${overallColor}`} />
          <h1 className="text-2xl font-bold">H.O.M – Real-Time Monitor</h1>
          <div className={badgeClass(overall)}>{statusText(overall)}</div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          {Object.keys(services).map((k) => {
            const key = k as ServiceKey;
            const s = services[key];
            const level = classifyLevel(s);
            const meta = SERVICE_META[key];
            return (
              <motion.div
                key={key}
                whileHover={{ scale: 1.03 }}
                className="rounded-xl border bg-white p-4 shadow-sm"
              >
                <div className="flex justify-between items-center mb-2">
                  <div className={`flex items-center gap-2 text-${meta.color}-600`}>
                    {meta.icon}
                    <span className="font-semibold">{meta.label}</span>
                  </div>
                  <div className={badgeClass(level)}>{statusText(level)}</div>
                </div>
                <div className="text-gray-600 text-sm">
                  Ping: {s.data?._ping ?? "—"} ms
                </div>
                <div className="text-sky-500">
                  <Sparkline points={s.history} />
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>
    </div>
  );
}
