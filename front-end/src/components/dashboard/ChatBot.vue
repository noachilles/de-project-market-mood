<template>
  <div class="chatbot-container">
    <!-- 플로팅 버튼 -->
    <button 
      v-if="!isOpen"
      class="chatbot-toggle"
      @click="toggleChat"
      aria-label="챗봇 열기"
    >
      💬
    </button>

    <!-- 챗봇 창 -->
    <div v-if="isOpen" class="chatbot-window">
      <div class="chatbot-header">
        <div class="chatbot-title">AI 챗봇</div>
        <button class="chatbot-close" @click="toggleChat" aria-label="챗봇 닫기">
          ✕
        </button>
      </div>

      <div class="chatbot-messages" ref="messagesContainer">
        <div 
          v-for="(message, idx) in messages" 
          :key="idx"
          :class="['message', message.role]"
        >
          <div class="message-content">{{ message.content }}</div>
          <div v-if="message.sources && message.sources.length > 0" class="message-sources">
            <div class="sources-label">참고 뉴스:</div>
            <ul class="sources-list">
              <li v-for="(source, sIdx) in message.sources" :key="sIdx" class="source-item">
                {{ source }}
              </li>
            </ul>
          </div>
        </div>
        <div v-if="isLoading" class="message assistant">
          <div class="message-content">답변을 생성하는 중...</div>
        </div>
      </div>

      <div class="chatbot-input">
        <input
          v-model="inputMessage"
          @keyup.enter="sendMessage"
          placeholder="질문을 입력하세요..."
          :disabled="isLoading"
          class="chatbot-input-field"
        />
        <button 
          @click="sendMessage" 
          :disabled="isLoading || !inputMessage.trim()"
          class="chatbot-send-btn"
        >
          전송
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";

const API_BASE = "http://localhost:8000";
const isOpen = ref(false);
const inputMessage = ref("");
const messages = ref([]);
const isLoading = ref(false);
const messagesContainer = ref(null);

function toggleChat() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    // 챗봇 열 때 환영 메시지 추가
    if (messages.value.length === 0) {
      messages.value.push({
        role: "assistant",
        content: "안녕하세요! 주식 시장 뉴스에 대해 궁금한 것이 있으시면 물어보세요.",
        sources: []
      });
    }
    // 스크롤을 맨 아래로
    nextTick(() => {
      scrollToBottom();
    });
  }
}

async function sendMessage() {
  const question = inputMessage.value.trim();
  if (!question || isLoading.value) return;

  // 사용자 메시지 추가
  messages.value.push({
    role: "user",
    content: question,
    sources: []
  });

  inputMessage.value = "";
  isLoading.value = true;

  // 스크롤을 맨 아래로
  await nextTick();
  scrollToBottom();

  try {
    const res = await fetch(`${API_BASE}/api/news/chat/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    if (!res.ok) {
      throw new Error("챗봇 API 에러");
    }

    const data = await res.json();
    
    // AI 답변 추가
    messages.value.push({
      role: "assistant",
      content: data.answer || "답변을 생성할 수 없습니다.",
      sources: data.sources || []
    });

  } catch (e) {
    console.error("챗봇 오류:", e);
    messages.value.push({
      role: "assistant",
      content: "죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
      sources: []
    });
  } finally {
    isLoading.value = false;
    // 스크롤을 맨 아래로
    await nextTick();
    scrollToBottom();
  }
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

// 메시지가 추가될 때마다 스크롤
watch(() => messages.value.length, () => {
  nextTick(() => {
    scrollToBottom();
  });
});
</script>

<style scoped>
.chatbot-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.chatbot-toggle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: transform 0.2s, box-shadow 0.2s;
}

.chatbot-toggle:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

.chatbot-window {
  width: 400px;
  height: 600px;
  background: #1f2937;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chatbot-header {
  background: #111827;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.chatbot-title {
  font-size: 16px;
  font-weight: 600;
  color: #e5e7eb;
}

.chatbot-close {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.2s;
}

.chatbot-close:hover {
  color: #e5e7eb;
}

.chatbot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 80%;
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message.assistant .message-content {
  background: #374151;
  color: #e5e7eb;
}

.message-sources {
  margin-top: 8px;
  padding: 8px;
  background: rgba(148, 163, 184, 0.1);
  border-radius: 8px;
  font-size: 11px;
}

.sources-label {
  color: #9ca3af;
  margin-bottom: 4px;
  font-weight: 500;
}

.sources-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.source-item {
  color: #cbd5e1;
  padding: 2px 0;
  font-size: 11px;
}

.chatbot-input {
  padding: 16px;
  background: #111827;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
  display: flex;
  gap: 8px;
}

.chatbot-input-field {
  flex: 1;
  padding: 10px 12px;
  background: #374151;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  color: #e5e7eb;
  font-size: 14px;
}

.chatbot-input-field:focus {
  outline: none;
  border-color: #667eea;
}

.chatbot-input-field:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chatbot-send-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
}

.chatbot-send-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.chatbot-send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 스크롤바 스타일 */
.chatbot-messages::-webkit-scrollbar {
  width: 6px;
}

.chatbot-messages::-webkit-scrollbar-track {
  background: #111827;
}

.chatbot-messages::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 3px;
}

.chatbot-messages::-webkit-scrollbar-thumb:hover {
  background: #6b7280;
}
</style>

