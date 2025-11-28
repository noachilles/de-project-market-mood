<template>

  <!-- 기존 종목 헤더 (두 번째 파란 카드) -->
  <header class="header">
    <div class="header-left">
      <div class="ticker-row">
        <div class="symbol">삼성전자</div>
        <div class="code">(005930)</div>
      </div>

      <div class="price-row">
        <div class="price-main">85,300원</div>
        <div class="change-pill">
          <span>▲</span>
          <span>+2.55%</span>
        </div>
        <div class="volume">거래량: 1,250,000주</div>
      </div>
    </div>

    <div class="header-right">
      <div class="pill-tag">
        <span>AI 기반 종목 인사이트</span>
      </div>
      <button class="primary-btn">
        <span class="icon">✨</span> AI Insights 보기
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref } from "vue"

const keyword = ref("")

const search = () => {
  if (!keyword.value.trim()) return
  alert(`검색: ${keyword.value}`)
}
</script>

<style scoped>
/* 최상단 네비게이션 바 */
.top-nav {
  width: 100%;
  padding: 14px 28px;
  background: rgba(17, 34, 64, 0.85);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  backdrop-filter: blur(8px);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

/* 로고 */
.logo {
  font-size: 20px;
  font-weight: 700;
  color: #e6edff;
}

/* 검색박스 */
.search-box {
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.08);
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.08);
}

.search-box input {
  border: none;
  outline: none;
  background: transparent;
  color: #e6edff;
  font-size: 14px;
  width: 180px;
}

.search-box button {
  background: transparent;
  border: none;
  cursor: pointer;
  color: #e6edff;
  font-size: 16px;
  margin-left: 6px;
}

.nav-right {
  display: flex;
  align-items: center;
}

/* 로그인 버튼 */
.login-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: 0.15s;
}

.login-btn:hover {
  background: #2563eb;
}
</style>
