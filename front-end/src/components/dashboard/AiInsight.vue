<!-- src/components/dashboard/AiInsight.vue -->
<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">AI 인사이트</div>
      <div class="card-sub">
        오늘의 판단:
        <span :class="toneClass">{{ insight.toneLabel }}</span>
      </div>
    </div>
    <div class="divider"></div>

    <div class="ai-summary">
      <p>{{ insight.summary }}</p>
      <ul class="ai-bullets" v-if="insight.bullets?.length">
        <li v-for="(b, i) in insight.bullets" :key="i">{{ b }}</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";

const props = defineProps({
  ticker: { type: String, required: true },
});

const dummyInsightByTicker = {
  "005930": {
    tone: "pos",
    toneLabel: "긍정",
    summary:
      "삼성전자는 기관·외국인 매수세와 긍정 뉴스 비중 증가로 단기 상승 신호가 우세합니다.",
    bullets: [
      "수급: 외국인·기관 동반 순매수",
      "감정: 긍정 기사 비중 확대",
      "리스크: 단기 과열 구간만 주의",
    ],
  },
  "000660": {
    tone: "neg",
    toneLabel: "주의",
    summary:
      "SK하이닉스는 단기 수급 약화와 변동성 확대로 보수적 접근이 필요합니다.",
    bullets: [
      "수급: 기관 매도 우위",
      "감정: 부정 헤드라인 증가",
      "전략: 분할 접근 또는 추세 확인 후 대응",
    ],
  },
};

const insight = ref({
  tone: "neutral",
  toneLabel: "중립",
  summary: "인사이트를 불러오는 중…",
  bullets: [],
});

const toneClass = computed(() => {
  return insight.value.tone === "pos"
    ? "pos"
    : insight.value.tone === "neg"
    ? "neg"
    : "neutral";
});

watch(
  () => props.ticker,
  (t) => {
    // 🔄 실제 API 연동 시 이 부분만 axios로 교체
    insight.value =
      dummyInsightByTicker[t] ?? {
        tone: "neutral",
        toneLabel: "중립",
        summary: "해당 종목의 인사이트 데이터가 없습니다.",
        bullets: [],
      };
  },
  { immediate: true }
);
</script>

<style scoped>
/* 헤더 톤 표시 */
.pos { color: #4ade80; font-weight: 700; }
.neg { color: #fecaca; font-weight: 700; }
.neutral { color: #e5e7eb; font-weight: 700; }

.ai-summary p {
  margin: 0;
  line-height: 1.55;
  color: #e5e7eb;
  font-size: 13px;
}

.ai-bullets {
  margin: 10px 0 0;
  padding-left: 16px;
  color: #cbd5f5;
  font-size: 12px;
}

.ai-bullets li {
  margin: 4px 0;
}
</style>
