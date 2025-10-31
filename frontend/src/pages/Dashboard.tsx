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
const HISTORY_LEN = 40; // сколько точек держим в истории для спарклайна
const DEGRADED_PING_MS = 800; // >= — деградирован
const OFFLINE_GRACE_MS = 30000; // если нет успешных ответов дольше этого — считаем offline

type StatusMap = "ok" | "error" | "loading";
type ServiceKey = "backend" | "db" | "redis" | "graphql";

interface HealthData {
  [key: string]: any;
  _ping?: number; // ms
  _ts?: number; // timestamp
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

/**
 * Вспомогательные утилиты
 */
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

  // если давно не было ОК ответа — оффлайн
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
 * Мини-спарклайн (SVG)
 */
function Sparkline({
  points,
  className = "",
}: {
  points: PingPoint[];
  className?: string;
}) {
  const width = 160;
  const height = 40;
  const pad = 4;

  const filtered = points.slice(-HISTORY_LEN);
  const vals = filtered.map((p) => (p.v ?? 0));
  const vmin = Math.min(...vals, 0);
  const vmax = Math.max(...vals, 1);

  const x = (i: number) =>
    pad + (i * (width - pad * 2)) / Math.max(filtered.length - 1, 1);
  const y = (v: number) =>
    height - pad - ((v - vmin) / Math.max(vmax - vmin, 1)) * (height - pad * 2);

  const d =
    filtered.length > 0
      ? filtered
          .map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)},${y(p.v ?? 0)}`)
          .join(" ")
      : "";

  // заливка под графиком
  const area =
    filtered.length > 1
      ? `${filtered
          .map((p, i) => `${i === 0 ? "M" : "L"} ${x(i)},${y(p.v ?? 0)}`)
          .join(" ")} L ${x(filtered.length - 1)},${height - pad} L ${x(0)},${
          height - pad
        } Z`
      : "";

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={`w-[160px] h-[40px] ${className}`}
      aria-hidden
    >
      <path d={area} fill="currentColor" opacity={0.1} />
      <path d={d} fill="none" stroke="currentColor" strokeWidth={2} />
    </svg>
  );
}

/**
 * Основной компонент
 */
export default function App() {
  const [services, setServices] = useState<Record<ServiceKey, ServiceState>>({
    backend: { status: "loading", data: null, history: [] },
    db: { status: "loading", data: null, history: [] },
    redis: { status: "loading", data: null, history: [] },
    graphql: { status: "loading", data: null, history: [] },
  });
  const [selected, setSelected] = useState<ServiceKey | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "raw" | "formatted" | "history">("overview");
  const [refreshMs, setRefreshMs] = useState<number>(REFRESH_MS_DEFAULT);
  const timerRef = useRef<number | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // ——— ПИНГУЕМ СЕРВИСЫ ———
  const poll = async () => {
    setIsRefreshing(true);

    const timedFetch = async (url: string, init?: RequestInit) => {
      const t0 = performance.now();
      const res = await fetch(url, init);
      const isJSON = (res.headers.get("content-type") || "").includes("json");
      const json = isJSON ? await res.json() : { status: res.ok ? "ok" : "error" };
      const t1 = performance.now();
      return { ok: res.ok, json, ping: Math.round(t1 - t0) };
    };

    const next = structuredClone(services) as typeof services;
    const now = Date.now();

    // Backend + DB из /health
    try {
      const r = await timedFetch(`${API_URL}/health`);
      next.backend.status = r.ok && r.json?.status === "ok" ? "ok" : "error";
      next.backend.data = { ...r.json, _ping: r.ping, _ts: now };
      next.backend.history = [
        ...next.backend.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: r.ok ? r.ping : null, ok: r.ok },
      ];
      if (r.ok) next.backend.lastOkAt = now;

      // DB статус вытаскиваем из ответа backend
      const dbOk = r.ok && r.json?.db_status === "ok";
      next.db.status = dbOk ? "ok" : "error";
      next.db.data = {
        status: dbOk ? "ok" : "error",
        db_status: r.json?.db_status ?? "unknown",
        _ping: r.ping,
        _ts: now,
      };
      next.db.history = [
        ...next.db.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: dbOk ? r.ping : null, ok: dbOk },
      ];
      if (dbOk) next.db.lastOkAt = now;
    } catch {
      const fail = (k: ServiceKey) => {
        next[k].status = "error";
        next[k].history = [
          ...next[k].history.slice(-(HISTORY_LEN - 1)),
          { t: now, v: null, ok: false },
        ];
      };
      fail("backend");
      fail("db");
    }

    // Redis отдельно
    try {
      const r = await timedFetch(`${API_URL}/redis-health`);
      const ok = r.ok && r.json?.status === "ok";
      next.redis.status = ok ? "ok" : "error";
      next.redis.data = { ...r.json, _ping: r.ping, _ts: now };
      next.redis.history = [
        ...next.redis.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: ok ? r.ping : null, ok },
      ];
      if (ok) next.redis.lastOkAt = now;
    } catch {
      next.redis.status = "error";
      next.redis.history = [
        ...next.redis.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: null, ok: false },
      ];
    }

    // GraphQL: пробуем без слеша и со слешем (у тебя раньше было 307->/graphql/)
    const tryGraphQL = async () => {
      try {
        return await timedFetch(`${API_URL}/graphql`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: "{ __typename }" }),
          redirect: "manual",
        });
      } catch {
        // fallback
        return await timedFetch(`${API_URL}/graphql/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: "{ __typename }" }),
        });
      }
    };

    try {
      const r = await tryGraphQL();
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
      next.graphql.history = [
        ...next.graphql.history.slice(-(HISTORY_LEN - 1)),
        { t: now, v: null, ok: false },
      ];
    }

    setServices(next);
    setIsRefreshing(false);
  };

  useEffect(() => {
    poll();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    timerRef.current = window.setInterval(poll, refreshMs) as unknown as number;
    return () => {
      if (timerRef.current) window.clearInterval(timerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshMs, services.backend.status]); // зависимость слабая, чтобы не зациклить

  const overall = useMemo(() => {
    // сводный статус сверху (как панелька в Grafana)
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

  /**
   * Карточка сервиса
   */
  const StatusCard = ({ name }: { name: ServiceKey }) => {
    const s = services[name];
    const meta = SERVICE_META[name];
    const level = classifyLevel(s);
    const isSelected = selected === name;

    const colorClass = {
      sky: "text-sky-500",
      emerald: "text-emerald-500",
      orange: "text-orange-500",
      fuchsia: "text-fuchsia-500",
    }[meta.color];

    return (
      <motion.button
        onClick={() => {
          setSelected(name);
          setActiveTab("overview");
        }}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.995 }}
        animate={{
          boxShadow: isSelected
            ? "0px 0px 26px rgba(56, 189, 248, 0.7)"
            : "0px 2px 10px rgba(0,0,0,0.06)",
        }}
        transition={{ duration: 0.25 }}
        className={`group relative cursor-pointer rounded-2xl border bg-white p-5 text-left outline-none 
          ${isSelected ? "border-sky-300 ring-2 ring-sky-200" : "border-gray-100 hover:border-sky-200"}
          `}
      >
        <div className="flex items-center justify-between">
          <div className={`flex items-center gap-3 ${colorClass}`}>
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
              Updated:{" "}
              {s.data?._ts
                ? new Date(s.data._ts).toLocaleTimeString()
                : "—"}
            </div>
          </div>

          <div className={`text-sky-500`}>
            <Sparkline points={s.history} />
          </div>
        </div>
      </motion.button>
    );
  };

  /**
   * Модалка
   */
  const SelectedModal = () => {
    if (!selected) return null;
    const s = services[selected];
    const level = classifyLevel(s);
    const meta = SERVICE_META[selected];

    const avgPing =
      s.history.filter((p) => p.v != null).reduce((a, b) => a + (b.v || 0), 0) /
        Math.max(1, s.history.filter((p) => p.v != null).length) || 0;

    const avail =
      (s.history.filter((p) => p.ok).length / Math.max(1, s.history.length)) *
      100;

    return (
      <AnimatePresence>
        {selected && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="relative w-full max-w-4xl rounded-2xl bg-white p-6 shadow-2xl"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
            >
              <button
                onClick={() => setSelected(null)}
                className="absolute right-4 top-4 text-gray-400 transition-colors hover:text-gray-600"
              >
                <X size={22} />
              </button>

              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`text-${meta.color}-500`}>{meta.icon}</div>
                  <h2 className="text-xl font-semibold">{meta.label}</h2>
                  <div className={badgeClass(level)}>{statusText(level)}</div>
                </div>
              </div>

              <div className="mb-4 flex items-center gap-2 border-b pb-3">
                <TabBtn icon={Activity} label="Overview" v="overview" at={activeTab} set={setActiveTab} />
                <TabBtn icon={Code2} label="Raw JSON" v="raw" at={activeTab} set={setActiveTab} />
                <TabBtn icon={BarChart3} label="Formatted" v="formatted" at={activeTab} set={setActiveTab} />
                <TabBtn icon={Clock} label="History" v="history" at={activeTab} set={setActiveTab} />
              </div>

              {/* Тело вкладок */}
              <div className="max-h-[60vh] overflow-auto">
                {activeTab === "overview" && (
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-xl border bg-white p-4">
                      <div className="text-sm text-gray-500">Avg. Ping (last {HISTORY_LEN})</div>
                      <div className="mt-1 text-2xl font-bold">{Math.round(avgPing)} ms</div>
                    </div>
                    <div className="rounded-xl border bg-white p-4">
                      <div className="text-sm text-gray-500">Availability</div>
                      <div className="mt-1 text-2xl font-bold">
                        {avail.toFixed(0)}%
                      </div>
                    </div>
                    <div className="rounded-xl border bg-white p-4">
                      <div className="text-sm text-gray-500">Last OK</div>
                      <div className="mt-1 text-lg font-semibold">
                        {s.lastOkAt ? new Date(s.lastOkAt).toLocaleTimeString() : "—"}
                      </div>
                    </div>

                    <div className="md:col-span-3 rounded-xl border bg-white p-4">
                      <div className="mb-2 flex items-center justify-between">
                        <div className="text-sm font-medium text-gray-700">Ping Timeline</div>
                        <div className="text-xs text-gray-500">
                          {new Date().toLocaleTimeString()}
                        </div>
                      </div>
                      <div className="text-sky-500">
                        <Sparkline points={s.history} className="w-full" />
                      </div>
                    </div>
                  </div>
                )}

                {activeTab === "raw" && (
                  <pre className="whitespace-pre-wrap rounded-xl bg-gray-50 p-4 text-xs font-mono text-gray-800">
                    {JSON.stringify(s.data ?? {}, null, 2)}
                  </pre>
                )}

                {activeTab === "formatted" && (
                  <div className="rounded-xl bg-white">
                    <table className="w-full overflow-hidden rounded-xl text-sm">
                      <tbody>
                        {Object.entries(s.data ?? {}).map(([k, v]) => (
                          <tr key={k} className="border-b last:border-0">
                            <td className="w-1/3 bg-gray-50 px-4 py-2 font-medium text-gray-700">
                              {k}
                            </td>
                            <td className="px-4 py-2 text-gray-800">
                              {typeof v === "object" ? (
                                <code className="text-xs">
                                  {JSON.stringify(v)}
                                </code>
                              ) : (
                                String(v)
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {activeTab === "history" && (
                  <div className="space-y-2">
                    {s.history
                      .slice()
                      .reverse()
                      .map((p, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between rounded-lg border bg-white px-3 py-2 text-sm"
                        >
                          <div className="flex items-center gap-2">
                            {p.ok ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                            ) : (
                              <XCircle className="h-4 w-4 text-rose-600" />
                            )}
                            <span className="font-mono">
                              {new Date(p.t).toLocaleTimeString()}
                            </span>
                          </div>
                          <div className="font-mono">
                            {p.v != null ? `${p.v} ms` : "—"}
                          </div>
                        </div>
                      ))}
                  </div>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-gray-900">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mx-auto max-w-6xl space-y-8"
      >
        {/* TOP BAR */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <Activity className={`h-6 w-6 ${overallColor}`} />
            <h1 className="text-2xl font-bold">H.O.M – Real-Time Monitor</h1>
            <div className={badgeClass(overall)}>{statusText(overall)}</div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 rounded-xl border bg-white px-3 py-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <span className="text-sm text-gray-600">Auto-refresh</span>
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
        </div>

        {/* GRID */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
          <StatusCard name="backend" />
          <StatusCard name="db" />
          <StatusCard name="redis" />
          <StatusCard name="graphql" />
        </div>

        <footer className="pt-6 text-center text-sm text-gray-500">
          Auto-refresh running • Click any card to inspect details
        </footer>
      </motion.div>

      {/* MODAL */}
      <SelectedModal />
    </div>
  );
}

/**
 * Кнопка вкладки модалки
 */
function TabBtn({
  icon: Icon,
  label,
  v,
  at,
  set,
}: {
  icon: any;
  label: string;
  v: "overview" | "raw" | "formatted" | "history";
  at: "overview" | "raw" | "formatted" | "history";
  set: (v: "overview" | "raw" | "formatted" | "history") => void;
}) {
  const active = at === v;
  return (
    <button
      onClick={() => set(v)}
      className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
        active ? "bg-sky-100 text-sky-700" : "text-gray-600 hover:text-gray-800"
      }`}
    >
      <Icon size={16} />
      {label}
    </button>
  );
}
