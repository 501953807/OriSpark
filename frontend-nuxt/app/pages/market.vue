<template>
  <div class="page-market">
    <h1 class="page-title">市场数据看板</h1>

    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="market-content">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats?.total_users ?? 0 }}</div>
          <div class="stat-label">注册创作者</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats?.total_works ?? 0 }}</div>
          <div class="stat-label">作品总数</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats?.active_contracts ?? 0 }}</div>
          <div class="stat-label">活跃合约</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatCurrency(stats?.monthly_transaction_volume) }}</div>
          <div class="stat-label">月交易额</div>
        </div>
      </div>

      <div class="charts-placeholder">
        <p class="chart-hint">图表组件待接入 ECharts / Vue Chart.js</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMarketData } from '~/composables/useMarketData'

useHead({
  title: '市场数据 — OriSpark',
})

const { stats, loading, error, loadStats } = useMarketData()
await loadStats()

function formatCurrency(value?: number): string {
  if (value == null) return '¥0'
  return `¥${value.toLocaleString('zh-CN')}`
}
</script>

<style scoped>
.page-market {
  padding: 32px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #059669;
}

.stat-label {
  font-size: 14px;
  color: #6b7280;
  margin-top: 8px;
}

.charts-placeholder {
  background: #f9fafb;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
}

.chart-hint {
  color: #9ca3af;
  font-size: 14px;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 48px 0;
  color: #6b7280;
}

.error-state {
  color: #ef4444;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
