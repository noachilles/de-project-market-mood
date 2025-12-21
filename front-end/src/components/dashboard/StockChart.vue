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
import "chartjs-adapter-date-fns";

Chart.register(...registerables);

const props = defineProps({
  ticker: { type: String, required: true },
});

const ticker = computed(() => props.ticker);

const chartCanvas = ref(null);
let chartInstance = null;

const range = ref("6m");
const ranges = [
  { value: "rt", label: "실시간" },
  { value: "1d", label: "1일" },
  { value: "1w", label: "1주" },
  { value: "1m", label: "1달" },
  { value: "3m", label: "3달" },
  { value: "6m", label: "6달" },
  { value: "1y", label: "1년" },
];

const labelRange = computed(() => {
  const map = {
    rt: "실시간",
    "1d": "1일",
    "1w": "1주",
    "1m": "1달",
    "3m": "3달",
    "6m": "6달",
    "1y": "1년",
  };
  return map[range.value] ?? "1년";
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

const series = computed(() => {
  const spec = RANGE_SPEC[range.value] ?? RANGE_SPEC["6m"];
  const base = baseByTicker[ticker.value] ?? baseByTicker["005930"];
  return genSeries({
    basePrice: base.price,
    baseSent: base.sentiment,
    baseFlow: base.flow,
    points: spec.points,
    stepMs: spec.stepMs,
  });
});

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
  const spec = RANGE_SPEC[range.value] ?? RANGE_SPEC["6m"];
  const d = series.value;

  try {
    chartInstance?.destroy();
    chartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        datasets: [
          {
            type: "line",
            label: "Price",
            data: d.map((r) => ({ x: r.x, y: r.price })),
            yAxisID: "yPrice",
            borderColor: "#60a5fa",
            backgroundColor: "rgba(96,165,250,0.18)",
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.25,
          },
          {
            type: "line",
            label: "Sentiment",
            data: d.map((r) => ({ x: r.x, y: r.sentiment })),
            yAxisID: "ySentiment",
            borderColor: "#fb923c",
            borderDash: [4, 3],
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.25,
          },
          {
            type: "bar",
            label: "Flow",
            data: d.map((r) => ({ x: r.x, y: r.flow })),
            yAxisID: "yFlow",
            backgroundColor: (ctx) => {
              const v = ctx.raw?.y ?? 0;
              return v >= 0 ? "rgba(74,222,128,0.45)" : "rgba(248,113,113,0.45)";
            },
            borderRadius: 4,
            barPercentage: 0.7,
            categoryPercentage: 0.9,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "rgba(15,23,42,0.96)",
            callbacks: {
              footer: (items) => {
                const idx = items?.[0]?.dataIndex ?? 0;
                const msg = d?.[idx]?.news ?? "뉴스 요약 데이터가 없습니다.";
                return "뉴스 요약: " + msg;
              },
            },
          },
        },
        scales: {
          x: {
            type: "time",
            time: { unit: spec.unit },
            ticks: { color: "#9ca3af", font: { size: 11 }, maxTicksLimit: 8 },
            grid: { display: false },
          },
          yPrice: {
            position: "left",
            ticks: { color: "#9ca3af" },
            grid: { color: "rgba(55,65,81,0.55)" },
          },
          ySentiment: {
            position: "right",
            display: false,
            suggestedMin: 0,
            suggestedMax: 100,
          },
          yFlow: {
            position: "right",
            display: false,
          },
        },
      },
    });
  } catch (e) {
    console.error("[StockChart] buildChart failed:", e);
  }
}

watch([ticker, range], () => {
  buildChartSafe();
});

onMounted(() => {
  buildChartSafe();
});

onBeforeUnmount(() => {
  chartInstance?.destroy();
});

function changeRange(v) {
  range.value = v;
}
</script>

<style scoped>
/* ✅ 차트가 사라지는 1순위 원인: wrapper 높이 0 방지 */
.chart-wrapper {
  min-height: 320px;
}
</style>
