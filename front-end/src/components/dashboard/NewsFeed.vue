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

    <div v-if="isLoading" class="loading-state">
      <span>🔄 뉴스 로딩 중...</span>
    </div>
    <ul v-else class="news-list">
      <li
        v-for="(news, idx) in newsList"
        :key="idx"
        class="news-item"
        :class="{ 'clickable': news.url }"
        @click="news.url && handleNewsClick(news.url)"
      >
        {{ news.title || news }}
      </li>

      <li v-if="newsList.length === 0" class="news-item muted">
        관련 뉴스가 없습니다.
      </li>
    </ul>
  </div>
</template>

<script setup>
import { computed } from "vue";

/* ✅ Dashboard.vue에서 내려주는 props */
const props = defineProps({
  ticker: {
    type: String,
    required: true,
  },
  items: {
    type: Array,
    default: () => [],
  },
  isLoading: {
    type: Boolean,
    default: false,
  },
});

/* ------------------ 더미 뉴스 데이터 (하위 호환성) ------------------ */
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

/* ------------------ ticker → 종목명 매핑 (임시) ------------------ */
const stockName = computed(() => {
  return {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
  }[props.ticker] ?? props.ticker;
});

/* ------------------ 뉴스 리스트 (props.items 사용) ------------------ */
const newsList = computed(() => {
  // items가 객체 배열인 경우 그대로 사용 (title, original_url 포함)
  if (props.items && props.items.length > 0) {
    return props.items.map(item => ({
      title: item.title || item,
      url: item.original_url || item.url || null,
    }));
  }
  // items가 없으면 더미 데이터 사용 (하위 호환성)
  return (dummyNewsByTicker[props.ticker] ?? []).map(title => ({ title, url: null }));
});

/* ------------------ 뉴스 클릭 핸들러 ------------------ */
function handleNewsClick(url) {
  if (url) {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
}
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

.news-item.clickable {
  cursor: pointer;
  transition: background-color 0.2s;
}

.news-item.clickable:hover {
  background-color: rgba(148, 163, 184, 0.1);
}

.loading-state {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}
</style>
