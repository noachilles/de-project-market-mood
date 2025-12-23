<!-- src/views/Dashboard.vue (or 해당 위치) -->
<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";

import Header from "@/components/dashboard/Header.vue";
import WatchList from "@/components/dashboard/WatchList.vue";
import StockChart from "@/components/dashboard/StockChart.vue";
import NewsFeed from "@/components/dashboard/NewsFeed.vue";
import AiInsight from "@/components/dashboard/AiInsight.vue";
import { useRoute } from "vue-router";
import { watch } from "vue";

const route = useRoute();

watch(
  () => route.query.code,
  (code) => {
    if (typeof code === "string" && code.trim()) {
      onSelectTicker(code.trim());
    }
  },
  { immediate: true }
);

/* =========================
   0) API 설정
========================= */
const API_BASE = "http://localhost:8000";

/**
 * current-price API 호출
 * - 200이면 정상 JSON
 * - 404(캐시 없음)이어도 정상 상태로 취급하고 JSON을 그대로 반환
 * - 그 외 에러는 throw
 */
async function fetchCurrentPrice(code) {
  const url = `${API_BASE}/api/current-price/${code}`;
  const res = await fetch(url);

  if (res.status === 404) {
    // {"code": "...", "data": null, "message": "..."} 형태
    try {
      return await res.json();
    } catch {
      return { code, data: null, message: "No cached price in Redis" };
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`current-price API failed: ${res.status} ${text}`);
  }

  return await res.json(); // {"code","price","change_rate","volume","timestamp"}
}

/* =========================
   1) 관심종목 마스터 (초기값은 더미)
========================= */
const watchItems = ref([
  { ticker: "005930", name: "삼성전자", price: 0, change: 0, volume: 0 },
  { ticker: "000660", name: "SK하이닉스", price: 0, change: 0, volume: 0 },
]);

/* =========================
   2) 선택 상태
========================= */
const selectedTicker = ref(watchItems.value[0].ticker);

const selectedStock = computed(() => {
  return watchItems.value.find((w) => w.ticker === selectedTicker.value) ?? null;
});

/* =========================
   3) 전날 리포트 (더미 유지)
========================= */
const reportsByTicker = {
  "005930": {
    date: "2025-12-12 (금)",
    tag: "선행 지표 검증",
    summary:
      "기관·외국인 순매수 확대와 긍정 뉴스 비중 증가로 단기 상승 시그널이 우세했습니다.",
    bullets: [
      "긍정 뉴스 비중 42% → 57%",
      "외국인 +820억 / 기관 +310억",
      "감정 점수 선행 패턴 확인",
    ],
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

/* =========================
   4) 이벤트
========================= */
function onSelectTicker(ticker) {
  selectedTicker.value = ticker;
}

/* =========================
   5) 현재가 폴링
========================= */
const polling = ref(false);
const lastUpdatedAt = ref(null);
const lastError = ref(null);
let timer = null;

function isFiniteNumber(v) {
  const n = Number(v);
  return Number.isFinite(n);
}

async function refreshAllPrices() {
  polling.value = true;
  lastError.value = null;

  try {
    const results = await Promise.allSettled(
      watchItems.value.map(async (it) => {
        const data = await fetchCurrentPrice(it.ticker);
        return { ticker: it.ticker, data };
      })
    );

    for (const r of results) {
      if (r.status !== "fulfilled") continue;

      const { ticker, data } = r.value;

      // 캐시 없음(data:null)인 경우는 스킵
      if (data?.data === null) continue;

      // price가 숫자면 반영
      if (!isFiniteNumber(data?.price)) continue;

      const idx = watchItems.value.findIndex((x) => x.ticker === ticker);
      if (idx === -1) continue;

      watchItems.value[idx] = {
        ...watchItems.value[idx],
        price: Number(data.price),
        change: isFiniteNumber(data.change_rate)
          ? Number(data.change_rate)
          : watchItems.value[idx].change ?? 0,
        volume: isFiniteNumber(data.volume)
          ? Number(data.volume)
          : watchItems.value[idx].volume ?? 0,
      };
    }

    lastUpdatedAt.value = new Date().toISOString();
  } catch (e) {
    console.error("[Dashboard] refreshAllPrices failed:", e);
    lastError.value = String(e?.message ?? e);
  } finally {
    polling.value = false;
  }
}

onMounted(async () => {
  await refreshAllPrices();
  timer = setInterval(refreshAllPrices, 3000);
});

onBeforeUnmount(() => {
  clearInterval(timer);
});
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
        <AiInsight :ticker="selectedTicker" />
        <NewsFeed :ticker="selectedTicker" />
      </section>
    </main>
  </div>
</template>
