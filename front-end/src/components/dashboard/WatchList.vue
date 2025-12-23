<script setup>
  import { computed } from "vue";
import YesterdayReportCard from "./YesterdayReportCard.vue";

const props = defineProps({
  items: { type: Array, default: () => [] },
  selectedTicker: { type: String, default: "" },
  yesterdayReport: { type: Object, default: null },
});

const emit = defineEmits(["select", "open-report"]);

const sortedItems = computed(() => {
  const arr = [...(props.items || [])];

  // 1) 변화율 내림차순 정렬
  arr.sort((a, b) => Number(b.change || 0) - Number(a.change || 0));

  // 2) (선택) 선택 종목은 맨 위로
  const idx = arr.findIndex((x) => x.ticker === props.selectedTicker);
  if (idx > 0) {
    const [picked] = arr.splice(idx, 1);
    arr.unshift(picked);
  }

  return arr;
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

<template>
  <!-- 관심종목 리스트 카드 -->
  <div class="card watchlist-card">
    <div class="card-header">
      <div class="card-title">내 관심종목 리스트</div>
      <div class="card-sub">실시간 변화율 기준</div>
    </div>
    <div class="divider"></div>

    <div class="watchlist">
      <div
        v-for="it in sortedItems"
        :key="it.ticker"
        class="watch-item"
        :class="{ active: it.ticker === selectedTicker }"
        @click="emit('select', it.ticker)"
        style="cursor:pointer;"
      >
        <div>
          <div class="watch-symbol">{{ it.name }}</div>
          <div class="watch-price">{{ it.price != null ? formatKRW(it.price) : "로딩…" }}</div>
        </div>
        <div class="watch-change" :class="toneClass(it.change)">
          {{ it.change != null ? formatChange(it.change) : "-" }}
        </div>
      </div>
    </div>
  </div>

  <!-- 전날 분석 리포트 카드 -->
  <YesterdayReportCard
    :report="yesterdayReport"
    @open="emit('open-report')"
  />
</template>
