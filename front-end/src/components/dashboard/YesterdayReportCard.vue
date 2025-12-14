<template>
  <div class="card">
    <div class="card-header">
      <div>
        <div class="card-title">전날 분석 리포트</div>
        <div class="card-sub">{{ report?.date || "-" }}</div>
      </div>

      <button class="ghost-btn" @click="$emit('open')">
        상세
      </button>
    </div>

    <div class="divider"></div>

    <div class="report-text" v-if="report">
      <div class="report-tag">
        <span>📊</span>
        <span>{{ report.tag }}</span>
      </div>

      <p class="report-summary">
        {{ report.summary }}
      </p>

      <ul class="bullet">
        <li v-for="(b, i) in report.bullets" :key="i">{{ b }}</li>
      </ul>

      <div class="mini-stats">
        <div class="mini-stat" v-for="(s, i) in report.stats" :key="i">
          <div class="k">{{ s.label }}</div>
          <div class="v" :class="s.tone">{{ s.value }}</div>
        </div>
      </div>

      <div class="stat-highlight" v-if="report.todayFocus">
        오늘의 핵심: <span>{{ report.todayFocus }}</span>
      </div>
    </div>

    <div class="report-text" v-else>
      전날 리포트를 불러오는 중…
    </div>
  </div>
</template>

<script setup>
defineProps({
  report: { type: Object, default: null }
});
defineEmits(["open"]);
</script>

<style scoped>
/* mockup.html 톤과 맞추는 최소 보강 (기존 card/divider/report-text 클래스가 있다면 생략 가능) */
.ghost-btn{
  border: 1px solid rgba(148,163,184,0.6);
  background: transparent;
  color: #e5e7eb;
  font-size: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  cursor: pointer;
}
.report-summary{ margin: 6px 0 8px; line-height: 1.5; }
.bullet{ margin: 6px 0 10px; padding-left: 16px; color:#cbd5f5; font-size:12px; }
.bullet li{ margin: 4px 0; }
.mini-stats{
  display:grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: 6px;
  margin-top: 6px;
}
.mini-stat{
  padding: 6px 8px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(55, 65, 81, 0.9);
}
.k{ font-size: 11px; color:#9ca3af; }
.v{ font-weight: 600; color:#e5e7eb; }
.v.pos{ color:#4ade80; }
.v.neg{ color:#fecaca; }
</style>
