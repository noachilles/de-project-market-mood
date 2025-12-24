<!-- src/views/Dashboard.vue (or 해당 위치) -->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import { useRoute } from "vue-router";

import Header from "@/components/dashboard/Header.vue";
import WatchList from "@/components/dashboard/WatchList.vue";
import StockChart from "@/components/dashboard/StockChart.vue";
import NewsFeed from "@/components/dashboard/NewsFeed.vue";
import AiInsight from "@/components/dashboard/AiInsight.vue";

/* =========================
   0) API 및 상태 설정
========================= */
const route = useRoute();
const API_BASE = "http://localhost:8000";

const watchItems = ref([
  { ticker: "005930", name: "삼성전자", price: 0, change: 0, volume: 0 },
  { ticker: "000660", name: "SK하이닉스", price: 0, change: 0, volume: 0 },
]);

const selectedTicker = ref(watchItems.value[0].ticker);
const aiNewsList = ref([]); 
const dailyReport = ref(null); // DB: StockDailyReport
const isNewsLoading = ref(false);

/* =========================
   1) 데이터 fetch 로직
========================= */
// Dashboard.vue 수정
async function fetchStockData(ticker) {
  isNewsLoading.value = true;

  // 개별적으로 실행하여 서로의 실패가 영향을 주지 않도록 함
  const loadNews = async () => {
    try {
      const newsRes = await fetch(`${API_BASE}/api/news/?ticker=${ticker}&size=5`);
      if (!newsRes.ok) throw new Error("News API status error");
      const newsData = await newsRes.json();
      aiNewsList.value = newsData.items || [];
    } catch (e) {
      console.warn("⚠️ 뉴스 로드 실패 (ES 확인 필요):", e);
      aiNewsList.value = []; // 실패 시 빈 배열 처리
    }
  };

  const loadChartAndReport = async () => {
    try {
      // 404 방지를 위해 슬래시(/)를 명시적으로 포함
      const reportRes = await fetch(`${API_BASE}/api/chart/${ticker}/?range=1w`);
      if (!reportRes.ok) throw new Error("Report API status error");
      
      const chartData = await reportRes.json();
      
      // AI 리포트 추출 로직
      const reportDates = Object.keys(chartData.ai_reports || {}).sort().reverse();
      if (reportDates.length > 0) {
        const latestDate = reportDates[0];
        dailyReport.value = {
          ...chartData.ai_reports[latestDate],
          date: latestDate
        };
      }
    } catch (e) {
      console.error("❌ 분석 리포트 로드 실패:", e);
    }
  };

  // 두 함수를 동시에 실행 (하나가 거절되어도 나머지는 계속됨)
  await Promise.allSettled([loadNews(), loadChartAndReport()]);
  isNewsLoading.value = false;
}
async function fetchCurrentPrice(code) {
  const res = await fetch(`${API_BASE}/api/current-price/${code}`);
  return await res.json();
}

/* =========================
   2) 감시 및 이벤트 로직
========================= */
watch(selectedTicker, (newTicker) => {
  if (newTicker) fetchStockData(newTicker);
}, { immediate: true });

watch(
  () => route.query.code,
  (code) => {
    if (code) selectedTicker.value = code;
  },
  { immediate: true }
);

function onSelectTicker(ticker) {
  selectedTicker.value = ticker;
}

/* =========================
   3) 리포트 변환 로직 (WatchList 전달용)
========================= */
const selectedReport = computed(() => {
  // 1순위: DB에 저장된 종합 리포트가 있는 경우
  if (dailyReport.value) {
    return {
      date: dailyReport.value.date,
      tag: "AI 종합 브리핑",
      summary: dailyReport.value.summary,
      bullets: aiNewsList.value.slice(0, 3).map(n => n.title),
      stats: [
        { 
          label: "AI 감정 지수", 
          value: dailyReport.value.sentiment.toFixed(2), 
          tone: dailyReport.value.sentiment >= 0 ? "pos" : "neg" 
        }
      ],
      todayFocus: "주요 매물대 및 뉴스 모멘텀 분석"
    };
  }

  // 2순위: 종합 리포트는 없지만 개별 뉴스는 있는 경우 (실시간 분석 모드)
  if (aiNewsList.value.length > 0) {
    const latest = aiNewsList.value[0];
    return {
      date: latest.published_at.split('T')[0],
      tag: "실시간 뉴스 분석",
      summary: latest.content_summary,
      bullets: aiNewsList.value.slice(1, 4).map(n => n.title),
      stats: [
        { label: "감정 점수", value: latest.sentiment_score.toFixed(2), tone: latest.sentiment_score >= 0 ? "pos" : "neg" }
      ],
      todayFocus: "최신 뉴스 헤드라인 분석 중"
    };
  }

  return null;
});

/* =========================
   4) 현재가 폴링 (기존 유지)
========================= */
// ... (refreshAllPrices 및 setInterval 로직은 기존과 동일하므로 생략 가능하나 그대로 유지)
const polling = ref(false);
const lastUpdatedAt = ref(null);
const lastError = ref(null);
let timer = null;

async function refreshAllPrices() {
  polling.value = true;
  try {
    const results = await Promise.allSettled(watchItems.value.map(it => fetchCurrentPrice(it.ticker)));
    results.forEach((r, idx) => {
      if (r.status === "fulfilled" && r.value.price) {
        watchItems.value[idx].price = Number(r.value.price);
        watchItems.value[idx].change = Number(r.value.change_rate || 0);
        watchItems.value[idx].volume = Number(r.value.volume || 0);
      }
    });
    lastUpdatedAt.value = new Date().toISOString();
  } catch (e) {
    lastError.value = String(e);
  } finally {
    polling.value = false;
  }
}

onMounted(() => {
  refreshAllPrices();
  timer = setInterval(refreshAllPrices, 3000);
});
onBeforeUnmount(() => clearInterval(timer));
</script>
<template>
  <div class="dashboard-shell">
    <!-- ✅ 헤더 검색에서 종목 선택 emit("select", code) 받기 -->
    <Header :stock="selectedStock" @select="onSelectTicker" />

    <!-- (선택) 상태 표시 -->
    <div style="padding: 8px 12px; color: #9ca3af; font-size: 12px;">
      <span v-if="polling">현재가 갱신 중…</span>
      <span v-else>마지막 갱신: {{ lastUpdatedAt ?? "없음" }}</span>
      <span v-if="lastError" style="margin-left: 10px; color: #fca5a5;">
        (에러: {{ lastError }})
      </span>
    </div>

    <main class="layout">
      <!-- 왼쪽 -->
      <section class="column left">
        <WatchList
          :items="watchItems"
          :selected-ticker="selectedTicker"
          :yesterday-report="selectedReport"
          @select="onSelectTicker"
        />
      </section>

      <!-- 중앙 -->
      <section class="column center">
        <StockChart :ticker="selectedTicker" />
      </section>

      <!-- 오른쪽 -->
      <section class="column right">
        <AiInsight 
          :ticker="selectedTicker" 
          :news="aiNewsList" 
        />
        
        <NewsFeed 
          :ticker="selectedTicker" 
          :news="aiNewsList" 
          :loading="isNewsLoading" 
        />
      </section>
    </main>
  </div>
</template>
