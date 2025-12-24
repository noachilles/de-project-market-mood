<<<<<<< HEAD
=======
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

>>>>>>> origin/develop
<script setup>
import { ref, watch, onMounted } from "vue";
import { Chart, registerables } from "chart.js";
import "chartjs-adapter-date-fns";

Chart.register(...registerables);

const props = defineProps({
  ticker: String,
  liveData: Array,
  news: Array // Dashboard에서 넘겨받은 뉴스 더미
});

const chartCanvas = ref(null);
let chartInstance = null;
const currentRange = ref("rt");

<<<<<<< HEAD
// 더미 캔들 데이터 생성 (Open, High, Low, Close)
function getCandleDummy(count) {
  const data = [];
  const now = Date.now();
  for (let i = count; i > 0; i--) {
    const base = 111000 + Math.random() * 1000;
    data.push({
      x: new Date(now - i * 24 * 3600 * 1000),
      o: base,
      h: base + 300,
      l: base - 300,
      c: base + (Math.random() > 0.5 ? 200 : -200),
      newsSummary: props.news[i % props.news.length].title // 호버 시 보여줄 뉴스
    });
  }
  return data;
}

function initChart() {
  const ctx = chartCanvas.value.getContext("2d");
  chartInstance = new Chart(ctx, {
    type: "line",
    data: {
      datasets: [{
        label: "Price",
        data: props.liveData,
        borderColor: "#10b981",
        backgroundColor: "rgba(16, 185, 129, 0.2)",
        borderWidth: 2,
        pointRadius: 4,
        fill: true,
        tension: 0.1,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: { type: 'time', time: { unit: 'minute' }, grid: { display: false }, ticks: { color: '#9ca3af' } },
        y: { 
          beginAtZero: false, 
          ticks: { stepSize: 500, color: '#9ca3af' }, 
          grid: { color: 'rgba(255,255,255,0.05)' } 
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1f2937',
          titleColor: '#60a5fa',
          bodyColor: '#fff',
          padding: 12,
          cornerRadius: 8,
          callbacks: {
            label: (ctx) => `가격: ${ctx.raw.y?.toLocaleString() || ctx.raw.c?.toLocaleString()}원`,
            footer: (items) => {
              const raw = items[0].raw;
              return raw.newsSummary ? `\n📰 뉴스 요약:\n${raw.newsSummary}` : "";
            }
          }
        }
      }
    }
  });
}

function updateChart() {
  if (!chartInstance) return;
  
  if (currentRange.value === "rt") {
    chartInstance.data.datasets[0].type = "line";
    chartInstance.data.datasets[0].data = props.liveData;
    chartInstance.data.datasets[0].pointRadius = 4;
    const latest = props.liveData.length > 0 ? props.liveData[props.liveData.length-1].y : 111200;
    chartInstance.options.scales.y.min = latest - 1000;
    chartInstance.options.scales.y.max = latest + 1000;
  } else {
    // 캔들 모사 (Bar 형태 활용)
    const dummy = getCandleDummy(currentRange.value === '1w' ? 7 : 30);
    chartInstance.data.datasets[0].type = "bar"; // 캔들 느낌을 위해 Bar로 변경 가능
    chartInstance.data.datasets[0].data = dummy.map(d => ({ x: d.x, y: d.c, newsSummary: d.newsSummary }));
    chartInstance.options.scales.y.min = undefined;
    chartInstance.options.scales.y.max = undefined;
  }
  chartInstance.update('none');
=======
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
>>>>>>> origin/develop
}

watch(() => props.liveData, updateChart, { deep: true });

onMounted(initChart);
</script>

<template>
  <div class="chart-card">
    <div class="chart-header">
      <h3 class="title">Market Flow</h3>
      <div class="range-selector">
        <button v-for="r in ['rt', '1w', '1m', '3m']" :key="r" 
                @click="currentRange = r; updateChart()" 
                :class="{ active: currentRange === r }">
          {{ r.toUpperCase() }}
        </button>
      </div>
    </div>
    <div class="canvas-container">
      <canvas ref="chartCanvas"></canvas>
    </div>
  </div>
</template>

<style scoped>
.chart-card { background: rgba(15, 23, 42, 0.9); border: 1px solid #1f2937; border-radius: 16px; padding: 24px; height: 100%; }
.chart-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.title { color: #f3f4f6; font-size: 1.1rem; margin: 0; }
.range-selector { display: flex; background: #1f2937; padding: 4px; border-radius: 8px; }
button { 
  background: transparent; color: #9ca3af; border: none; padding: 6px 12px; 
  border-radius: 6px; cursor: pointer; font-size: 12px; transition: 0.3s;
}
<<<<<<< HEAD
button.active { background: #3b82f6; color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
.canvas-container { height: 320px; }
</style>
=======
</style>
>>>>>>> origin/develop
