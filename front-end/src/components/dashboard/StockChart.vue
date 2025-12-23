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

    <div v-if="loading" class="status-line">차트 로딩 중…</div>
    <div v-else-if="errorMsg" class="status-line error">{{ errorMsg }}</div>

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

/**
 * ✅ 백엔드 차트 API
 * GET /api/chart/{code}?range=1d
 * 응답 예:
 * {
 *   code, range,
 *   labels: [ISO...],
 *   price: [..],
 *   volume: [..],
 *   sentiment: [],
 *   flow: []
 * }
 */
async function fetchChart(code, range) {
  const res = await fetch(`http://localhost:8000/api/chart/${code}?range=${range}`);
  if (!res.ok) throw new Error(`Chart API failed: ${res.status}`);
  return await res.json();
}

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

const RANGE_UNIT = {
  rt: "second",
  "1d": "hour",
  "1w": "day",
  "1m": "day",
  "3m": "week",
  "6m": "week",
  "1y": "month",
};

const unit = computed(() => RANGE_UNIT[range.value] ?? "week");

/** ✅ API 데이터를 여기로 적재 */
const series = ref([]); // [{x, price, sentiment, flow, volume, news}]
const loading = ref(false);
const errorMsg = ref("");

/* ✅ 한 프레임 뒤에 실행(레이아웃 0 높이 방지) */
function raf() {
  return new Promise((resolve) => requestAnimationFrame(resolve));
}

async function loadChartData() {
  loading.value = true;
  errorMsg.value = "";
  try {
    const res = await fetchChart(ticker.value, range.value);

    const labels = res.labels || [];
    const prices = res.price || [];
    const vols = res.volume || [];
    const sents = res.sentiment || [];
    const flows = res.flow || [];

    series.value = labels.map((label, i) => {
      const x = new Date(label).getTime();
      const price = Number(prices[i] ?? 0);
      const volume = Number(vols[i] ?? 0);

      const sentiment =
        sents[i] != null && sents[i] !== "" ? Number(sents[i]) : null;

      const flow =
        flows[i] != null && flows[i] !== "" ? Number(flows[i]) : null;

      return {
        x,
        price,
        volume,
        sentiment,
        flow,
        // 현재 API에는 뉴스 요약이 없어서 placeholder (나중에 labels 기준으로 조인하면 됨)
        news: `(${label}) 뉴스 요약: (연동 예정)`,
      };
    });
  } catch (e) {
    console.error("[StockChart] loadChartData failed:", e);
    errorMsg.value = "차트 데이터를 불러오지 못했습니다.";
    series.value = [];
  } finally {
    loading.value = false;
  }
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
  const d = series.value;

  // 데이터가 없으면 차트만 비워두고 종료
  if (!d || d.length === 0) {
    try {
      chartInstance?.destroy();
      chartInstance = null;
    } catch (_) {}
    return;
  }

  // ✅ Flow가 없으면 volume으로 대체(임시)
  const flowOrVolume = d.map((r) => ({
    x: r.x,
    y: Number(r.flow ?? r.volume ?? 0),
  }));

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
            // ✅ sentiment 값 있는 것만 그리기(없으면 라인도 안 보임)
            data: d
              .filter((r) => r.sentiment != null)
              .map((r) => ({ x: r.x, y: r.sentiment })),
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
            data: flowOrVolume,
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
            time: { unit: unit.value },
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

/** ✅ ticker / range 바뀌면: API 재조회 → 차트 rebuild */
watch([ticker, range], async () => {
  await loadChartData();
  await buildChartSafe();
});

/** ✅ 마운트 시 최초 로딩 + (선택) 5초 폴링 */
let timer = null;

onMounted(async () => {
  await loadChartData();
  await buildChartSafe();

  // 실시간 느낌 폴링 (필요 없으면 주석)
  timer = setInterval(async () => {
    await loadChartData();
    await buildChartSafe();
  }, 5000);
});

onBeforeUnmount(() => {
  clearInterval(timer);
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
.status-line {
  padding: 8px 12px;
  color: #9ca3af;
  font-size: 13px;
}
.status-line.error {
  color: #fecaca;
}
</style>
