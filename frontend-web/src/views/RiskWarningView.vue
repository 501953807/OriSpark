<template>
  <div class="risk-warning-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
    <h2>风险预警中心</h2>
    <p class="subtitle">检测提示词、参考图、模型、商标四个维度的侵权风险</p>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-val">{{ warnings.length }}</div>
        <div class="stat-lbl">预警总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ uncheckedCount }}</div>
        <div class="stat-lbl">未查看</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ highCount }}</div>
        <div class="stat-lbl">高风险</div>
      </div>
    </div>

    <!-- 手动检测 -->
    <div class="check-section">
      <h3>手动检测</h3>
      <div class="form-grid">
        <input v-model="checkForm.workTitle" placeholder="作品标题" class="input" />
        <input v-model="checkForm.prompt" placeholder="提示词 (prompt)" class="input" />
        <input v-model="checkForm.modelName" placeholder="模型名称 (如 photorealism)" class="input" />
        <select v-model="severityFilter" class="select">
          <option value="">全部级别</option>
          <option value="high">高</option>
          <option value="medium">中</option>
          <option value="low">低</option>
        </select>
      </div>
      <button class="btn-primary" @click="runCheck" :disabled="checking">
        {{ checking ? '检测中...' : '开始检测' }}
      </button>
    </div>

    <!-- 批量检测 -->
    <div class="check-section">
      <h3>批量侵权检测</h3>
      <p class="hint">输入多个作品的提示词和标题，一次性检测侵权风险。</p>
      <div v-for="(item, idx) in batchItems" :key="idx" class="batch-item">
        <div class="batch-row">
          <input v-model="item.title" placeholder="作品标题" class="input batch-input" />
          <input v-model="item.prompt" placeholder="提示词" class="input batch-input" />
          <select v-model="item.severity" class="select batch-select">
            <option value="">全部</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
          </select>
        </div>
      </div>
      <button class="btn-secondary" @click="addBatchItem">+ 添加作品</button>
      <button class="btn-primary" @click="runBatchCheck" :disabled="batchChecking">
        {{ batchChecking ? '批量检测中...' : '批量检测' }}
      </button>
    </div>

    <!-- 预警列表 -->
    <div class="warning-list">
      <div v-if="filteredWarnings.length === 0" class="empty">
        {{ warnings.length === 0 ? '暂无预警记录 — 点击上方开始检测' : '没有匹配的预警' }}
      </div>
      <div v-for="w in filteredWarnings" :key="w.id" class="warning-card" :class="w.severity">
        <div class="severity-badge" :class="w.severity">{{ severityLabel(w.severity) }}</div>
        <div class="warning-content">
          <div class="warning-title">{{ w.title }}</div>
          <div class="warning-desc">{{ w.matched_entity ? `匹配: ${w.matched_entity}` : '' }}</div>
          <div class="warning-meta">
            <span>{{ w.warning_type }}</span>
            <span v-if="w.confidence">置信度: {{ w.confidence.toFixed(0) }}%</span>
            <span>{{ w.created_at ? new Date(w.created_at).toLocaleDateString() : '' }}</span>
          </div>
        </div>
        <div class="warning-actions">
          <button v-if="!w.dismissed" class="btn-small" @click="dismiss(w.id)">已查看</button>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRiskWarningStore } from '@/stores/useRiskWarningStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { riskWarningApi } from '@/api/risk_warning'

const store = useRiskWarningStore()
const checking = ref(false)
const severityFilter = ref('')
const checkForm = ref({ workTitle: '', prompt: '', modelName: '' })
const batchChecking = ref(false)
const batchItems = ref([{ title: '', prompt: '', severity: '' }])
const batchResults = ref<any[]>([])

function addBatchItem() {
  batchItems.value.push({ title: '', prompt: '', severity: '' })
}

async function runBatchCheck() {
  batchChecking.value = true
  try {
    const items = batchItems.value.map(item => ({
      work_title: item.title,
      prompt: item.prompt,
    }))
    const res = await riskWarningApi.batchCheck(items)
    batchResults.value = res.data || []
  } finally {
    batchChecking.value = false
  }
}

const warnings = computed(() => store.warnings)
const uncheckedCount = computed(() => store.warnings.filter(w => !w.dismissed).length)
const highCount = computed(() => store.warnings.filter(w => w.severity === 'high').length)

const filteredWarnings = computed(() => {
  if (!severityFilter.value) return store.warnings
  return store.warnings.filter(w => w.severity === severityFilter.value)
})

function severityLabel(sev: string): string {
  return { high: '高', medium: '中', low: '低' }[sev] || sev
}

function severityColor(sev: string): string {
  return { high: 'red', medium: 'orange', low: 'yellow' }[sev] || sev
}

async function runCheck() {
  checking.value = true
  try {
    const results = await store.check({
      work_title: checkForm.value.workTitle,
      prompt: checkForm.value.prompt,
      model_name: checkForm.value.modelName,
    })
    if (results) {
      // Prepend new warnings to the store list
      store.warnings = [...(results as any[]), ...store.warnings]
    }
  } finally {
    checking.value = false
  }
}

async function dismiss(id: string) {
  await store.dismiss(id)
}

onMounted(async () => {
  await store.fetchAll()
})
</script>

<style scoped>
.risk-warning-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }
.stats-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; text-align: center; }
.stat-val { font-size: 1.5rem; font-weight: 700; color: var(--accent); }
.stat-lbl { font-size: 0.82rem; color: var(--muted); margin-top: 4px; }
.check-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 24px; }
.check-section h3 { margin-top: 0; font-size: 1rem; }
.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.input, .select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.9rem; }
.btn-primary { background: var(--accent); color: white; border: none; padding: 8px 20px; border-radius: var(--radius-sm); cursor: pointer; font-size: 0.9rem; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.warning-list { display: flex; flex-direction: column; gap: 8px; }
.warning-card { display: flex; align-items: flex-start; gap: 12px; padding: 14px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); border-left: 4px solid var(--border); }
.warning-card.high { border-left-color: #dc2626; }
.warning-card.medium { border-left-color: #f59e0b; }
.warning-card.low { border-left-color: #22c55e; }
.severity-badge { padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.severity-badge.high { background: #fef2f2; color: #dc2626; }
.severity-badge.medium { background: #fffbeb; color: #d97706; }
.severity-badge.low { background: #f0fdf4; color: #16a34a; }
.warning-content { flex: 1; }
.warning-title { font-weight: 600; font-size: 0.9rem; margin-bottom: 4px; }
.warning-desc { font-size: 0.82rem; color: var(--muted); margin-bottom: 4px; }
.warning-meta { display: flex; gap: 12px; font-size: 0.75rem; color: var(--muted); }
.warning-actions { flex-shrink: 0; }
.btn-small { padding: 4px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); cursor: pointer; font-size: 0.8rem; }
.empty { padding: 48px; text-align: center; color: var(--muted); }
</style>
