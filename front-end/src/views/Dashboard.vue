<script setup>
import { ref, computed } from "vue";

import Header from "@/components/dashboard/Header.vue";
import WatchList from "@/components/dashboard/WatchList.vue";
import StockChart from "@/components/dashboard/StockChart.vue";
import NewsFeed from "@/components/dashboard/NewsFeed.vue";
import AiInsight from "@/components/dashboard/AiInsight.vue";
import MyHolding from "@/components/dashboard/MyHolding.vue";

/* ================= 1. 관심종목 마스터 ================= */
const watchItems = [
  { ticker: "005930", name: "삼성전자", price: 85300, change: 2.55, volume: 1250000 },
  { ticker: "000660", name: "SK하이닉스", price: 135000, change: -1.15, volume: 980000 },
];

/* ================= 2. 선택 상태 (🔥 핵심) ================= */
const selectedTicker = ref(watchItems[0].ticker);

/* ✅ Header에서 바로 쓸 “선택된 종목 객체” */
const selectedStock = computed(() => {
  return watchItems.find((w) => w.ticker === selectedTicker.value) ?? null;
});

/* ================= 3. 보유 종목 ================= */
const holdingsByTicker = {
  "005930": { symbol: "삼성전자", avgPrice: 72000, quantity: 100, currentPrice: 85300 },
  "000660": { symbol: "SK하이닉스", avgPrice: 142000, quantity: 20, currentPrice: 135000 },
};

const selectedHolding = computed(() => holdingsByTicker[selectedTicker.value] ?? null);

/* ================= 4. 전날 리포트 ================= */
const reportsByTicker = {
  "005930": {
    date: "2025-12-12 (금)",
    tag: "선행 지표 검증",
    summary: "기관·외국인 순매수 확대와 긍정 뉴스 비중 증가로 단기 상승 시그널이 우세했습니다.",
    bullets: ["긍정 뉴스 비중 42% → 57%", "외국인 +820억 / 기관 +310억", "감정 점수 선행 패턴 확인"],
    stats: [
      { label: "감정 점수", value: "71 (+6)", tone: "pos" },
      { label: "수급 합계", value: "+1,130억", tone: "pos" },
    ],
    todayFocus: "HBM 공급 계약 관련 헤드라인",
  },
  "000660": {
    date: "2025-12-12 (금)",
    tag: "리스크 점검",
    summary: "단기 수급 약화로 보수적 접근이 필요했습니다.",
    bullets: ["기관 매도 우위", "변동성 확대", "단기 추세 이탈 주의"],
    stats: [
      { label: "감정 점수", value: "48 (-5)", tone: "neg" },
      { label: "수급 합계", value: "-320억", tone: "neg" },
    ],
    todayFocus: "메모리 업황 가이던스",
  },
};

const selectedReport = computed(() => reportsByTicker[selectedTicker.value] ?? null);

/* ================= 5. 이벤트 ================= */
function onSelectTicker(ticker) {
  selectedTicker.value = ticker;
}
</script>

<template>
  <div class="dashboard-shell">
    <!-- 🔹 종목 헤더 -->
    <Header :stock="selectedStock" />

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
        <NewsFeed :ticker="selectedTicker" />
      </section>

      <!-- 오른쪽 -->
      <section class="column right">
        <AiInsight :ticker="selectedTicker" />
        <MyHolding :holding="selectedHolding" />
      </section>
    </main>
  </div>
</template>
