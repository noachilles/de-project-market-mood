<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">Real-time Stock ({{ labelRange }})</div>
        <div class="card-sub">Price · Sentiment · Flow 통합</div>
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
import { ref, onMounted, onBeforeUnmount, computed } from "vue";
import { Chart, registerables } from "chart.js";
import "chartjs-adapter-date-fns";

Chart.register(...registerables);

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

/* ------------------ 데이터 ------------------ */
const labels = [
  "1월","2월","3월","4월","5월","6월",
  "7월","8월","9월","10월","11월","12월"
];

// Price line
const priceData = [70,72,69,75,78,80,82,86,83,88,90,92];

// Sentiment line (dotted)
const sentimentData = [40,45,48,55,60,58,62,70,65,72,75,78];

// Flow bar
const flowData = [50,-20,10,30,60,-10,40,80,-25,35,45,65];

// Tooltip text
const newsSummaries = [
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
];

/* ------------------ 차트 렌더링 ------------------ */
function buildChart(count = 12) {
  if (chartInstance) chartInstance.destroy();

  const ctx = chartCanvas.value.getContext("2d");

  chartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels.slice(0, count),
      datasets: [
        /* ====== 1) Price Line (파란선) ====== */
        {
          type: "line",
          label: "Price",
          data: priceData.slice(0, count),
          borderColor: "#60a5fa",
          backgroundColor: "rgba(96,165,250,0.25)",
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
          yAxisID: "yPrice",
        },

        /* ====== 2) Sentiment Line (주황 점선) ====== */
        {
          type: "line",
          label: "Sentiment",
          data: sentimentData.slice(0, count),
          borderColor: "#fb923c",
          borderDash: [4, 3],
          borderWidth: 2,
          pointRadius: 2,
          tension: 0.3,
          yAxisID: "ySentiment"
        },

        /* ====== 3) Flow Bar (빨/초 막대) ====== */
        {
          type: "bar",
          label: "Flow",
          data: flowData.slice(0, count),
          yAxisID: "yFlow",
          backgroundColor: (ctx) => {
            const v = ctx.raw;
            return v >= 0
              ? "rgba(74,222,128,0.45)"   // 초록
              : "rgba(248,113,113,0.45)"; // 빨강
          },
          borderRadius: 4,
          barPercentage: 0.65,
          categoryPercentage: 0.75
        }
      ]
    },

    options: {
      responsive: true,
      maintainAspectRatio: false,

      interaction: {
        mode: "index",
        intersect: false
      },

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
              const idx = items[0].dataIndex;
              return "뉴스 요약: " + newsSummaries[idx];
            }
          }
        }
      },

      scales: {
        x: {
          ticks: { color: "#9ca3af", font: { size: 11 } },
          grid: { display: false }
        },

        /* Price */
        yPrice: {
          position: "left",
          ticks: { color: "#9ca3af" },
          grid: { color: "rgba(55,65,81,0.55)" }
        },

        /* Sentiment */
        ySentiment: {
          position: "right",
          display: false,
          suggestedMin: 0,
          suggestedMax: 100
        },

        /* Flow */
        yFlow: {
          position: "right",
          display: false,
          suggestedMin: Math.min(...flowData) - 20,
          suggestedMax: Math.max(...flowData) + 20
        }
      }
    }
  });
}

/* ------------------ 기간 변경 ------------------ */
function changeRange(v) {
  range.value = v;
  const count = {
    "1d": 1, "1w": 2, "1m": 3,
    "3m": 4, "6m": 6, "1y": 12,
    "5y": 12, "all": 12
  }[v];

  buildChart(count);
}

/* ------------------ Lifecycle ------------------ */
onMounted(() => buildChart(12));
onBeforeUnmount(() => chartInstance?.destroy());
</script>
