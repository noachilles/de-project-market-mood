<template>
  <Teleport to="body">
    <div class="overlay" @click.self="emit('close')">
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-header">
          <div>
            <div class="title">로그인</div>
            <div class="sub">MarketMood에 로그인하세요</div>
          </div>
          <button class="icon-btn" @click="emit('close')" aria-label="닫기">✕</button>
        </div>

        <div class="divider"></div>

        <form class="form" @submit.prevent="onSubmit">
          <label class="field">
            <span class="label">아이디</span>
            <input v-model.trim="username" type="text" placeholder="아이디 입력" autocomplete="username" />
          </label>

          <label class="field">
            <span class="label">비밀번호</span>
            <input v-model="password" type="password" placeholder="비밀번호 입력" autocomplete="current-password" />
          </label>

          <button class="primary" type="submit">로그인</button>

          <p class="hint">* 아직 인증 API 연결 전이라, 제출 시 콘솔에만 출력돼요.</p>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from "vue";

const emit = defineEmits(["close", "submit"]);

const username = ref("");
const password = ref("");

function onSubmit() {
  emit("submit", { username: username.value, password: password.value });
}

function onKeydown(e) {
  if (e.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => window.removeEventListener("keydown", onKeydown));
</script>

<style scoped>
.overlay{
  position: fixed; inset: 0;
  background: rgba(2, 6, 23, 0.72);
  display: flex; align-items: center; justify-content: center;
  z-index: 9999;
  backdrop-filter: blur(6px);
}
.modal{
  width: 420px;
  border-radius: 18px;
  background: rgba(17, 34, 64, 0.92);
  border: 1px solid rgba(255,255,255,0.10);
  box-shadow: 0 30px 80px rgba(0,0,0,0.55);
  padding: 16px;
}
.modal-header{
  display:flex; justify-content: space-between; align-items: center;
  gap: 12px;
}
.title{ font-size: 18px; font-weight: 800; color:#e6edff; }
.sub{ font-size: 12px; color:#9ca3af; margin-top: 2px; }
.icon-btn{
  border: 1px solid rgba(255,255,255,0.15);
  background: transparent;
  color:#e6edff;
  border-radius: 10px;
  padding: 6px 10px;
  cursor: pointer;
}
.divider{
  height:1px;
  background: rgba(255,255,255,0.10);
  margin: 12px 0;
}
.form{ display:flex; flex-direction: column; gap: 10px; }
.field{ display:flex; flex-direction: column; gap: 6px; }
.label{ font-size: 12px; color:#cbd5f5; }
input{
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.10);
  color:#e6edff;
  border-radius: 10px;
  padding: 10px 12px;
  outline: none;
}
input:focus{
  border-color: rgba(59,130,246,0.7);
}
.primary{
  margin-top: 4px;
  background: #3b82f6;
  border: none;
  color: white;
  font-weight: 800;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
}
.primary:hover{ background:#2563eb; }
.hint{ font-size: 11px; color:#9ca3af; margin: 0; }
</style>
