import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
});

export function fetchNews({ q = "", page = 1, size = 10, from = "", to = "", source = "" } = {}) {
  return api.get("/news/", { params: { q, page, size, from, to, source } });
}
