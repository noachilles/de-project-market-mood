<!-- src/components/dashboard/MyHolding.vue -->
<script setup>
import { computed } from "vue";

/**
 * holding 예시
 * {
 *   symbol: "삼성전자",
 *   avgPrice: 72000,   // 매입 단가
 *   quantity: 100,     // 보유 수량
 *   currentPrice: 85300 // 현재가 (평가금액/손익 계산용)
 * }
 */
const props = defineProps({
  holding: {
    type: Object,
    default: () => ({
      symbol: "삼성전자",
      avgPrice: 72000,
      quantity: 100,
      currentPrice: 85300,
    }),
  },
});

const marketValue = computed(() => props.holding.currentPrice * props.holding.quantity);
const costValue = computed(() => props.holding.avgPrice * props.holding.quantity);
const pnl = computed(() => marketValue.value - costValue.value);

const pnlRate = computed(() => {
  if (costValue.value === 0) return 0;
  return (pnl.value / costValue.value) * 100;
});

const pnlClass = computed(() => (pnl.value >= 0 ? "pos" : "neg"));

function formatKRW(n) {
  return Number(n || 0).toLocaleString("ko-KR") + "원";
}
</script>

<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">나의 보유 종목</div>
      <div class="card-sub">‘{{ holding.symbol }}’ 개별 포지션 요약</div>
    </div>

    <div class="divider"></div>

    <!-- ✅ mockup.html의 holding-grid 구조 -->
    <div class="holding-grid">
      <div class="holding-item">
        <div class="holding-label">매입 단가</div>
        <div class="holding-value">{{ formatKRW(holding.avgPrice) }}</div>
      </div>

      <div class="holding-item">
        <div class="holding-label">보유 수량</div>
        <div class="holding-value">{{ holding.quantity.toLocaleString("ko-KR") }}주</div>
      </div>

      <div class="holding-item">
        <div class="holding-label">평가 금액</div>
        <div class="holding-value">{{ formatKRW(marketValue) }}</div>
      </div>

      <div class="holding-item">
        <div class="holding-label">평가 손익</div>
        <div class="holding-value" :class="pnlClass">
          {{ pnl >= 0 ? "+" : "" }}{{ formatKRW(pnl) }}
          ({{ pnlRate >= 0 ? "+" : "" }}{{ pnlRate.toFixed(1) }}%)
        </div>
      </div>
    </div>

    <!-- (옵션) mockup처럼 하단 설명 한 줄 -->
    <div class="report-text" style="margin-top:8px;">
      손절 기준 <strong>-3%</strong>, 일부 익절 기준 <strong>+15%</strong>로 저장되어 있으며,
      조건 충족 시 시그널 알림으로 안내합니다.
    </div>
  </div>
</template>

<style scoped>
/* 프로젝트에 이미 전역 스타일이 있다면 이 스타일은 생략해도 됨.
   (mockup.html과 동일한 클래스명 사용: holding-grid/item/label/value) */
.holding-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  margin-top: 6px;
  font-size: 12px;
}
.holding-item {
  padding: 6px 8px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(55, 65, 81, 0.9);
}
.holding-label {
  font-size: 11px;
  color: #9ca3af;
  margin-bottom: 2px;
}
.holding-value {
  font-weight: 600;
  color: #e5e7eb;
}
.holding-value.pos {
  color: #4ade80;
}
.holding-value.neg {
  color: #fecaca;
}
</style>
