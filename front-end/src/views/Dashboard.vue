<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { useRoute } from "vue-router";

import Header from "@/components/dashboard/Header.vue";
import WatchList from "@/components/dashboard/WatchList.vue";
import StockChart from "@/components/dashboard/StockChart.vue";
import NewsFeed from "@/components/dashboard/NewsFeed.vue";
import HotKeywords from "@/components/dashboard/HotKeywords.vue";
import ChatBot from "@/components/dashboard/ChatBot.vue";
import { fetchCurrentPrice } from "@/services/stocks";

/* =========================
   0) 상태 및 API 설정
========================= */
const livePriceData = ref([]); // ✅ 차트에 보낼 실시간 데이터 배열
const route = useRoute();
const API_BASE = "http://localhost:8000";

/* ================= 1. 관심종목 리스트 (초기 데이터) ================= */
const watchItems = ref([
  { ticker: "005930", name: "삼성전자", price: 0, change: 0, vol: 0 },
]);

/* ================= 2. 선택 상태 (🔥 핵심) ================= */
const selectedTicker = ref(watchItems.value[0]?.ticker || "005930");
const aiNewsList = ref([]); 
const dailyReport = ref(null);
const isNewsLoading = ref(false);

// 폴링 및 에러 상태
const polling = ref(false);
const lastUpdatedAt = ref(null);
const lastError = ref(null);
let timer = null;

/* ✅ Header에 전달할 현재 선택된 종목 정보 */
const selectedStock = computed(() => {
  return watchItems.value.find((w) => w.ticker === selectedTicker.value) ?? null;
});

/* =========================
   1) 데이터 Fetch 로직 (AI & News)
========================= */
async function fetchStockData(ticker) {
  isNewsLoading.value = true;
  lastError.value = null;

  // 뉴스 로드 (Elasticsearch 기반)
  const loadNews = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/news/?ticker=${ticker}&size=5`);
      if (!res.ok) throw new Error("News API 에러");
      const data = await res.json();
      aiNewsList.value = data.items || [];
    } catch (e) {
      console.warn("⚠️ 뉴스 로드 실패:", e);
      aiNewsList.value = [];
    }
  };

  // 차트 및 AI 리포트 로드 (Postgres 기반)
  const loadChartAndReport = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/chart/${ticker}?range=1w`);
      if (!res.ok) throw new Error("Chart/Report API 에러");
      const data = await res.json();
      
      // 최신 AI 리포트 추출
      const reportDates = Object.keys(data.ai_reports || {}).sort().reverse();
      if (reportDates.length > 0) {
        const latestDate = reportDates[0];
        dailyReport.value = { ...data.ai_reports[latestDate], date: latestDate };
      } else {
        dailyReport.value = null;
      }
    } catch (e) {
      console.error("❌ 분석 리포트 로드 실패:", e);
    }
  };

  await Promise.allSettled([loadNews(), loadChartAndReport()]);
  isNewsLoading.value = false;
}

/* =========================
   2) 현재가 실시간 갱신 (Redis 기반)
========================= */
// Dashboard.vue 의 refreshAllPrices 함수 내부
async function refreshAllPrices() {
  polling.value = true;
  try {
    const results = await Promise.allSettled(
      watchItems.value.map(it => fetchCurrentPrice(it.ticker))
    );

    results.forEach((res, idx) => {
      if (res.status === "fulfilled" && res.value && res.value.price) {
        const item = watchItems.value[idx];
        const data = res.value; // 백엔드 응답 데이터

        item.price = Number(data.price);
        item.change = Number(data.change_rate || 0);
        
        // ✅ [핵심] 백엔드의 "volume": 22 데이터를 Header가 인식하는 "vol"에 할당
        item.vol = Number(data.volume || 0); 

        if (item.ticker === selectedTicker.value) {
          const now = new Date();
          const nextPoint = { x: now, y: item.price };
          // 무한 루프 방지용 새 배열 할당
          livePriceData.value = [...livePriceData.value, nextPoint].slice(-1200);
        }
      }
    });
    lastUpdatedAt.value = new Date().toLocaleTimeString();
  } catch (e) {
    console.error("❌ 데이터 수집 에러:", e);
  } finally {
    polling.value = false;
  }
}

/* =========================
   3) 이벤트 핸들러 및 감시
========================= */
// Header나 WatchList에서 종목 선택 시 실행
function onSelectTicker(ticker) {
  selectedTicker.value = ticker;
}

// 종목 변경 감시 -> 실시간 데이터 초기화 및 데이터 로드
watch(selectedTicker, (newTicker) => {
  if (newTicker) {
    livePriceData.value = [];
    fetchStockData(newTicker);
  }
}, { immediate: true });

// URL 쿼리 파라미터 감시 (ticker 또는 code)
watch(() => route.query.ticker || route.query.code, (ticker) => {
  if (ticker) selectedTicker.value = ticker;
}, { immediate: true });

/* ✅ WatchList에 전달할 리포트 데이터 변환 */
const selectedReport = computed(() => {
  if (!dailyReport.value) return null;
  return {
    date: dailyReport.value.date,
    tag: "AI 종합 브리핑",
    summary: dailyReport.value.summary,
    bullets: aiNewsList.value.slice(0, 3).map(n => n.title),
    stats: [
      { label: "AI 감정 지수", value: dailyReport.value.sentiment.toFixed(2), tone: dailyReport.value.sentiment >= 0 ? "pos" : "neg" }
    ],
    todayFocus: "뉴스 모멘텀 분석 중"
  };
});

/* ✅ NewsFeed에 전달할 뉴스 데이터 */
const newsFeedData = computed(() => {
  return {
    items: aiNewsList.value,
    isLoading: isNewsLoading.value,
    ticker: selectedTicker.value,
  };
});

onMounted(() => {
  refreshAllPrices();
  timer = setInterval(refreshAllPrices, 3000); // 3초마다 Redis 확인
});

onBeforeUnmount(() => clearInterval(timer));
</script>

<template>
  <div class="dashboard-shell">
    <Header :stock="selectedStock" @select="onSelectTicker" />

    <div class="status-bar">
      <span v-if="polling" class="loading-text">🔄 현재가 갱신 중…</span>
      <span v-else class="time-text">⏱ 마지막 갱신: {{ lastUpdatedAt ?? "없음" }}</span>
      <span v-if="lastError" class="error-text">⚠️ {{ lastError }}</span>
    </div>

    <main class="layout">
      <section class="column left">
        <WatchList
          :items="watchItems"
          :selected-ticker="selectedTicker"
          :yesterday-report="selectedReport"
          @select="onSelectTicker"
        />
      </section>

      <section class="column center">
        <StockChart 
          :ticker="selectedTicker" 
          :live-data="livePriceData" 
        />
      </section>

      <section class="column right">
        <HotKeywords />
        <NewsFeed :items="aiNewsList" :is-loading="isNewsLoading" :ticker="selectedTicker" />
      </section>
    </main>
    
    <ChatBot />
  </div>
</template>

<style scoped>
.status-bar {
  padding: 8px 12px;
  color: #9ca3af;
  font-size: 12px;
  background: #1f2937;
  display: flex;
  gap: 15px;
}
.error-text { color: #fca5a5; }
.loading-text { color: #60a5fa; }
/* 레이아웃 관련 CSS는 기존 스타일 유지 */
</style>