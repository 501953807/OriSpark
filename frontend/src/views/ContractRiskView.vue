<template>
  <div class="contract-risk-view">
    <LoadingSpinner v-if="store.loading" text="分析中..." />
    <template v-else>
      <h2>合约风险评估</h2>
      <p class="subtitle">自动识别合同条款风险，保护创作者权益</p>

      <!-- Tab 切换 -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="['tab', { active: activeTab === tab.key }]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- 输入区 -->
      <div class="input-section">
        <textarea
          v-model="contractText"
          placeholder="请粘贴合同文本或上传合同文件..."
          rows="10"
          class="contract-input"
        ></textarea>
        <div class="input-actions">
          <label class="btn-secondary">
            上传文件
            <input type="file" accept=".txt,.pdf,.docx" @change="handleFileUpload" style="display:none" />
          </label>
          <button class="btn-primary" @click="submitReview" :disabled="!contractText.trim()">
            开始分析
          </button>
        </div>
      </div>

      <!-- 分析结果 -->
      <div v-if="result" class="results-section">
        <!-- 风险评分 -->
        <div class="score-card" :class="'score-' + result.risk_level">
          <div class="score-circle">
            <span class="score-value">{{ result.total_score }}</span>
            <span class="score-label">风险分</span>
          </div>
          <div class="score-info">
            <div class="risk-badge" :class="'risk-' + result.risk_level">
              {{ riskLevelLabel(result.risk_level) }}
            </div>
            <div class="score-stats">
              <span>识别条款: {{ result.clauses_found }}</span>
              <span>发现风险: {{ result.risk_count }}</span>
            </div>
          </div>
        </div>

        <!-- 建议 -->
        <div v-if="result.suggestions.length > 0" class="suggestions">
          <h3>修改建议</h3>
          <ul>
            <li v-for="(s, i) in result.suggestions" :key="i">{{ s }}</li>
          </ul>
        </div>

        <!-- 条款列表 -->
        <div class="clauses-list">
          <h3>条款明细</h3>
          <div
            v-for="(c, i) in result.clauses"
            :key="i"
            class="clause-item"
            :class="{ flagged: c.is_flagged }"
          >
            <div class="clause-header">
              <span class="clause-index">第{{ c.clause_index }}条</span>
              <span
                class="clause-risk"
                :class="'risk-' + (c.risk_level || 'safe')"
              >
                {{ c.risk_level ? riskLevelLabel(c.risk_level) : '—' }}
              </span>
            </div>
            <p class="clause-text">{{ c.clause_text }}</p>
            <div v-if="c.risk_description" class="clause-risk-desc">{{ c.risk_description }}</div>
            <div v-if="c.suggestion" class="clause-suggestion">💡 {{ c.suggestion }}</div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!result && !store.loading" class="empty">
        暂无分析结果 — 请在上方粘贴合同文本开始分析
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useContractRiskStore } from '@/stores/useContractRiskStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useContractRiskStore()
const activeTab = ref('general')
const contractText = ref('')

const tabs = [
  { key: 'general', label: '通用合同审查' },
  { key: 'transaction', label: '交易合约预检' },
]

const result = computed(() => store.result)

function riskLevelLabel(level: string): string {
  const labels: Record<string, string> = {
    safe: '安全',
    low: '低风险',
    medium: '中等风险',
    high: '高风险',
    critical: '极高风险',
  }
  return labels[level] || level
}

async function submitReview() {
  if (!contractText.value.trim()) return
  await store.review({
    review_type: activeTab.value,
    contract_text: contractText.value,
  })
}

function handleFileUpload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    contractText.value = e.target?.result as string
  }
  reader.readAsText(file)
}
</script>

<style scoped>
.contract-risk-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--muted); font-size: 0.85rem; margin-bottom: 24px; }

.tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
}
.tab.active {
  background: var(--accent);
  color: white;
  border-color: var(--accent);
}

.input-section {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 24px;
}
.contract-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-family: inherit;
  font-size: 0.9rem;
  resize: vertical;
  box-sizing: border-box;
}
.input-actions { display: flex; gap: 12px; margin-top: 12px; justify-content: flex-end; }
.btn-primary {
  background: var(--accent);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary {
  background: var(--bg-secondary);
  color: var(--text);
  border: 1px solid var(--border);
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
}

.results-section { margin-bottom: 24px; }

.score-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 24px;
  border-radius: var(--radius);
  border: 2px solid;
  margin-bottom: 20px;
}
.score-card.score-safe { border-color: #22c55e; background: #f0fdf4; }
.score-card.score-low { border-color: #84cc16; background: #f7fee7; }
.score-card.score-medium { border-color: #f59e0b; background: #fffbeb; }
.score-card.score-high { border-color: #ef4444; background: #fef2f2; }
.score-card.score-critical { border-color: #dc2626; background: #fef2f2; }

.score-circle {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 100px;
}
.score-value { font-size: 2rem; font-weight: 700; }
.score-label { font-size: 0.75rem; color: var(--muted); }

.score-info { flex: 1; }
.risk-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 8px;
}
.risk-safe { background: #dcfce7; color: #166534; }
.risk-low { background: #ecfccb; color: #3f6212; }
.risk-medium { background: #fef3c7; color: #92400e; }
.risk-high { background: #fee2e2; color: #991b1b; }
.risk-critical { background: #fecaca; color: #7f1d1d; }

.score-stats { display: flex; gap: 16px; font-size: 0.82rem; color: var(--muted); }

.suggestions {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 20px;
}
.suggestions h3 { margin-top: 0; font-size: 1rem; }
.suggestions ul { padding-left: 20px; }
.suggestions li { font-size: 0.85rem; margin-bottom: 4px; }

.clauses-list h3 { font-size: 1rem; margin-bottom: 12px; }
.clause-item {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  margin-bottom: 8px;
}
.clause-item.flagged {
  border-left: 3px solid #ef4444;
}
.clause-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}
.clause-index { font-size: 0.82rem; font-weight: 600; }
.clause-risk {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 999px;
}
.clause-text { font-size: 0.85rem; margin: 4px 0; color: var(--text); }
.clause-risk-desc { font-size: 0.8rem; color: #dc2626; margin-top: 4px; }
.clause-suggestion { font-size: 0.8rem; color: #166534; margin-top: 4px; }

.empty { padding: 48px; text-align: center; color: var(--muted); }
</style>
