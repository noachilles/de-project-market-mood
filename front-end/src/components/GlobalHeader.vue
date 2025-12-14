<template>
    <header class="global-header">
    <div class="header-content">
        
        <!-- 왼쪽: 로고 -->
        <div class="logo">MarketMood</div>

        <!-- 오른쪽: 검색창 + 로그인 -->
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

        <button class="login-btn">로그인</button>
        </div>

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
/* 전체 헤더 */
.global-header {
  width: 100%;
  padding: 16px 32px;
  
  /* 배경 완전 투명 */
  background: transparent;

  /* 아래 그림자·테두리도 제거해주는 게 자연스러움 */
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
  flex-direction: row;     /* 무조건 가로 */
  align-items: center;     /* 수직 가운데 정렬 */
  gap: 16px;               /* 검색창과 로그인 버튼 사이 간격 */
}

/* 검색영역 */
.search-area {
  flex: 1;
  display: flex;
  justify-content: center;
}

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
</style>
