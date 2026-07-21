<template>
  <div class="risk-warning-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>风险预警中心</h2>
      <p class="subtitle">税务日历 · 侵权预警 · Burnout检测</p>

      <!-- Burnout 风险 -->
      <div class="section">
        <h3>创作健康</h3>
        <div v-if="store.burnoutRisk" class="burnout-card" :class="store.burnoutRisk.risk_level">
          <div class="burnout-header">
            <span class="burnout-label">{{ riskLabel(store.burnoutRisk.risk_level) }}</span>
            <span class="burnout-score">{{ store.burnoutRisk.score }}/100</span>
          </div>
          <ul v-if="store.burnoutRisk.factors.length > 0" class="burnout-factors">
            <li v-for="f in store.burnoutRisk.factors" :key="f">{{ f }}</li>
          </ul>
          <p class="burnout-rec">{{ store.burnoutRisk.recommendation }}</p>
        </div>
      </div>

      <!-- 税务日历 -->
      <div class="section">
        <h3>税务合规日历</h3>
        <div class="tax-list">
          <div v-for="d in store.taxDeadlines" :key="d.id" class="tax-item" :class="{ done: d.is_completed }">
            <div class="tax-info">
              <strong>{{ taxTypeLabel(d.tax_type) }}</strong>
              <span class="tax-due">截止 {{ d.due_date }} ({{ d.days_remaining }}天)</span>
            </div>
            <button v-if="!d.is_completed" class="btn-complete" @click="markComplete(d.id)">完成</button>
            <span v-else class="status-done">已完成</span>
          </div>
          <div v-if="store.taxDeadlines.length === 0" class="empty-state">
            暂无税务截止日期，添加后自动监控。
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { useRiskWarningStore } from '@/stores/useRiskWarningStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useRiskWarningStore()

function riskLabel(level: string): string {
  return { low: '状态良好', medium: '注意疲劳', high: '高风险' }[level] || level
}

function taxTypeLabel(key: string): string {
  return { quarterly_vat: '季度增值税', annual_income: '年度汇算', foreign_withholding: '境外预扣税' }[key] || key
}

async function markComplete(id: string) {
  await store.markComplete(id)
}

// Init
store.loadTaxDeadlines()
store.loadBurnoutRisk()
</script>

<style scoped>
.risk-warning-view { max-width: 800px; margin: 0 auto; }
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.section h3 { margin: 0 0 16px; font-size: 1rem; }

/* Burnout card */
.burnout-card { padding: 16px; border-radius: var(--radius); border: 1px solid var(--border); }
.burnout-card.low { background: #f0fdf4; border-color: #bbf7d0; }
.burnout-card.medium { background: #fffbeb; border-color: #fde68a; }
.burnout-card.high { background: #fef2f2; border-color: #fecaca; }
.burnout-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.burnout-label { font-weight: 700; font-size: 1.1rem; }
.burnout-score { font-size: 1.5rem; font-weight: 800; }
.burnout-card.low .burnout-score { color: #22c55e; }
.burnout-card.medium .burnout-score { color: #d97706; }
.burnout-card.high .burnout-score { color: #ef4444; }
.burnout-factors { margin: 0 0 12px; padding-left: 20px; }
.burnout-factors li { margin-bottom: 4px; font-size: 0.85rem; }
.burnout-rec { font-size: 0.85rem; color: var(--muted); margin: 0; }

/* Tax list */
.tax-list { display: grid; gap: 8px; }
.tax-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}
.tax-item.done { opacity: 0.5; }
.tax-info { display: flex; flex-direction: column; }
.tax-info strong { font-size: 0.9rem; }
.tax-due { font-size: 0.8rem; color: var(--muted); }
.btn-complete {
  background: var(--accent);
  color: white;
  border: none;
  padding: 6px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.8rem;
}
.status-done { color: #22c55e; font-size: 0.8rem; font-weight: 600; }
.empty-state { text-align: center; color: var(--muted); padding: 20px; font-size: 0.85rem; }
</style>
