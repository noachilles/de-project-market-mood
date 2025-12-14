<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Real-time Stock ({{ labelRange }})</div>
        <div class="card-sub">Price · Sentiment · Flow 통합 · {{ ticker }}</div>
      </div>

      <div class="range-tabs">
        <button
          v-for="item in ranges"
          :key="item.value"
          class="range-btn"
          :class="{ active: range === item.value }"
          @click="changeRange(item.value)"
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
      차트 위 시점을 마우스로 올리면 해당 시점의 <strong>뉴스 요약</strong>이 표시됩니다.
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch } from "vue";
import { Chart, registerables } from "chart.js";
import "chartjs-adapter-date-fns";

Chart.register(...registerables);

/* ✅ Dashboard에서 받는 ticker */
const props = defineProps({
  ticker: { type: String, required: true },
});

const chartCanvas = ref(null);
let chartInstance = null;

/* ------------------ 기간 ------------------ */
const range = ref("1y");
const ranges = [
  { value: "1d", label: "1일" }, { value: "1w", label: "1주" },
  { value: "1m", label: "1달" }, { value: "3m", label: "3달" },
  { value: "6m", label: "6달" }, { value: "1y", label: "1년" },
  { value: "5y", label: "5년" }, { value: "all", label: "전체" }
];

const labelRange = computed(() => ({
  "1d": "1일", "1w": "1주", "1m": "1달",
  "3m": "3달", "6m": "6달", "1y": "1년",
  "5y": "5년", "all": "전체"
}[range.value]));

/* ------------------ 공통 라벨 ------------------ */
const labelsBase = [
  "1월","2월","3월","4월","5월","6월",
  "7월","8월","9월","10월","11월","12월"
];

/* ------------------ ✅ ticker별 더미 데이터(임시) ------------------ */
const dummyByTicker = {
  "005930": {
    price: [70,72,69,75,78,80,82,86,83,88,90,92],
    sentiment: [40,45,48,55,60,58,62,70,65,72,75,78],
    flow: [50,-20,10,30,60,-10,40,80,-25,35,45,65],
    news: [
      "1월: AI 서버 수요 둔화 우려에도 견조한 실적 전망.",
      "2월: 북미 데이터센터향 신규 HBM 수주 공시.",
      "3월: 매크로 불확실성으로 단기 변동성 확대.",
      "4월: AI GPU 공급 부족, 관련주 동반 강세.",
      "5월: 해외 리포트 Top Pick 선정.",
      "6월: 환율 부담 부각, 외국인 매도.",
      "7월: HBM3E 양산 계획 발표.",
      "8월: 글로벌 빅테크와 장기 공급 계약 기대.",
      "9월: 단기 차익 실현 구간.",
      "10월: 실적 서프라이즈.",
      "11월: 업황 회복 기조.",
      "12월: CAPEX 확대 계획 발표."
    ],
  },
  "000660": {
    // SK하이닉스는 패턴이 좀 다르게 보여주기 (변화 확인용)
    price: [120,118,121,125,130,128,126,132,129,127,131,135],
    sentiment: [55,52,50,48,46,49,51,47,45,44,46,48],
    flow: [-10,-30,5,15,20,-25,-15,10,-40,-5,8,12],
    news: [
      "1월: 메모리 업황 둔화 우려로 약세.",
      "2월: 고객사 재고 조정 이슈 재부각.",
      "3월: 환율 영향으로 변동성 확대.",
      "4월: HBM 관련 기대감 일부 반영.",
      "5월: 공급사와 단가 협상 뉴스.",
      "6월: 기관 매도 우위 지속.",
      "7월: 업황 바닥론 제기.",
      "8월: 경쟁사 증설 우려.",
      "9월: 단기 반등 후 조정.",
      "10월: 실적 컨센서스 하향.",
      "11월: 내년 수요 전망 혼재.",
      "12월: 수주 모멘텀 점검 필요."
    ],
  },
};

/* ------------------ ✅ 현재 ticker 데이터 선택 ------------------ */
const currentData = computed(() => {
  return dummyByTicker[props.ticker] ?? dummyByTicker["005930"];
});

/* ------------------ count 계산 ------------------ */
function getCountByRange(v) {
  return {
    "1d": 1, "1w": 2, "1m": 3,
    "3m": 4, "6m": 6, "1y": 12,
    "5y": 12, "all": 12
  }[v] ?? 12;
}

/* ------------------ 차트 렌더링 ------------------ */
function buildChart(count = 12) {
  if (!chartCanvas.value) return;

  const ctx = chartCanvas.value.getContext("2d");
  const d = currentData.value;

  // ✅ 차트가 이미 있으면 destroy 후 재생성 (확실하게 갱신)
  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labelsBase.slice(0, count),
      datasets: [
        {
          type: "line",
          label: "Price",
          data: d.price.slice(0, count),
          borderColor: "#60a5fa",
          backgroundColor: "rgba(96,165,250,0.25)",
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
          yAxisID: "yPrice",
        },
        {
          type: "line",
          label: "Sentiment",
          data: d.sentiment.slice(0, count),
          borderColor: "#fb923c",
          borderDash: [4, 3],
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.3,
          yAxisID: "ySentiment",
        },
        {
          type: "bar",
          label: "Flow",
          data: d.flow.slice(0, count),
          yAxisID: "yFlow",
          backgroundColor: (ctx) => {
            const v = ctx.raw;
            return v >= 0
              ? "rgba(74,222,128,0.45)"
              : "rgba(248,113,113,0.45)";
          },
          borderRadius: 4,
          barPercentage: 0.65,
          categoryPercentage: 0.75,
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
          borderColor: "rgba(148,163,184,0.8)",
          borderWidth: 1,
          padding: 10,
          titleColor: "#e5e7eb",
          bodyColor: "#e5e7eb",
          footerColor: "#9ca3af",
          callbacks: {
            footer: (items) => {
              const idx = items?.[0]?.dataIndex ?? 0;
              const msg = d.news?.[idx] ?? "뉴스 요약 데이터가 없습니다.";
              return "뉴스 요약: " + msg;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: { color: "#9ca3af", font: { size: 11 } },
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
          suggestedMin: Math.min(...d.flow) - 20,
          suggestedMax: Math.max(...d.flow) + 20,
        },
      },
    },
  });
}

/* ------------------ 기간 변경 ------------------ */
function changeRange(v) {
  range.value = v;
  buildChart(getCountByRange(v));
}

/* ------------------ ✅ ticker/range 변경 감지 ------------------ */
watch(
  () => props.ticker,
  () => {
    // ticker 바뀌면 현재 range 기준으로 다시 그리기
    buildChart(getCountByRange(range.value));
  }
);

watch(
  () => range.value,
  (v) => {
    // range 바뀌면 현재 ticker 기준으로 다시 그리기
    buildChart(getCountByRange(v));
  }
);

/* ------------------ Lifecycle ------------------ */
onMounted(() => buildChart(getCountByRange(range.value)));
onBeforeUnmount(() => chartInstance?.destroy());
</script>
