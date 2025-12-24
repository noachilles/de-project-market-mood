<template>
  <!-- stock이 아직 없거나 로딩 중이면 fallback -->
  <header class="header" v-if="stock">
    <div class="header-left">
      <div class="ticker-row">
        <div class="symbol">{{ stock.name }}</div>
        <div class="code">({{ stock.ticker }})</div>
      </div>

      <div class="price-row">
        <div class="price-main">{{ formatKRW(stock.price) }}</div>

        <div class="change-pill" :class="toneClass(stock.change)">
          <span>{{ stock.change >= 0 ? "▲" : "▼" }}</span>
          <span>{{ formatChange(stock.change) }}</span>
        </div>

        <div class="volume">
          거래량: {{ (stock.vol || 0).toLocaleString("ko-KR") }}주
        </div>
      </div>
    </div>

    <div class="header-right">
      <div class="pill-tag">
        <span></span>
      </div>
      <button class="primary-btn">
        <span class="icon">✨</span> AI 챗봇 이용하기
      </button>
    </div>
  </header>

  <!-- fallback UI (에러 방지용) -->
  <header class="header" v-else>
    <div class="header-left">
      <div class="ticker-row">
        <div class="symbol">종목 로딩 중…</div>
      </div>
    </div>
  </header>
</template>

<script setup>
const props = defineProps({
<<<<<<< HEAD
  stock: { type: Object, default: () => ({ price: 0, change: 0, vol: 0 }) }
});

const formatKRW = (val) => new Intl.NumberFormat('ko-KR').format(val || 0) + '원';
const formatChange = (val) => {
  const num = Number(val || 0);
  return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`;
};
const toneClass = (val) => (Number(val) > 0 ? 'up' : Number(val) < 0 ? 'down' : '');
=======
  stock: {
    type: Object,
    default: null, // ✅ required 제거 + 안전 처리
  },
});

function formatKRW(n) {
  return Number(n || 0).toLocaleString("ko-KR") + "원";
}
function formatChange(v) {
  const num = Number(v || 0);
  return (num >= 0 ? "+" : "") + num.toFixed(2) + "%";
}
function toneClass(v) {
  return Number(v || 0) >= 0 ? "pos" : "neg";
}
>>>>>>> origin/develop
</script>

<style scoped>
.change-pill.pos { color: #4ade80; }
.change-pill.neg { color: #fecaca; }
</style>
