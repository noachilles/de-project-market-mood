import { createRouter, createWebHistory } from "vue-router";
import Dashboard from "@/views/Dashboard.vue";
import StocksList from "@/views/StocksList.vue";

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
