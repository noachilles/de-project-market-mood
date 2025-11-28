<!-- src/views/Dashboard.vue -->
<template>
  <div class="dashboard-shell">

    <!-- 상단 헤더 -->
    <Header />

    <!-- 3열 레이아웃 -->
    <main class="layout">

      <!-- 왼쪽 컬럼 -->
      <section class="column left">
        <WatchList />
      </section>

      <!-- 중앙 컬럼 -->
      <section class="column center">
        <StockChart />
        <NewsFeed />
      </section>

      <!-- 오른쪽 컬럼 -->
      <section class="column right">
        <AiInsight />
        <MyHolding />
      </section>

    </main>

  </div>
</template>

<script setup>
import Header from '@/components/dashboard/Header.vue'
import WatchList from '@/components/dashboard/WatchList.vue'
import StockChart from '@/components/dashboard/StockChart.vue'
import NewsFeed from '@/components/dashboard/NewsFeed.vue'
import AiInsight from '@/components/dashboard/AiInsight.vue'
import MyHolding from '@/components/dashboard/MyHolding.vue'
</script>
