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
</script>

<style scoped>
.change-pill.pos { color: #4ade80; }
.change-pill.neg { color: #fecaca; }
</style>
