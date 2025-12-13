<!-- src/components/dashboard/NewsFeed.vue -->
<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">뉴스 피드</div>
        <div class="card-sub">{{ stockName }} · 실시간 뉴스</div>
      </div>
    </div>

    <div class="divider"></div>

    <ul class="news-list">
      <li
        v-for="(news, idx) in newsList"
        :key="idx"
        class="news-item"
      >
        {{ news }}
      </li>

      <li v-if="newsList.length === 0" class="news-item muted">
        관련 뉴스가 없습니다.
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";

/* ✅ Dashboard.vue에서 내려주는 ticker */
const props = defineProps({
  ticker: {
    type: String,
    required: true,
  },
});

/* ------------------ ticker → 종목명 매핑 (임시) ------------------ */
const stockName = computed(() => {
  return {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
  }[props.ticker] ?? props.ticker;
});

/* ------------------ 뉴스 리스트 ------------------ */
const newsList = ref([]);

/* ------------------ 더미 뉴스 데이터 ------------------ */
const dummyNewsByTicker = {
  "005930": [
    "🔥 [속보] 삼성전자 HBM 신제품 출시",
    "📈 외국인 반도체 업종 순매수 확대",
    "🧠 AI 서버 투자 확대 수혜 기대",
    "💬 증권가 “하반기 실적 개선 본격화”",
  ],
  "000660": [
    "📉 메모리 업황 둔화 우려 재부각",
    "🏭 SK하이닉스 HBM 증설 속도 조절",
    "💬 기관, 반도체주 차익 실현",
    "🔍 내년 수요 회복 시점 주목",
  ],
};

/* ------------------ ticker 변경 감지 ------------------ */
watch(
  () => props.ticker,
  (newTicker) => {
    // 🔄 실제 API 연동 시 이 부분을 axios 호출로 교체
    newsList.value = dummyNewsByTicker[newTicker] ?? [];
  },
  { immediate: true }
);
</script>

<style scoped>
.news-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.news-item {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(148,163,184,0.15);
  font-size: 13px;
  color: #e5e7eb;
}

.news-item:last-child {
  border-bottom: none;
}

.news-item.muted {
  color: #9ca3af;
  font-style: italic;
}
</style>
