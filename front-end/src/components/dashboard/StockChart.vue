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
button.active { background: #3b82f6; color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); }
.canvas-container { height: 320px; }
</style>