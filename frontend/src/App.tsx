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
  RefreshCcw,
  X,
  Activity,
  BarChart3,
  Code2,
  Clock,
} from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const REFRESH_MS_DEFAULT = 5000;
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
  backend: { label: "Backend API", icon: <Server className="w-6 h-6" />, color: "sky" },
  db: { label: "Database", icon: <Database className="w-6 h-6" />, color: "emerald" },
  redis: { label: "Redis / Cache", icon: <Network className="w-6 h-6" />, color: "orange" },
  graphql: { label: "GraphQL API", icon: <Cloud className="w-6 h-6" />, color: "fuchsia" },
};

const badgeClass = (level: "online" | "degraded" | "offline") => {
  const map: Record<string, string> = {
    online: "bg-emerald-100 text-emerald-700 ring-1 ring-inset ring-emerald-200",
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
  if (level === "online") return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
  if (level === "degraded") return <AlertTriangle className="w-4 h-4 text-amber-600" />;
  return <XCircle className="w-4 h-4 text-rose-600" />;
}

function statusText(level: "online" | "degraded" | "offline") {
  if (level === "online") return "Online";
  if (level === "degraded") return "Degraded";
  return "Offline";
}

function Sparkline({ points }: { points: PingPoint[] }) {
  const width = 160;
  const height = 40;
  const pad = 4;
  const filtered = points.slice(-HISTORY_LEN);
  const vals = filtered.map((p) => p.v ?? 0);
  const vmin = Math.min(...vals, 0);
  const vmax = Math.max(...vals, 1);
  const x = (i: number) => pad + (i * (width - pad * 2)) / Math.max(filtered.length - 1, 1);
  const y = (v: number) =>
    height - pad - ((v - vmin) / Math.max(vmax - vmin, 1)) * (height - pad * 2);
  const d =
    filtered.length > 0
      ? filtered.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)},${y(p.v ?? 0)}`).join(" ")
      : "";
  const area =
    filtered.length > 1
      ? `${filtered.map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)},${y(p.v ?? 0)}`).join(" ")} 
        L ${x(filtered.length - 1)},${height - pad} L ${x(0)},${height - pad} Z`
      : "";
  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-[160px] h-[40px]" aria-hidden>
      <path d={area} fill="currentColor" opacity={0.1} />
      <path d={d} fill="none" stroke="currentColor" strokeWidth={2} />
    </svg>
  );
}

export default function App() {
  const [services, setServices] = useState<Record<ServiceKey, ServiceState>>({
    backend: { status: "loading", data: null, history: [] },
    db: { status: "loading", data: null, history: [] },
    redis: { status: "loading", data: null, history: [] },
    graphql: { status: "loading", data: null, history: [] },
  });
  const [selected, setSelected] = useState<ServiceKey | null>(null);
  const [refreshMs, setRefreshMs] = useState<number>(REFRESH_MS_DEFAULT);
  const timerRef = useRef<number | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const poll = async () => {
    setIsRefreshing(true);
    const timedFetch = async (url: string, init?: RequestInit) => {
      const t0 = performance.now();
      const res = await fetch(url, init);
      const json = await res.json().catch(() => ({}));
      const t1 = performance.now();
      return { ok: res.ok, json, ping: Math.round(t1 - t0) };
    };

    const next = structuredClone(services);
    const now = Date.now();

    // --- Основной health ---
    try {
      const r = await timedFetch(`${API_URL}/health`);
      const ok = r.ok && r.json?.status === "ok";
      next.backend.status = ok ? "ok" : "error";
      next.backend.data = { ...r.json, _ping: r.ping, _ts: now };
      next.backend.history = [
        ...next.backend.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: ok ? r.ping : null, ok },
      ];
      if (ok) next.backend.lastOkAt = now;

      const dbOk = r.json?.db_status === "ok";
      next.db.status = dbOk ? "ok" : "error";
      next.db.data = { status: dbOk ? "ok" : "error", _ping: r.ping, _ts: now };
      next.db.history = [
        ...next.db.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: dbOk ? r.ping : null, ok: dbOk },
      ];
      if (dbOk) next.db.lastOkAt = now;

      const redisOk = r.json?.redis_status === "ok";
      next.redis.status = redisOk ? "ok" : "error";
      next.redis.data = { status: redisOk ? "ok" : "error", _ping: r.ping, _ts: now };
      next.redis.history = [
        ...next.redis.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: redisOk ? r.ping : null, ok: redisOk },
      ];
      if (redisOk) next.redis.lastOkAt = now;
    } catch {
      ["backend", "db", "redis"].forEach((k) => {
        next[k as ServiceKey].status = "error";
        next[k as ServiceKey].history.push({ t: now, v: null, ok: false });
      });
    }

    // --- GraphQL ---
    try {
      const r = await timedFetch(`${API_URL}/graphql`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: "{ __typename }" }),
      });
      const ok = r.ok && !!r.json?.data;
      next.graphql.status = ok ? "ok" : "error";
      next.graphql.data = { ...r.json, _ping: r.ping, _ts: now };
      next.graphql.history = [
        ...next.graphql.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: ok ? r.ping : null, ok },
      ];
      if (ok) next.graphql.lastOkAt = now;
    } catch {
      next.graphql.status = "error";
      next.graphql.history.push({ t: now, v: null, ok: false });
    }

    setServices(next);
    setIsRefreshing(false);
  };

  useEffect(() => {
    poll();
  }, []);

  useEffect(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = window.setInterval(poll, refreshMs) as unknown as number;
    return () => timerRef.current && clearInterval(timerRef.current);
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
        className="mx-auto max-w-6xl space-y-8"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className={`h-6 w-6 ${overallColor}`} />
            <h1 className="text-2xl font-bold">H.O.M – Real-Time Monitor</h1>
            <div className={badgeClass(overall)}>{statusText(overall)}</div>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-gray-500" />
            <select
              className="rounded-md border px-2 py-1 text-sm"
              value={refreshMs}
              onChange={(e) => setRefreshMs(parseInt(e.target.value, 10))}
            >
              <option value={2000}>2s</option>
              <option value={5000}>5s</option>
              <option value={10000}>10s</option>
              <option value={30000}>30s</option>
            </select>
            <button
              onClick={poll}
              className="ml-2 inline-flex items-center gap-1 rounded-md bg-sky-600 px-2 py-1 text-sm font-semibold text-white hover:bg-sky-700"
            >
              <RefreshCcw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          {(["backend", "db", "redis", "graphql"] as ServiceKey[]).map((key) => (
            <StatusCard key={key} name={key} services={services} />
          ))}
        </div>
      </motion.div>
    </div>
  );
}

function StatusCard({ name, services }: { name: ServiceKey; services: Record<ServiceKey, ServiceState> }) {
  const s = services[name];
  const meta = SERVICE_META[name];
  const level = classifyLevel(s);
  const colorMap = {
    sky: "text-sky-500",
    emerald: "text-emerald-500",
    orange: "text-orange-500",
    fuchsia: "text-fuchsia-500",
  }[meta.color];

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.995 }}
      className={`rounded-2xl border bg-white p-5 text-left shadow-sm ${colorMap}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {meta.icon}
          <div className="text-gray-800 font-semibold">{meta.label}</div>
        </div>
        <div className={badgeClass(level)}>
          {statusIcon(level)}
          {statusText(level)}
        </div>
      </div>
      <div className="mt-4 flex items-end justify-between gap-4">
        <div className="text-sm text-gray-600">
          <div>
            Last ping:{" "}
            <span className="font-mono font-semibold text-gray-800">
              {s.data?._ping ?? "—"} ms
            </span>
          </div>
          <div className="text-xs text-gray-400">
            Updated: {s.data?._ts ? new Date(s.data._ts).toLocaleTimeString() : "—"}
          </div>
        </div>
        <div className="text-sky-500">
          <Sparkline points={s.history} />
        </div>
      </div>
    </motion.div>
  );
}
