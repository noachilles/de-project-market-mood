import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "@/views/Dashboard.vue";
import StocksList from "@/views/StocksList.vue";
import { fetchCurrentPrice, fetchChart } from "@/services/stocks";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // ✅ 기본 진입 → 대시보드
    { path: "/", redirect: "/dashboard" },

    // ✅ 메인 화면
    { path: "/dashboard", component: Dashboard },

    // ✅ 전체 종목 리스트
    { path: "/stocks", component: StocksList },
  ],
});

export default router;

/* =========================
   2) 현재가 실시간 갱신 (Redis 기반)
========================= */
async function refreshAllPrices() {
  polling.value = true;
  try {
    // 직접 fetch 대신 서비스를 호출합니다.
    const results = await Promise.allSettled(
      watchItems.value.map(it => fetchCurrentPrice(it.ticker))
    );

    results.forEach((r, idx) => {
      // r.value가 이미 JSON 데이터(data)이므로 바로 사용 가능합니다.
      if (r.status === "fulfilled" && r.value.price) {
        const item = watchItems.value[idx];
        item.price = Number(r.value.price);
        item.change = Number(r.value.change_rate || 0);

        if (item.ticker === selectedTicker.value) {
          const now = new Date().toISOString();
          livePriceData.value.push({ x: now, y: item.price });
          if (livePriceData.value.length > 30) livePriceData.value.shift();
        }
      }
    });
    lastUpdatedAt.value = new Date().toLocaleTimeString();
  } catch (e) {
    lastError.value = "가격 갱신 실패";
  } finally {
    polling.value = false;
  }
}
