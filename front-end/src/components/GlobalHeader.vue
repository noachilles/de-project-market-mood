<template>
  <header class="global-header">
    <div class="header-content">
      <!-- 왼쪽: 로고 -->
      <div class="logo">MarketMood</div>

      <!-- 오른쪽: 검색창 + 로그인/유저메뉴 -->
      <div class="right-area">
        <div class="search-box">
          <input
            type="text"
            v-model="keyword"
            placeholder="종목명 또는 코드 검색"
            @keyup.enter="search"
          />
          <button @click="search">
            <span class="search-icon">🔍</span>
          </button>
        </div>

        <!-- ✅ 로그인 전 -->
        <button v-if="!isLoggedIn" class="login-btn" @click="openLogin">
          로그인
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

/* 검색 */
const keyword = ref("");
const search = () => {
  if (!keyword.value.trim()) return;
  alert(`검색: ${keyword.value}`);
};

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
});

function handleOutsideClick(e) {
  if (!isMenuOpen.value) return;
  const el = menuRef.value;
  if (el && !el.contains(e.target)) closeMenu();
}

function handleEsc(e) {
  if (e.key === "Escape") closeMenu();
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
}

/* 로고 */
.logo {
  font-size: 30px;
  font-weight: 700;
  color: #eeeeee;
  text-shadow: 0 0 3px rgba(59, 130, 246, 0.5);
}

/* 검색창 + 로그인 위치 고정 */
.right-area {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 16px;
}

/* 검색박스 */
.search-box {
  display: flex;
  align-items: center;
  width: 320px;
  padding: 8px 14px;
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
</style>
