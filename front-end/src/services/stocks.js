import { api } from "@/lib/api";

export async function fetchCurrentPrice(code) {
  const { data } = await api.get(`/api/current-price/${code}`);
  return data;
}

export async function fetchChart(code, range = "1d") {
  const { data } = await api.get(`/api/chart/${code}`, { params: { range } });
  return data;
}
