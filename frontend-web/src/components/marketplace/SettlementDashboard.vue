<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { podSettlementApi } from '@/api/marketplace'
import type { SalesStatistics } from '@/api/marketplace'

const stats = ref<SalesStatistics | null>(null)
const loading = ref(true)
const period = ref('2026-07')

onMounted(async () => {
  try {
    const res = await podSettlementApi.getSalesStatistics({ start_date: `${period.value}-01`, end_date: `${period.value}-28` })
    stats.value = res.data
  } catch { /* handled */ } finally { loading.value = false }
})

function formatYuan(v: number): string {
  return `¥${v.toLocaleString('zh-CN', { minimumFractionDigits: 2 })}`
}
</script>

<template>
  <div class="settlement-dashboard card">
    <h3>POD 结算看板</h3>

    <div v-if="loading" class="loading">加载中...</div>
    <template v-else-if="stats">
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-label">总销售额</div>
          <div class="stat-value">{{ formatYuan(stats.total_revenue_yuan) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">总利润</div>
          <div class="stat-value success">{{ formatYuan(stats.total_profit_yuan) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">订单数</div>
          <div class="stat-value">{{ stats.total_sales }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">平均利润/单</div>
          <div class="stat-value">{{ formatYuan(stats.avg_profit_per_sale_yuan) }}</div>
        </div>
      </div>

      <div class="platform-breakdown">
        <h4>平台明细</h4>
        <table class="data-table">
          <thead>
            <tr><th>平台</th><th>订单</th><th>营收</th><th>利润</th></tr>
          </thead>
          <tbody>
            <tr v-for="(v, k) in stats.by_platform" :key="k">
              <td>{{ k }}</td>
              <td>{{ v.sales }}</td>
              <td>{{ formatYuan(v.revenue_yuan) }}</td>
              <td class="success">{{ formatYuan(v.profit_yuan) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<style scoped>
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px; }
.stat-card { background: var(--bg-secondary); padding: 16px; border-radius: 8px; text-align: center; }
.stat-label { font-size: 0.8rem; color: var(--muted); margin-bottom: 4px; }
.stat-value { font-size: 1.4rem; font-weight: 600; }
.success { color: #059669; }
.platform-breakdown { margin-top: 16px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.data-table th, .data-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); text-align: left; }
.data-table th { font-weight: 600; color: var(--muted); }
</style>
