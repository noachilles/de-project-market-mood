<!-- src/components/dashboard/WatchList.vue -->
<template>
  <div class="card">
    <div class="card-header">
      <div class="card-title">내 관심종목 리스트</div>
      <div class="card-sub">실시간 변화율 기준</div>
    </div>
    <div class="divider"></div>

    <div class="watchlist">
      <div class="watch-item active">
        <div>
          <div class="watch-symbol">삼성전자</div>
          <div class="watch-price">85,300원</div>
        </div>
        <div class="watch-change pos">+2.55%</div>
      </div>

      <div class="watch-item">
        <div>
          <div class="watch-symbol">SK하이닉스</div>
          <div class="watch-price">135,000원</div>
        </div>
        <div class="watch-change neg">-1.15%</div>
      </div>
    </div>
  </div>
</template>
