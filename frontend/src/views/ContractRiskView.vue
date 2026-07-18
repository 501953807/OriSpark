<template>
  <div class="contract-risk-view">
    <!-- Header -->
    <div class="header">
      <h2>合约风险评估</h2>
      <p class="subtitle">智能审查合同条款风险，提供修改建议</p>
    </div>

    <!-- Tab switch -->
    <div class="tabs card">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Main content: two-column layout -->
    <div class="content-grid">
      <!-- Left: input area -->
      <div class="input-panel card">
        <div class="panel-title">
          <span>合同文本</span>
          <div class="input-actions">
            <label class="btn btn-secondary btn-sm">
              上传文件
              <input
                type="file"
                accept=".txt,.pdf,.docx,.md"
                hidden
                @change="handleFileUpload"
              />
            </label>
            <button class="btn btn-ghost btn-sm" @click="loadSample">加载示例</button>
            <button class="btn btn-ghost btn-sm" @click="clearInput">清空</button>
          </div>
        </div>
        <textarea
          v-model="contractText"
          class="contract-textarea"
          placeholder="在此粘贴合同文本，或上传文件。系统将自动识别条款并分析风险。"
          rows="20"
        ></textarea>
        <div class="input-footer">
          <span class="char-count">{{ contractText.length }} 字符</span>
          <button
            class="btn btn-primary"
            :disabled="!contractText.trim() || store.loading"
            @click="submitReview"
          >
            <span v-if="store.loading" class="spinner"></span>
            {{ store.loading ? '分析中...' : '开始审查' }}
          </button>
        </div>
      </div>

      <!-- Right: analysis panel -->
      <div class="analysis-panel">
        <!-- Risk score gauge -->
        <div v-if="result || store.loading" class="score-card card">
          <div class="gauge-container">
            <div
              class="gauge-ring"
              :style="{ '--gauge-color': riskColor, '--gauge-progress': gaugePercent }"
            >
              <div class="gauge-fill"></div>
              <div class="gauge-center">
                <span class="gauge-value">{{ result?.total_score ?? 0 }}</span>
                <span class="gauge-label">综合风险分</span>
              </div>
            </div>
            <div class="risk-badge" :class="'risk-' + (result?.risk_level ?? 'safe')">
              {{ riskLabel }}
            </div>
          </div>
          <div class="score-stats">
            <div class="stat-item">
              <span class="stat-value">{{ result?.clauses_found ?? 0 }}</span>
              <span class="stat-label">识别条款</span>
            </div>
            <div class="stat-item">
              <span class="stat-value" :class="riskStatClass">
                {{ result?.risk_count ?? 0 }}
              </span>
              <span class="stat-label">风险条款</span>
            </div>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="empty-analysis card">
          <div class="empty-icon">&#9878;</div>
          <p>在左侧输入合同文本，点击"开始审查"查看风险分析结果。</p>
        </div>

        <!-- Clause list -->
        <div v-if="result?.clauses?.length" class="clause-list">
          <h3 class="section-title">条款分析明细</h3>
          <div
            v-for="(clause, idx) in result.clauses"
            :key="idx"
            class="clause-item card"
            :class="'level-' + (clause.risk_level ?? 'safe')"
          >
            <div class="clause-header">
              <span class="clause-index">#{{ clause.clause_index }}</span>
              <span class="clause-level" :class="'level-' + (clause.risk_level ?? 'safe')">
                {{ levelLabel(clause.risk_level) }}
              </span>
              <span v-if="clause.is_flagged" class="flag-badge">已标记</span>
            </div>
            <p class="clause-text">{{ clause.clause_text }}</p>
            <div v-if="clause.risk_description" class="clause-detail">
              <strong>风险说明：</strong>{{ clause.risk_description }}
            </div>
            <div v-if="clause.suggestion" class="clause-suggestion">
              <strong>建议修改：</strong>{{ clause.suggestion }}
            </div>
            <!-- Inline suggestion editor for flagged clauses -->
            <div v-if="clause.is_flagged && clause.suggestion" class="suggestion-editor">
              <textarea
                v-model="clauseEdits[idx]"
                class="edit-textarea"
                placeholder="输入修改后的条款内容..."
                rows="2"
              ></textarea>
              <button class="btn btn-ghost btn-xs" @click="saveClauseEdit(idx)">保存修改</button>
            </div>
          </div>
        </div>

        <!-- Suggestions section -->
        <div v-if="result?.suggestions?.length" class="suggestions-card card">
          <h3 class="section-title">通用建议</h3>
          <ul class="suggestions-list">
            <li v-for="(s, i) in result.suggestions" :key="i" class="suggestion-item">
              {{ s }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <!-- Review history -->
    <div class="history-section card">
      <div class="history-header">
        <h3>审查历史</h3>
        <button class="btn btn-secondary btn-sm" @click="loadHistory">刷新</button>
      </div>
      <div v-if="historyLoading" class="loading-hint">加载中...</div>
      <div v-else-if="history.length" class="history-table">
        <table>
          <thead>
            <tr>
              <th>类型</th>
              <th>分数</th>
              <th>风险等级</th>
              <th>条款数</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in history" :key="item.id">
              <td>{{ reviewTypeLabel(item.review_type) }}</td>
              <td>{{ item.total_score }}</td>
              <td>
                <span class="clause-level" :class="'level-' + item.risk_level">
                  {{ levelLabel(item.risk_level) }}
                </span>
              </td>
              <td>{{ item.clauses_found }}</td>
              <td class="mono">{{ formatDate(item.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="empty-hint">暂无审查记录</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useContractRiskStore } from '@/stores/useContractRiskStore'
import type { ContractReviewResult } from '@/types/contractRisk'

// ------------------------------------------------------------------
// Constants
// ------------------------------------------------------------------

const RISK_COLORS: Record<string, string> = {
  safe: '#22c55e',
  low: '#84cc16',
  medium: '#f59e0b',
  high: '#ef4444',
  critical: '#dc2626',
}

const RISK_LABELS: Record<string, string> = {
  safe: '安全',
  low: '低风险',
  medium: '中等风险',
  high: '高风险',
  critical: '严重风险',
}

const TABS = [
  { key: 'general', label: '通用合同审查' },
  { key: 'transaction', label: '交易合约预检' },
]

const SAMPLE_TEXT = `第一条 版权归属
甲方将本合同项下作品的全部著作权（包括但不限于复制权、发行权、改编权、信息网络传播权等）永久转让给乙方。

第二条 授权范围
甲方授予乙方在全球范围内、永久性的、不可撤销的、独占的许可，乙方可自行决定授权第三方使用本合同项下作品。

第三条 付款条件
乙方应在作品交付后30日内支付甲方首付款人民币10000元。后续收益分配按照乙方单方制定的标准执行。

第四条 自动续约
本合同自签署之日起生效，有效期为一年。除非甲方在到期前30日书面通知不续约，否则本合同自动续期一年，续期次数不限。

第五条 保密条款
甲方应对在履行本合同过程中知悉的乙方商业秘密承担保密义务。未经乙方书面同意，甲方不得向任何第三方披露。

第六条 违约责任
任何一方违反本合同约定，应向守约方支付违约金人民币50000元。若违约金不足以弥补守约方损失的，违约方还应赔偿全部损失。

第七条 争议解决
因本合同引起的或与本合同有关的任何争议，双方应友好协商解决。协商不成的，应提交乙方所在地人民法院诉讼解决。

第八条 不可抗力
因地震、台风、水灾、火灾、战争、政府行为等不可抗力导致本合同无法履行的，受影响方应及时通知对方并提供证明，可部分或全部免除责任。`

// ------------------------------------------------------------------
// State
// ------------------------------------------------------------------

const store = useContractRiskStore()
const activeTab = ref('general')
const contractText = ref('')
const history = ref<any[]>([])
const historyLoading = ref(false)
const clauseEdits = ref<Record<number, string>>({})

// ------------------------------------------------------------------
// Computed
// ------------------------------------------------------------------

const tabs = computed(() => TABS)

const result = computed<ContractReviewResult | null>(() => store.result)

const riskLevel = computed(() => result.value?.risk_level ?? 'safe')
const riskColor = computed(() => RISK_COLORS[riskLevel.value] ?? RISK_COLORS.safe)
const riskLabel = computed(() => RISK_LABELS[riskLevel.value] ?? riskLevel.value)

const gaugePercent = computed(() => {
  const score = result.value?.total_score ?? 0
  return Math.min(Math.max(score, 0), 100)
})

const riskStatClass = computed(() => {
  const lvl = riskLevel.value
  if (lvl === 'high' || lvl === 'critical') return 'text-red-600 font-bold'
  if (lvl === 'medium') return 'text-amber-600 font-semibold'
  return ''
})

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

function levelLabel(level: string | null): string {
  if (!level) return '—'
  return RISK_LABELS[level] || level
}

function reviewTypeLabel(type: string): string {
  return type === 'transaction' ? '交易预检' : '通用审查'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return '—'
  return dateStr.slice(0, 16).replace('T', ' ')
}

function clearInput() {
  contractText.value = ''
  store.clearResult()
  clauseEdits.value = {}
}

// ------------------------------------------------------------------
// Actions
// ------------------------------------------------------------------

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

function loadSample() {
  contractText.value = SAMPLE_TEXT
}

function saveClauseEdit(idx: number) {
  const edit = clauseEdits.value[idx]
  if (edit) {
    ;(window as any).$toast?.show('条款修改已保存', 'success')
    delete clauseEdits.value[idx]
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    await store.fetchHistory('local')
    history.value = store.history
  } catch {
    history.value = []
  } finally {
    historyLoading.value = false
  }
}

onMounted(loadHistory)
</script>

<style scoped>
.contract-risk-view {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Header */
.header h2 {
  font-size: 1.4rem;
  margin: 0 0 4px;
}
.subtitle {
  font-size: 0.85rem;
  color: var(--muted);
  margin: 0;
}

/* Tabs */
.tabs {
  padding: 6px;
  display: flex;
  gap: 4px;
  border-radius: var(--radius);
}
.tab-btn {
  flex: 1;
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  color: var(--muted);
  transition: all 0.15s;
  font-family: var(--font-body);
}
.tab-btn.active {
  background: var(--surface);
  color: var(--fg);
  box-shadow: 0 1px 3px oklch(0 0 0 / 0.08);
  font-weight: 600;
}
.tab-btn:hover:not(.active) {
  color: var(--fg);
}

/* Content grid */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}
@media (max-width: 1100px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

/* Input panel */
.input-panel {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.panel-title span {
  font-size: 0.95rem;
  font-weight: 700;
}
.input-actions {
  display: flex;
  gap: 8px;
}
.contract-textarea {
  flex: 1;
  min-height: 320px;
  padding: 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--fg);
  font-size: 0.88rem;
  font-family: var(--font-body);
  line-height: 1.6;
  resize: vertical;
  transition: border-color 0.2s;
}
.contract-textarea:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}
.contract-textarea::placeholder {
  color: var(--muted);
}
.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.char-count {
  font-size: 0.78rem;
  color: var(--muted);
}

/* Analysis panel */
.analysis-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Score card */
.score-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.gauge-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  flex-wrap: wrap;
}
.gauge-ring {
  position: relative;
  width: 140px;
  height: 140px;
  border-radius: 50%;
  background: conic-gradient(
    var(--gauge-color) calc(var(--gauge-progress) * 1%),
    var(--border) 0
  );
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.5s ease;
}
.gauge-fill {
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  background: var(--surface);
}
.gauge-center {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.gauge-value {
  font-size: 1.8rem;
  font-weight: 700;
  line-height: 1;
  color: var(--gauge-color);
}
.gauge-label {
  font-size: 0.7rem;
  color: var(--muted);
  margin-top: 4px;
}
.risk-badge {
  font-size: 0.85rem;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 100px;
}
.risk-safe {
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--green);
}
.risk-low {
  background: oklch(70% 0.15 100 / 0.1);
  color: #84cc16;
}
.risk-medium {
  background: oklch(62% 0.18 55 / 0.1);
  color: var(--orange);
}
.risk-high,
.risk-critical {
  background: oklch(58% 0.18 30 / 0.1);
  color: #e53e3e;
}

/* Score stats */
.score-stats {
  display: flex;
  gap: 24px;
  justify-content: center;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.stat-value {
  font-size: 1.3rem;
  font-weight: 700;
}
.stat-label {
  font-size: 0.75rem;
  color: var(--muted);
}

/* Empty analysis */
.empty-analysis {
  padding: 48px 24px;
  text-align: center;
  color: var(--muted);
  font-size: 0.88rem;
}
.empty-icon {
  font-size: 2.5rem;
  margin-bottom: 12px;
  opacity: 0.4;
}

/* Section title */
.section-title {
  font-size: 0.92rem;
  font-weight: 700;
  margin: 0 0 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

/* Clause items */
.clause-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.clause-item {
  padding: 16px;
  border-left: 4px solid var(--border);
  transition: border-color 0.2s;
}
.clause-item:hover {
  border-color: var(--muted);
}
.level-safe { border-left-color: #22c55e; }
.level-low { border-left-color: #84cc16; }
.level-medium { border-left-color: #f59e0b; }
.level-high { border-left-color: #ef4444; }
.level-critical { border-left-color: #dc2626; }

.clause-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.clause-index {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--muted);
}
.clause-text {
  font-size: 0.85rem;
  line-height: 1.5;
  margin: 0 0 8px;
  color: var(--fg);
}
.clause-detail {
  font-size: 0.8rem;
  color: var(--muted);
  margin-bottom: 4px;
}
.clause-suggestion {
  font-size: 0.8rem;
  color: var(--accent);
  margin-bottom: 8px;
}
.flag-badge {
  font-size: 0.68rem;
  padding: 1px 8px;
  border-radius: 100px;
  background: oklch(58% 0.18 30 / 0.1);
  color: #e53e3e;
  font-weight: 600;
}

/* Level color tags */
.level-safe { color: #22c55e; font-weight: 600; }
.level-low { color: #84cc16; font-weight: 600; }
.level-medium { color: #f59e0b; font-weight: 600; }
.level-high { color: #ef4444; font-weight: 600; }
.level-critical { color: #dc2626; font-weight: 600; }

/* Suggestion editor */
.suggestion-editor {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  align-items: flex-start;
}
.edit-textarea {
  flex: 1;
  padding: 8px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--fg);
  font-size: 0.8rem;
  font-family: var(--font-body);
  resize: vertical;
  min-height: 48px;
}
.edit-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

/* Suggestions card */
.suggestions-card {
  padding: 16px;
}
.suggestions-list {
  margin: 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.suggestion-item {
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--fg);
}

/* History section */
.history-section {
  padding: 16px;
}
.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.history-header h3 {
  margin: 0;
  font-size: 0.95rem;
  font-weight: 700;
}
.history-table {
  overflow-x: auto;
}
.history-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}
.history-table th {
  text-align: left;
  padding: 8px 12px;
  color: var(--muted);
  font-weight: 600;
  font-size: 0.75rem;
  border-bottom: 1px solid var(--border);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.history-table td {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border);
  color: var(--fg);
}
.history-table tr:last-child td {
  border-bottom: none;
}
.mono {
  font-family: 'SF Mono', 'Fira Code', monospace;
  font-size: 0.78rem;
}

/* Loading / empty hints */
.loading-hint,
.empty-hint {
  font-size: 0.82rem;
  color: var(--muted);
  text-align: center;
  padding: 16px;
}

/* Button sizes */
.btn-sm {
  padding: 5px 12px;
  font-size: 0.78rem;
}
.btn-xs {
  padding: 4px 10px;
  font-size: 0.72rem;
  white-space: nowrap;
  flex-shrink: 0;
}

/* Spinner */
.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid oklch(1 1 1 / 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
