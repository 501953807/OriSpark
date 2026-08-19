<template>
  <div v-if="warnings.length > 0" class="risk-warning-panel">
    <div class="panel-header">
      <span class="panel-title">⚠️ 侵权风险预警</span>
      <button class="dismiss-all" @click="$emit('dismiss-all')">全部已知晓</button>
    </div>
    <div v-for="w in warnings" :key="w.id || w.title" class="warning-item" :class="w.severity">
      <span class="severity-badge" :class="w.severity">{{ severityLabel(w.severity) }}</span>
      <div class="warning-body">
        <div class="warning-title">{{ w.title }}</div>
        <div v-if="w.description" class="warning-desc">{{ w.description }}</div>
        <div v-if="w.matched_entity" class="warning-entity">匹配实体: {{ w.matched_entity }}</div>
      </div>
      <div class="warning-actions">
        <span v-if="w.severity === 'high'" class="suggestion-btn red">建议修改</span>
        <span v-else-if="w.severity === 'medium'" class="suggestion-btn yellow">了解更多</span>
        <button class="dismiss-btn" @click="$emit('dismiss', w.id)">我知道了</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { RiskWarning } from '@/types/risk_warning'

defineProps<{
  warnings: RiskWarning[]
}>()

const emit = defineEmits<{
  dismiss: [id: string]
  'dismiss-all': []
}>()

const severityLabel = (sev: string) => ({ high: '高风险', medium: '中风险', low: '低风险' }[sev] || sev)
</script>

<style scoped>
.risk-warning-panel {
  background: #fff8f0;
  border: 1px solid #fde68a;
  border-radius: var(--m-radius-md, 8px);
  padding: 12px 14px;
  margin-bottom: 12px;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px;
}
.panel-title { font-size: 0.9rem; font-weight: 700; color: #b45309; }
.dismiss-all {
  background: none; border: none; font-size: 0.75rem; color: #92400e;
  cursor: pointer; text-decoration: underline;
}
.warning-item {
  display: flex; gap: 8px; align-items: flex-start;
  padding: 8px 0; border-top: 1px solid rgba(180, 83, 9, 0.15);
}
.severity-badge {
  font-size: 0.7rem; font-weight: 700; padding: 2px 8px; border-radius: 9999px;
  white-space: nowrap; flex-shrink: 0;
}
.severity-badge.high { background: #fef2f2; color: #dc2626; }
.severity-badge.medium { background: #fffbeb; color: #d97706; }
.severity-badge.low { background: #f0fdf4; color: #16a34a; }
.warning-body { flex: 1; min-width: 0; }
.warning-title { font-size: 0.85rem; font-weight: 600; color: var(--fg); }
.warning-desc { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }
.warning-entity { font-size: 0.72rem; color: var(--muted); margin-top: 2px; font-style: italic; }
.warning-actions { display: flex; flex-direction: column; gap: 4px; align-items: flex-end; flex-shrink: 0; }
.suggestion-btn { font-size: 0.72rem; padding: 3px 8px; border-radius: var(--m-radius-sm); cursor: pointer; font-weight: 600; }
.suggestion-btn.red { background: #fef2f2; color: #dc2626; }
.suggestion-btn.yellow { background: #fffbeb; color: #d97706; }
.dismiss-btn {
  background: none; border: none; font-size: 0.72rem; color: var(--muted);
  cursor: pointer; text-decoration: underline;
}
</style>
