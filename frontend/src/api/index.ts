import axios from "axios";

const apiDomain =
  import.meta.env.VITE_API_DOMAIN ||
  (typeof window !== "undefined"
    ? `https://api.${window.location.hostname}`
    : "http://localhost:8000");

const api = axios.create({
  baseURL: apiDomain,
  withCredentials: false,
});

api.interceptors.request.use((config) => {
  if (config.headers && config.headers.Authorization === "") return config;
  const token = localStorage.getItem("token");
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any)["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

export default api;
