<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">뉴스 피드</div>
        <div class="card-sub">{{ stockName }} 관련 최신 뉴스</div>
      </div>
    </div>

    <div class="divider"></div>

    <div v-if="loading" class="p-3 muted">불러오는 중…</div>

    <ul v-else class="news-list">
      <li v-for="n in items" :key="n.id" class="news-item">
        <a :href="n.link" target="_blank" rel="noreferrer" class="news-title">
          {{ n.title }}
        </a>
        <div class="news-meta">
          <span>{{ n.source }}</span>
          <span>·</span>
          <span>{{ formatDate(n.published_at) }}</span>
        </div>
      </li>

      <li v-if="items.length === 0" class="news-item muted">
        {{ stockName }} 관련 뉴스가 없습니다.
      </li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import axios from "axios";

/**
 * Dashboard.vue에서 ticker 내려주기 (추천)
 * <NewsFeed :ticker="selectedTicker" />
 */
const props = defineProps({
  ticker: { type: String, required: true },
});

const STOCK_NAME_BY_TICKER = {
  "005930": "삼성전자",
  "000660": "SK하이닉스",
  // 필요하면 계속 추가
};

const stockName = computed(() => STOCK_NAME_BY_TICKER[props.ticker] ?? props.ticker);

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api",
});

const items = ref([]);
const loading = ref(false);

function formatDate(s) {
  if (!s) return "";
  return new Date(s).toLocaleString("ko-KR");
}

/** 프론트에서 한 번 더 포함 필터(백엔드 검색이 애매할 때 대비) */
function filterByContains(list, keyword) {
  const k = (keyword || "").trim();
  if (!k) return list;
  return (list || []).filter((x) => {
    const t = (x.title || "").toLowerCase();
    const c = (x.content || "").toLowerCase();
    const kk = k.toLowerCase();
    return t.includes(kk) || c.includes(kk);
  });
}

async function loadRelatedNews() {
  loading.value = true;
  try {
    // ✅ 백엔드 검색(q=종목명)으로 우선 가져오기
    const { data } = await api.get("/news/", {
      params: { q: stockName.value, page: 1, size: 20 },
    });

    // ✅ 한번 더 “포함” 기준으로 필터링 (정확도 강화)
    const filtered = filterByContains(data.items || [], stockName.value);

    // 너무 많으면 상위 10개만
    items.value = filtered.slice(0, 10);
  } catch (e) {
    console.error("❌ news api error:", e);
    items.value = [];
  } finally {
    loading.value = false;
  }
}

// ticker 바뀔 때마다 자동 로드
watch(
  () => props.ticker,
  () => loadRelatedNews(),
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
  padding: 10px 12px;
  border-bottom: 1px solid rgba(148,163,184,0.15);
  font-size: 13px;
  color: #e5e7eb;
}

.news-item:last-child {
  border-bottom: none;
}

.news-title {
  display: block;
  font-weight: 600;
  color: inherit;
  text-decoration: none;
}

.news-title:hover {
  text-decoration: underline;
}

.news-meta {
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.75;
}

.muted {
  color: #9ca3af;
  font-style: italic;
}
</style>
