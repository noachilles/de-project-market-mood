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
          <span>{{ Number(stock.change || 0) >= 0 ? "▲" : "▼" }}</span>
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

    <div class="header-right">
      <div class="pill-tag">
        <span>AI 기반 종목 인사이트</span>
      </div>
      <button class="primary-btn" disabled>
        <span class="icon">✨</span> AI Insights 보기
      </button>
    </div>
  </header>
</template>

<script setup>
const props = defineProps({
  stock: { type: Object, default: () => ({ price: 0, change: 0, vol: 0 }) }
});

const formatKRW = (val) => new Intl.NumberFormat('ko-KR').format(val || 0) + '원';
const formatChange = (val) => {
  const num = Number(val || 0);
  return `${num > 0 ? '+' : ''}${num.toFixed(2)}%`;
};
const toneClass = (val) => (Number(val) > 0 ? 'up' : Number(val) < 0 ? 'down' : '');
</script>

<style scoped>
/* 기존 프로젝트 스타일이 대부분 이미 있을 거라 가정하고,
   여기에는 최소한의 톤만 유지 */
.change-pill.pos { color: #4ade80; }
.change-pill.neg { color: #fecaca; }

/* disabled 버튼이 어색하면 아래만 유지 */
.primary-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
