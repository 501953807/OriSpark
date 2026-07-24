<template>
  <section class="stats-section">
    <h2 class="section-title">平台实时数据</h2>
    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>
    <div v-else class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats?.totalWorks ?? 0 }}</div>
        <div class="stat-label">作品总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats?.totalContracts ?? 0 }}</div>
        <div class="stat-label">合约总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats?.totalUsers ?? 0 }}</div>
        <div class="stat-label">创作者数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ formatCurrency(stats?.monthly_transaction_volume) }}</div>
        <div class="stat-label">月成交额</div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useMarketData } from '~/composables/useMarketData'

const { stats, loading, error, loadStats } = useMarketData()
await loadStats()

function formatCurrency(value?: number): string {
  if (value == null) return '¥0'
  return `¥${value.toLocaleString('zh-CN')}`
}
</script>

<style scoped>
.stats-section {
  padding: 48px 32px;
  background: #f9fafb;
}

.section-title {
  text-align: center;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #111827;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  max-width: 960px;
  margin: 0 auto;
}

.stat-card {
  text-align: center;
  padding: 24px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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

.loading-state,
.error-state {
  text-align: center;
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
