<template>
  <div class="stocks-shell">
    <!-- 페이지 헤더 -->
    <div class="page-head card">
      <div>
        <div class="title">전체 종목</div>
        <div class="sub">종목을 선택하면 대시보드로 이동합니다</div>
      </div>

      <div class="kpi">
        <div class="kpi-item">
          <div class="kpi-label">전체</div>
          <div class="kpi-val">{{ filtered.length }}</div>
        </div>
        <div class="kpi-item">
          <div class="kpi-label">상승</div>
          <div class="kpi-val pos">{{ upCount }}</div>
        </div>
        <div class="kpi-item">
          <div class="kpi-label">하락</div>
          <div class="kpi-val neg">{{ downCount }}</div>
        </div>
      </div>
    </div>

    <!-- 컨트롤 영역 -->
    <div class="controls card">
      <div class="search">
        <input
          v-model.trim="query"
          type="text"
          placeholder="종목명 또는 코드 검색 (예: 삼성, 005930)"
        />
      </div>

      <div class="sort">
        <label>정렬</label>
        <select v-model="sortKey">
          <option value="change">등락률</option>
          <option value="price">현재가</option>
          <option value="volume">거래량</option>
        </select>

        <select v-model="sortDir">
          <option value="desc">내림차순</option>
          <option value="asc">오름차순</option>
        </select>
      </div>
    </div>

    <!-- 리스트 -->
    <div class="card list-card">
      <div class="card-header-row">
        <div class="card-title">종목 리스트</div>
        <div class="card-sub">클릭하여 대시보드로 이동</div>
      </div>

      <div class="divider"></div>

      <div class="table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th style="width: 34%">종목명</th>
              <th style="width: 16%">코드</th>
              <th style="width: 18%">현재가</th>
              <th style="width: 16%">등락률</th>
              <th style="width: 16%">거래량</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="s in paged"
              :key="s.ticker"
              class="row"
              @click="goDashboard(s.ticker)"
            >
              <td class="name">{{ s.name }}</td>
              <td class="ticker">{{ s.ticker }}</td>
              <td class="num">{{ formatKRW(s.price) }}</td>
              <td class="change" :class="s.change >= 0 ? 'pos' : 'neg'">
                {{ formatChange(s.change) }}
              </td>
              <td class="num">{{ formatVolume(s.volume) }}</td>
            </tr>

            <tr v-if="paged.length === 0">
              <td colspan="5" class="empty">
                검색 결과가 없습니다.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 페이지네이션 (MVP) -->
      <div class="pager" v-if="filtered.length > pageSize">
        <button class="pager-btn" :disabled="page === 1" @click="page--">이전</button>
        <div class="pager-info">{{ page }} / {{ totalPages }}</div>
        <button class="pager-btn" :disabled="page === totalPages" @click="page++">다음</button>

        <select class="page-size" v-model.number="pageSize">
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

/* ------------------ 더미 데이터 (나중에 API로 교체) ------------------ */
const stocks = ref([
  { ticker: "005930", name: "삼성전자", price: 85300, change: 2.55, volume: 1250000 },
  { ticker: "000660", name: "SK하이닉스", price: 135000, change: -1.15, volume: 980000 },
  { ticker: "035420", name: "NAVER", price: 212000, change: 0.35, volume: 220000 },
  { ticker: "035720", name: "카카오", price: 57500, change: -0.62, volume: 410000 },
  { ticker: "051910", name: "LG화학", price: 412000, change: 1.12, volume: 90000 },
]);

/* ------------------ 검색/정렬 ------------------ */
const query = ref("");
const sortKey = ref("change");
const sortDir = ref("desc");

/* 검색 결과 바뀌면 페이지 1로 */
watch([query, sortKey, sortDir], () => { page.value = 1; });

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase();
  const base = !q
    ? stocks.value
    : stocks.value.filter((s) => {
        return (
          s.name.toLowerCase().includes(q) ||
          s.ticker.toLowerCase().includes(q)
        );
      });

  const dir = sortDir.value === "asc" ? 1 : -1;

  return [...base].sort((a, b) => {
    const av = a[sortKey.value];
    const bv = b[sortKey.value];
    if (av === bv) return 0;
    return av > bv ? dir : -dir;
  });
});

/* KPI */
const upCount = computed(() => filtered.value.filter((s) => s.change > 0).length);
const downCount = computed(() => filtered.value.filter((s) => s.change < 0).length);

/* ------------------ Pagination ------------------ */
const page = ref(1);
const pageSize = ref(20);

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filtered.value.length / pageSize.value))
);

const paged = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return filtered.value.slice(start, start + pageSize.value);
});

/* ------------------ 네비게이션 ------------------ */
function goDashboard(ticker) {
  router.push({ path: "/dashboard", query: { ticker } });
}

/* ------------------ 포맷 ------------------ */
function formatKRW(n) {
  return Number(n || 0).toLocaleString("ko-KR") + "원";
}
function formatChange(v) {
  const num = Number(v || 0);
  return (num >= 0 ? "+" : "") + num.toFixed(2) + "%";
}
function formatVolume(v) {
  return Number(v || 0).toLocaleString("ko-KR");
}
</script>

<style scoped>
.stocks-shell {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 20px 30px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* card base (대시보드 카드 톤 맞추기) */
.card {
  background: rgba(17, 34, 64, 0.68);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  padding: 14px;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.title {
  font-size: 18px;
  font-weight: 800;
  color: #e6edff;
}
.sub {
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
}
.kpi {
  display: flex;
  gap: 10px;
}
.kpi-item {
  padding: 8px 10px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.06);
  min-width: 74px;
  text-align: center;
}
.kpi-label {
  font-size: 11px;
  color: #9ca3af;
}
.kpi-val {
  font-size: 16px;
  font-weight: 900;
  color: #e6edff;
}
.pos { color: #4ade80; }
.neg { color: #fecaca; }

/* controls */
.controls {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}
.search input {
  width: 340px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: 12px;
  padding: 10px 12px;
  outline: none;
  color: #e6edff;
}
.sort {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cbd5f5;
  font-size: 12px;
}
.sort select {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.10);
  color: #e6edff;
  border-radius: 10px;
  padding: 8px 10px;
  outline: none;
}

/* list */
.list-card { padding: 14px; }
.card-header-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}
.card-title { font-size: 16px; font-weight: 800; color: #e6edff; }
.card-sub { font-size: 12px; color: #9ca3af; }

.divider {
  height: 1px;
  background: rgba(255,255,255,0.10);
  margin: 12px 0;
}

.table-wrap { overflow-x: auto; }
.table {
  width: 100%;
  border-collapse: collapse;
  color: #e6edff;
  font-size: 13px;
}
th {
  text-align: left;
  font-size: 12px;
  color: #9ca3af;
  padding: 10px 8px;
  border-bottom: 1px solid rgba(255,255,255,0.10);
}
td {
  padding: 12px 8px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.row { cursor: pointer; }
.row:hover { background: rgba(255,255,255,0.06); }

.name { font-weight: 800; }
.ticker { color: #cbd5f5; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.num { text-align: right; }
.change { text-align: right; font-weight: 800; }

.empty {
  text-align: center;
  padding: 22px 8px;
  color: #9ca3af;
}

/* pager */
.pager {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  padding-top: 12px;
}
.pager-btn {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: #e6edff;
  border-radius: 10px;
  padding: 8px 10px;
  cursor: pointer;
}
.pager-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.pager-info {
  color: #cbd5f5;
  font-size: 12px;
}
.page-size {
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  color: #e6edff;
  border-radius: 10px;
  padding: 8px 10px;
  outline: none;
}
</style>
