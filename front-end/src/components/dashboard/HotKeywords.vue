<template>
  <div class="hot-keywords-card">
    <div class="card-header">
      <div class="card-title">🔥 이번 주 Hot 키워드</div>
      <div class="card-sub">{{ period }}</div>
    </div>
    <div class="divider"></div>
    
    <div class="keywords-list" v-if="keywords.length > 0">
      <div 
        v-for="(item, index) in keywords" 
        :key="index"
        class="keyword-item"
      >
        <div class="rank-badge" :class="getRankClass(index)">
          {{ index + 1 }}
        </div>
        <div class="keyword-text">{{ item.keyword }}</div>
        <div class="keyword-count">{{ item.count }}회</div>
      </div>
    </div>
    
    <div class="loading-state" v-else-if="isLoading">
      키워드를 불러오는 중...
    </div>
    
    <div class="empty-state" v-else>
      키워드 데이터가 없습니다.
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";

const API_BASE = "http://localhost:8000";
const keywords = ref([]);
const period = ref("7일");
const isLoading = ref(false);

function getRankClass(index) {
  if (index === 0) return "rank-1";
  if (index === 1) return "rank-2";
  if (index === 2) return "rank-3";
  return "rank-other";
}

async function fetchHotKeywords() {
  isLoading.value = true;
  try {
    const res = await fetch(`${API_BASE}/api/news/hot-keywords/`);
    if (!res.ok) throw new Error("Hot Keywords API 에러");
    const data = await res.json();
    keywords.value = data.keywords || [];
    period.value = data.period || "7일";
  } catch (e) {
    console.warn("⚠️ Hot Keywords 로드 실패:", e);
    keywords.value = [];
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  fetchHotKeywords();
  // 5분마다 갱신
  setInterval(fetchHotKeywords, 5 * 60 * 1000);
});
</script>

<style scoped>
.hot-keywords-card {
  background: rgba(148, 163, 184, 0.1);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #e5e7eb;
}

.card-sub {
  font-size: 12px;
  color: #9ca3af;
}

.divider {
  height: 1px;
  background: rgba(148, 163, 184, 0.1);
  margin-bottom: 12px;
}

.keywords-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.keyword-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.5);
  transition: background 0.2s;
}

.keyword-item:hover {
  background: rgba(15, 23, 42, 0.8);
}

.rank-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.rank-1 {
  background: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
}

.rank-2 {
  background: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
}

.rank-3 {
  background: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
}

.rank-other {
  background: rgba(148, 163, 184, 0.2);
  color: #cbd5e1;
}

.keyword-text {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: #e5e7eb;
}

.keyword-count {
  font-size: 11px;
  color: #9ca3af;
}

.loading-state,
.empty-state {
  padding: 20px;
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
}
</style>


