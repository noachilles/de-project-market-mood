<template>
  <header class="global-header">
    <div class="header-content">
      <!-- 왼쪽: 로고 -->
      <div class="left-area">
        <div class="logo" @click="goDashboard">MarketMood</div>

        <button
          v-if="route.path !== '/stocks'"
          class="nav-btn"
          @click="goStocks"
        >
          📋 전체 종목
        </button>
      </div>

      <!-- 오른쪽: 검색창 + 로그인/유저메뉴 -->
      <div class="right-area">
        <!-- ✅ 상단 검색창(자동완성 드롭다운 포함) -->
        <div class="search-box" ref="searchRef" @keydown.esc="closeSuggest">
          <input
            type="text"
            v-model="keyword"
            placeholder="종목명 또는 코드 검색"
            @focus="openSuggestIfAny"
            @input="onInput"
            @keydown.down.prevent="move(1)"
            @keydown.up.prevent="move(-1)"
            @keydown.enter.prevent="enterPick"
            @blur="onBlur"
          />

          <button @click="searchClick">
            <span class="search-icon">🔍</span>
          </button>

          <!-- hint -->
          <div v-if="loading" class="search-hint">검색 중…</div>

          <!-- dropdown -->
          <ul v-if="open && results.length" class="search-dropdown">
            <li
              v-for="(it, idx) in results"
              :key="it.code"
              class="search-item"
              :class="{ active: idx === activeIndex }"
              @mousedown.prevent="pick(it)"
            >
              <span class="nm">{{ it.name }}</span>
              <span class="cd">{{ it.code }}</span>
            </li>
          </ul>

          <!-- empty -->
          <div v-if="open && !loading && keyword.trim() && results.length === 0" class="search-empty">
            검색 결과가 없습니다.
          </div>
        </div>

        <!-- ✅ 로그인 전 -->
        <button v-if="!isLoggedIn" class="login-btn" @click="openLogin">
          로그아웃
        </button>

        <!-- ✅ 로그인 후: 유저 드롭다운 -->
        <div v-else class="user-menu" ref="menuRef">
          <button class="user-btn" @click="toggleMenu">
            <span class="user-name">{{ authUser?.username }}님</span>
            <span class="caret">▾</span>
          </button>

          <div v-if="isMenuOpen" class="dropdown">
            <button class="dropdown-item" @click="goMyPage">
              👤 마이페이지 (준비중)
            </button>
            <button class="dropdown-item" @click="goSettings">
              ⚙️ 설정 (준비중)
            </button>
            <div class="dropdown-divider"></div>
            <button class="dropdown-item danger" @click="logout">
              🚪 로그아웃
            </button>
          </div>
        </div>

        <!-- 로그인 모달 -->
        <LoginModal
          v-if="isLoginOpen"
          @close="closeLogin"
          @submit="handleLoginSubmit"
        />
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import LoginModal from "@/components/auth/LoginModal.vue";
import { useRouter, useRoute } from "vue-router";

/* 라우터 */
const router = useRouter();
const route = useRoute();

function goStocks() {
  router.push("/stocks");
}
function goDashboard() {
  router.push("/dashboard");
}

/* =========================
   ✅ Stock Search (ES via Django API)
========================= */
const API_BASE = "http://localhost:8000";

const searchRef = ref(null);
const keyword = ref("");
const results = ref([]);
const open = ref(false);
const loading = ref(false);
const activeIndex = ref(-1);

let debounceTimer = null;

async function fetchStockSuggestions(q) {
  const url = `${API_BASE}/api/stocks/search?q=${encodeURIComponent(q)}&size=8`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`stocks/search failed: ${res.status}`);
  return await res.json(); // { items: [{code,name}, ...] }
}

function onInput() {
  clearTimeout(debounceTimer);

  const q = (keyword.value || "").trim();
  if (!q) {
    results.value = [];
    open.value = false;
    loading.value = false;
    activeIndex.value = -1;
    return;
  }

  debounceTimer = setTimeout(async () => {
    loading.value = true;
    try {
      const data = await fetchStockSuggestions(q);
      results.value = data.items ?? [];
      open.value = true;
      activeIndex.value = results.value.length ? 0 : -1;
    } catch (e) {
      console.error("[GlobalHeader] stock search error:", e);
      results.value = [];
      open.value = true; // 결과 없음 UI 보여주고 싶으면 true 유지
      activeIndex.value = -1;
    } finally {
      loading.value = false;
    }
  }, 200);
}

function openSuggestIfAny() {
  if (results.value.length > 0) open.value = true;
}

function closeSuggest() {
  open.value = false;
  activeIndex.value = -1;
}

function onBlur() {
  // 클릭 선택(mousedown) 처리 후 닫히도록 살짝 딜레이
  setTimeout(() => closeSuggest(), 120);
}

function move(dir) {
  if (!open.value || results.value.length === 0) return;
  const next = activeIndex.value + dir;
  if (next < 0) activeIndex.value = results.value.length - 1;
  else if (next >= results.value.length) activeIndex.value = 0;
  else activeIndex.value = next;
}

function enterPick() {
  if (!open.value) {
    searchClick();
    return;
  }
  if (results.value.length === 0) return;
  const idx = activeIndex.value >= 0 ? activeIndex.value : 0;
  pick(results.value[idx]);
}

function searchClick() {
  // 엔터/돋보기 클릭 시: 첫 번째 결과가 있으면 선택
  const q = (keyword.value || "").trim();
  if (!q) return;

  if (results.value.length > 0) {
    pick(results.value[0]);
    return;
  }

  // 결과가 아직 없을 때는 그냥 드롭다운 열어두기(또는 안내)
  open.value = true;
}

function pick(item) {
  // ✅ 선택 시 대시보드로 이동 + code 전달
  // Dashboard.vue가 route.query.code를 읽어서 selectedTicker를 바꾸면 됨
  keyword.value = "";
  results.value = [];
  closeSuggest();

  if (route.path !== "/dashboard") {
    router.push({ path: "/dashboard", query: { code: item.code } });
  } else {
    router.replace({ query: { ...route.query, code: item.code } });
  }
}

/* =========================
   ✅ Auth / Menu (기존 그대로)
========================= */

/* 모달 상태 */
const isLoginOpen = ref(false);
function openLogin() { isLoginOpen.value = true; }
function closeLogin() { isLoginOpen.value = false; }

/* mock auth 상태 */
const authUser = ref(null); // { username: string }
const isLoggedIn = computed(() => !!authUser.value);

/* ✅ 드롭다운 상태 */
const isMenuOpen = ref(false);
const menuRef = ref(null);

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value;
}
function closeMenu() {
  isMenuOpen.value = false;
}

/* 새로고침 유지 */
onMounted(() => {
  const saved = localStorage.getItem("mm_auth_user");
  if (saved) authUser.value = JSON.parse(saved);

  window.addEventListener("mousedown", handleOutsideClick);
  window.addEventListener("keydown", handleEsc);
});

onBeforeUnmount(() => {
  window.removeEventListener("mousedown", handleOutsideClick);
  window.removeEventListener("keydown", handleEsc);
  clearTimeout(debounceTimer);
});

function handleOutsideClick(e) {
  // user menu 닫기
  if (isMenuOpen.value) {
    const el = menuRef.value;
    if (el && !el.contains(e.target)) closeMenu();
  }

  // search dropdown 닫기
  if (open.value) {
    const el2 = searchRef.value;
    if (el2 && !el2.contains(e.target)) closeSuggest();
  }
}

function handleEsc(e) {
  if (e.key === "Escape") {
    closeMenu();
    closeSuggest();
  }
}

/* ✅ mock 로그인 규칙: test / 1234 */
function handleLoginSubmit({ username, password }) {
  const u = (username ?? "").trim();
  const p = password ?? "";

  if (u === "test" && p === "1234") {
    authUser.value = { username: u };
    localStorage.setItem("mm_auth_user", JSON.stringify(authUser.value));
    closeLogin();
    closeMenu();
  } else {
    alert("아이디 또는 비밀번호가 올바르지 않습니다. (test / 1234)");
  }
}

function logout() {
  authUser.value = null;
  localStorage.removeItem("mm_auth_user");
  closeMenu();
}

/* (준비중 버튼) */
function goMyPage() {
  alert("마이페이지는 준비 중입니다.");
  closeMenu();
}
function goSettings() {
  alert("설정은 준비 중입니다.");
  closeMenu();
}
</script>

<style scoped>
/* 전체 헤더 */
.global-header {
  width: 100%;
  padding: 16px 32px;
  background: transparent;
  border-bottom: none;
  backdrop-filter: none;
  display: flex;
  justify-content: center;
}

.header-content {
  width: 100%;
  max-width: 1600px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

/* 로고 */
.logo {
  font-size: 30px;
  font-weight: 700;
  color: #eeeeee;
  text-shadow: 0 0 3px rgba(59, 130, 246, 0.5);
  cursor: pointer;
  white-space: nowrap;
}

/* 검색창 + 로그인 위치 고정 */
.right-area {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
  flex: 1;
  justify-content: flex-end;
}

/* 검색박스 */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  width: min(520px, 52vw);
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  transition: 0.2s;
}
.search-box:hover {
  background: rgba(255, 255, 255, 0.09);
}
.search-box input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  color: #e6edff;
  font-size: 14px;
}
.search-box button {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #cbd5e1;
  font-size: 18px;
  padding-left: 6px;
}
.search-icon {
  filter: drop-shadow(0 0 2px rgba(59, 130, 246, 0.7));
}

/* ✅ search dropdown */
.search-hint {
  position: absolute;
  left: 16px;
  top: calc(100% + 6px);
  font-size: 12px;
  color: #9ca3af;
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  z-index: 999;
  list-style: none;
  margin: 0;
  padding: 8px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(17, 34, 64, 0.96);
  box-shadow: 0 18px 50px rgba(0,0,0,0.55);
}

.search-item {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 10px;
  border-radius: 10px;
  cursor: pointer;
  color: #e6edff;
  font-size: 13px;
}
.search-item:hover,
.search-item.active {
  background: rgba(255,255,255,0.10);
}

.search-item .cd {
  color: #9ca3af;
  font-variant-numeric: tabular-nums;
}

.search-empty {
  position: absolute;
  top: calc(100% + 10px);
  left: 0;
  right: 0;
  z-index: 999;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(17, 34, 64, 0.96);
  color: #9ca3af;
  font-size: 13px;
  box-shadow: 0 18px 50px rgba(0,0,0,0.55);
}

/* 로그인 버튼 */
.login-btn {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
  box-shadow: 0 2px 10px rgba(59, 130, 246, 0.5);
  transition: 0.2s;
}
.login-btn:hover {
  background: linear-gradient(135deg, #2563eb, #4f46e5);
  transform: translateY(-1px);
}

/* ✅ 유저 드롭다운 */
.user-menu {
  position: relative;
}
.user-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e6edff;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: 0.2s;
  box-shadow: 0 2px 10px rgba(0,0,0,0.18);
}
.user-btn:hover {
  background: rgba(255, 255, 255, 0.10);
  transform: translateY(-1px);
}
.user-name {
  font-weight: 700;
  font-size: 14px;
}
.caret {
  opacity: 0.9;
  font-size: 12px;
}

/* dropdown panel */
.dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  width: 220px;
  background: rgba(17, 34, 64, 0.95);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 12px;
  box-shadow: 0 18px 50px rgba(0,0,0,0.55);
  overflow: hidden;
  z-index: 999;
}
.dropdown-item {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: none;
  background: transparent;
  color: #e6edff;
  cursor: pointer;
  font-size: 13px;
}
.dropdown-item:hover {
  background: rgba(255,255,255,0.08);
}
.dropdown-divider {
  height: 1px;
  background: rgba(255,255,255,0.10);
}
.dropdown-item.danger {
  color: #fecaca;
}
.dropdown-item.danger:hover {
  background: rgba(248,113,113,0.14);
}

.left-area {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 0 0 auto;
  min-width: 240px;
}

.nav-btn {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #e6edff;
  padding: 8px 12px;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  font-size: 13px;
  transition: 0.2s;
}

.nav-btn:hover {
  background: rgba(255, 255, 255, 0.10);
  transform: translateY(-1px);
}
</style>
