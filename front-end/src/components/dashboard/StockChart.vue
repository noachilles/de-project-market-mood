<template>
  <div class="card">
    <div class="card-header chart-header">
      <div class="chart-headline">
        <div>
          <div class="card-title">Real-time Stock ({{ labelRange }})</div>
          <div class="card-sub">Price · Sentiment · Flow 통합 · {{ ticker }}</div>
        </div>
      </div>

      <div class="range-tabs range-tabs--below" aria-label="기간 선택">
        <button
          v-for="item in ranges"
          :key="item.value"
          class="range-btn"
          :class="{ active: range === item.value }"
          @click="changeRange(item.value)"
          type="button"
        >
          {{ item.label }}
        </button>
      </div>
    </div>

    <div class="divider"></div>

    <div class="chart-wrapper">
      <canvas ref="chartCanvas"></canvas>
    </div>

    <div class="chart-legend">
      <span><span class="legend-dot legend-price"></span> Price</span>
      <span><span class="legend-dot legend-sentiment"></span> Sentiment</span>
      <span><span class="legend-dot legend-flow"></span> Flow</span>
    </div>

    <p class="tooltip-note">
      차트 위 시점을 마우스로 올리면 해당 시점의
      <strong>뉴스 요약</strong>이 표시됩니다.
    </p>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, nextTick } from "vue";
import { Chart, registerables } from "chart.js";
import { CandlestickController, CandlestickElement } from "chartjs-chart-financial";
import { fetchChart } from "@/services/stocks";
import { fetchNewsByDate } from "@/services/stocks";

// Chart.js 등록
Chart.register(...registerables, CandlestickController, CandlestickElement);

// date-fns 어댑터는 Chart.js 등록 후에 import
import "chartjs-adapter-date-fns";

const props = defineProps({
  ticker: String,
  liveData: {
    type: Array,
    default: () => [],
  },
});

const chartCanvas = ref(null);
let chartInstance = null;

// 캔들 차트용 범위 (실시간, 1주, 1달, 3달)
const range = ref("rt");
const ranges = [
  { value: "rt", label: "실시간" },
  { value: "1w", label: "1주" },
  { value: "1m", label: "1달" },
  { value: "3m", label: "3달" },
];

// 캔들 데이터 및 뉴스 캐시
const candleData = ref([]);
const newsCache = ref({}); // { "2024-12-25": [{title: "...", ...}] }

const labelRange = computed(() => {
  const map = {
    rt: "실시간 (1분 캔들)",
    "1w": "1주 (오전/오후 캔들)",
    "1m": "1달 (일봉 캔들)",
    "3m": "3달 (일봉 캔들)",
  };
  return map[range.value] ?? "실시간";
});

const RANGE_SPEC = {
  rt: { stepMs: 1_000, points: 60, unit: "second" },
  "1d": { stepMs: 60 * 60 * 1_000, points: 24, unit: "hour" },
  "1w": { stepMs: 24 * 60 * 60 * 1_000, points: 7, unit: "day" },
  "1m": { stepMs: 3 * 24 * 60 * 60 * 1_000, points: 10, unit: "day" },
  "3m": { stepMs: 7 * 24 * 60 * 60 * 1_000, points: 13, unit: "week" },
  "6m": { stepMs: 14 * 24 * 60 * 60 * 1_000, points: 13, unit: "week" },
  "1y": { stepMs: 30 * 24 * 60 * 60 * 1_000, points: 12, unit: "month" },
};

const baseByTicker = {
  "005930": { price: 85000, sentiment: 62, flow: 30 },
  "000660": { price: 150000, sentiment: 48, flow: -10 },
};

function genSeries({ basePrice, baseSent, baseFlow, points, stepMs }) {
  const now = Date.now();
  const out = [];

  let p = basePrice;
  let s = baseSent;
  let f = baseFlow;

  for (let i = points - 1; i >= 0; i--) {
    const t = now - i * stepMs;

    p = Math.max(1, p + (Math.random() - 0.5) * basePrice * 0.002);
    s = Math.min(100, Math.max(0, s + (Math.random() - 0.5) * 6));
    f = f + (Math.random() - 0.5) * 40;

    out.push({
      x: t,
      price: Math.round(p),
      sentiment: Math.round(s),
      flow: Math.round(f),
      news: `뉴스 요약(${new Date(t).toLocaleString()}): 더미 데이터`,
    });
  }
  return out;
}

// 캔들 데이터 로드 및 뉴스 미리 로드
async function loadCandleData() {
  if (!props.ticker) {
    candleData.value = [];
    return;
  }

  try {
    const data = await fetchChart(props.ticker, range.value);
    candleData.value = (data.candles || []).map((candle) => ({
      x: new Date(candle.x).getTime(),
      o: candle.o,
      h: candle.h,
      l: candle.l,
      c: candle.c,
      v: candle.v,
      date: candle.date || candle.x.split('T')[0], // 날짜 문자열 (YYYY-MM-DD)
    }));
    
    // 뉴스 미리 로드 (비동기, 백그라운드) - 실시간 제외
    if (range.value !== "rt") {
      const uniqueDates = [...new Set(candleData.value.map(c => c.date))];
      uniqueDates.forEach(dateStr => {
        if (!newsCache.value[dateStr]) {
          loadNewsForDate(dateStr).catch(err => {
            console.warn(`뉴스 미리 로드 실패 (${dateStr}):`, err);
          });
        }
      });
    }
  } catch (error) {
    console.error("캔들 데이터 로드 실패:", error);
    candleData.value = [];
  }
}

// 특정 날짜의 뉴스 로드 (캐시 사용)
async function loadNewsForDate(dateStr) {
  if (!props.ticker || !dateStr) return [];

  // 캐시 확인
  if (newsCache.value[dateStr]) {
    return newsCache.value[dateStr];
  }

  try {
    const newsData = await fetchNewsByDate(props.ticker, dateStr);
    const items = newsData.items || [];
    newsCache.value[dateStr] = items;
    return items;
  } catch (error) {
    console.error(`뉴스 로드 실패 (${dateStr}):`, error);
    return [];
  }
}

/* ✅ 한 프레임 뒤에 실행(레이아웃 0 높이 방지) */
function raf() {
  return new Promise((resolve) => requestAnimationFrame(resolve));
}

async function buildChartSafe() {
  if (!chartCanvas.value) return;

  await nextTick();
  await raf();

  // canvas가 0 높이면 한 번 더 기다림
  const parent = chartCanvas.value.parentElement;
  if (parent && parent.clientHeight === 0) {
    await raf();
  }

  const ctx = chartCanvas.value.getContext("2d");

  try {
    chartInstance?.destroy();

    // 모든 범위에서 캔들 차트 사용
    if (candleData.value.length === 0) {
      await loadCandleData();
    }

    const candles = candleData.value.map((c) => ({
      x: c.x,
      o: c.o,
      h: c.h,
      l: c.l,
      c: c.c,
      date: c.date, // 뉴스 조회용
    }));

    // 시간 단위 설정
    let timeUnit = "minute";
    if (range.value === "1w" || range.value === "1m" || range.value === "3m") {
      timeUnit = "day";
    }

    chartInstance = new Chart(ctx, {
      type: "candlestick",
      data: {
        datasets: [{
          label: "OHLC",
          data: candles,
          // 주식 시장 스타일: 상승(초록), 하락(빨강)
          color: {
            up: "#22c55e",      // 상승 캔들 (밝은 초록)
            down: "#ef4444",    // 하락 캔들 (밝은 빨강)
            unchanged: "#9ca3af", // 동일 (회색)
          },
          // 캔들 스타일 설정
          borderColor: {
            up: "#16a34a",      // 상승 테두리 (진한 초록)
            down: "#dc2626",    // 하락 테두리 (진한 빨강)
            unchanged: "#6b7280", // 동일 테두리
          },
          borderWidth: 1,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { 
          mode: "index", 
          intersect: false,
          axis: "x",
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(15,23,42,0.96)",
            padding: 12,
            borderColor: "rgba(148,163,184,0.3)",
            borderWidth: 1,
            titleColor: "#f9fafb",
            bodyColor: "#e5e7eb",
            callbacks: {
              title: (items) => {
                if (items.length === 0) return "";
                const point = items[0].raw;
                const date = new Date(point.x);
                if (range.value === "rt") {
                  return date.toLocaleString("ko-KR", { 
                    month: "short", 
                    day: "numeric", 
                    hour: "2-digit", 
                    minute: "2-digit" 
                  });
                }
                return date.toLocaleDateString("ko-KR", { 
                  year: "numeric", 
                  month: "long", 
                  day: "numeric" 
                });
              },
              label: (context) => {
                const point = context.raw;
                const change = point.c - point.o;
                const changePercent = ((change / point.o) * 100).toFixed(2);
                const changeColor = change >= 0 ? "#22c55e" : "#ef4444";
                const changeSign = change >= 0 ? "+" : "";
                
                return [
                  `시가: ${point.o?.toLocaleString("ko-KR")}원`,
                  `고가: ${point.h?.toLocaleString("ko-KR")}원`,
                  `저가: ${point.l?.toLocaleString("ko-KR")}원`,
                  `종가: ${point.c?.toLocaleString("ko-KR")}원`,
                  `변동: ${changeSign}${change.toLocaleString("ko-KR")}원 (${changeSign}${changePercent}%)`,
                ];
              },
              afterBody: (items) => {
                if (items.length === 0 || range.value === "rt") return [];
                const point = items[0].raw;
                const dateStr = point.date;
                if (!dateStr) return [];

                // 캐시에서 뉴스 가져오기 (동기)
                const newsItems = newsCache.value[dateStr] || [];
                
                if (newsItems.length === 0) {
                  // 캐시에 없으면 비동기로 로드 시도 (다음 호버 시 표시됨)
                  loadNewsForDate(dateStr).catch(() => {});
                  return ["\n📰 당일 뉴스 로딩 중..."];
                }

                // 당일 기사 리포트 표시
                const newsTitles = newsItems.slice(0, 3).map((item, idx) => 
                  `${idx + 1}. ${item.title || '뉴스 제목 없음'}`
                );
                return ["\n📰 당일 주요 뉴스:", ...newsTitles];
              },
            },
          },
        },
        scales: {
          x: {
            type: "time",
            time: {
              unit: timeUnit,
              displayFormats: {
                minute: "HH:mm",
                hour: "MM/dd HH:mm",
                day: "MM/dd",
                week: "MM/dd",
                month: "yyyy/MM",
              },
            },
            ticks: { 
              color: "#9ca3af", 
              font: { size: 11 }, 
              maxTicksLimit: range.value === "rt" ? 12 : 10,
              maxRotation: 0,
            },
            grid: { 
              display: true,
              color: "rgba(55,65,81,0.3)",
              drawBorder: false,
            },
          },
          y: {
            position: "right",
            ticks: { 
              color: "#9ca3af",
              font: { size: 11 },
              callback: function(value) {
                return value.toLocaleString("ko-KR") + "원";
              },
            },
            grid: { 
              color: "rgba(55,65,81,0.3)",
              drawBorder: false,
            },
          },
        },
      },
    });
  } catch (e) {
    console.error("[StockChart] buildChart failed:", e);
  }
}

function changeRange(v) {
  range.value = v;
  candleData.value = []; // 범위 변경 시 데이터 초기화
  newsCache.value = {}; // 뉴스 캐시 초기화
}

// ticker나 range 변경 시 캔들 데이터 로드
watch([() => props.ticker, range], async () => {
  await loadCandleData();
  buildChartSafe();
});

onMounted(() => {
  buildChartSafe();
});

onBeforeUnmount(() => {
  chartInstance?.destroy();
});
</script>

<style scoped>
.chart-wrapper {
  height: 400px;
  position: relative;
}
.chart-legend {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding: 12px;
  font-size: 12px;
  color: #9ca3af;
}
.legend-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.legend-price {
  background: #60a5fa;
}
.legend-sentiment {
  background: #fb923c;
}
.legend-flow {
  background: #4ade80;
}
.tooltip-note {
  text-align: center;
  font-size: 11px;
  color: #6b7280;
  margin-top: 8px;
}
.range-btn {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #9ca3af;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.range-btn:hover {
  background: rgba(255, 255, 255, 0.05);
}
.range-btn.active {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}
</style>
