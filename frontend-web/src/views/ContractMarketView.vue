<template>
  <div class="contract-market-view">
    <LoadingSpinner v-if="store.loading" text="加载中..." />
    <template v-else>
      <h2>合约市场</h2>
      <p class="subtitle">管理版权交易合约的全生命周期 — 挂牌、认购、托管、履约、验收</p>

      <!-- Tab 切换 -->
      <div class="tabs">
        <button :class="['tab', { active: tab === 'list' }]" @click="tab = 'list'">合约列表</button>
        <button :class="['tab', { active: tab === 'create' }]" @click="tab = 'create'">新建合约</button>
        <button v-if="currentId" :class="['tab', { active: tab === 'detail' }]" @click="tab = 'detail'">合约详情</button>
      </div>

      <!-- 合约列表 -->
      <div v-if="tab === 'list'" class="section">
        <div class="filter-bar">
          <select v-model="filterStatus" @change="doFilter">
            <option value="">全部状态</option>
            <option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option>
          </select>
        </div>

        <div v-if="contracts.length === 0" class="empty-state">
          暂无合约，点击「新建合约」创建第一个合约
        </div>
        <div v-else class="contract-table">
          <table>
            <thead>
              <tr>
                <th>标题</th>
                <th>状态</th>
                <th>金额</th>
                <th>类型</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="c in contracts" :key="c.id" @click="showDetail(c.id)">
                <td>{{ c.title }}</td>
                <td><span class="status-badge" :class="'status-' + c.status">{{ statusLabel(c.status) }}</span></td>
                <td>¥{{ c.total_amount.toLocaleString() }}</td>
                <td>{{ contractTypeLabel(c.contract_type) }}</td>
                <td>{{ formatDate(c.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 新建合约 -->
      <div v-if="tab === 'create'" class="section">
        <div class="form-grid">
          <div class="form-group">
            <label>合约标题 *</label>
            <input v-model="form.title" type="text" placeholder="例如：插画商业授权协议" />
          </div>
          <div class="form-group">
            <label>总金额 (CNY) *</label>
            <input v-model.number="form.total_amount" type="number" min="0" step="0.01" />
          </div>
          <div class="form-group">
            <label>合约类型</label>
            <select v-model="form.contract_type">
              <option value="non_exclusive_license">非独占许可</option>
              <option value="exclusive_license">独占许可</option>
              <option value="product_license">产品许可</option>
              <option value="copyright_transfer">著作权转让</option>
            </select>
          </div>
          <div class="form-group">
            <label>计费周期</label>
            <select v-model="form.billing_cycle">
              <option value="one_time">一次性</option>
              <option value="monthly">按月</option>
              <option value="quarterly">按季度</option>
              <option value="yearly">按年</option>
              <option value="revenue_share">分成</option>
            </select>
          </div>
          <div class="form-group">
            <label>使用范围</label>
            <select v-model="form.scope_usage">
              <option value="personal">个人使用</option>
              <option value="commercial">商业使用</option>
              <option value="resale">转售</option>
              <option value="modify">修改衍生</option>
            </select>
          </div>
          <div class="form-group">
            <label>地理范围</label>
            <select v-model="form.scope_geography">
              <option value="china">中国大陆</option>
              <option value="local">本地</option>
              <option value="national">全国</option>
              <option value="global">全球</option>
              <option value="eu">欧盟</option>
              <option value="us">美国</option>
              <option value="jp">日本</option>
            </select>
          </div>
          <div class="form-group">
            <label>授权期限</label>
            <input v-model="form.scope_duration" type="text" placeholder="例如：1year, 3years" />
          </div>
          <div class="form-group full-width">
            <label>描述</label>
            <textarea v-model="form.description" rows="3" placeholder="合约详细描述..."></textarea>
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-primary" @click="doCreate" :disabled="!form.title || !form.total_amount">创建合约</button>
          <button class="btn-secondary" @click="tab = 'list'">取消</button>
        </div>
      </div>

      <!-- 合约详情 -->
      <div v-if="tab === 'detail' && currentContract" class="section">
        <div class="detail-header">
          <h3>{{ currentContract.title }}</h3>
          <span class="status-badge large" :class="'status-' + currentContract.status">
            {{ statusLabel(currentContract.status) }}
          </span>
        </div>

        <div class="detail-grid">
          <div class="detail-field">
            <span class="field-label">合约类型</span>
            <span class="field-value">{{ contractTypeLabel(currentContract.contract_type) }}</span>
          </div>
          <div class="detail-field">
            <span class="field-label">总金额</span>
            <span class="field-value">¥{{ currentContract.total_amount.toLocaleString() }}</span>
          </div>
          <div class="detail-field">
            <span class="field-label">计费周期</span>
            <span class="field-value">{{ billingCycleLabel(currentContract.billing_cycle) }}</span>
          </div>
          <div class="detail-field">
            <span class="field-label">使用范围</span>
            <span class="field-value">{{ currentContract.scope_usage }}</span>
          </div>
          <div class="detail-field">
            <span class="field-label">地理范围</span>
            <span class="field-value">{{ currentContract.scope_geography }}</span>
          </div>
          <div class="detail-field">
            <span class="field-label">审核状态</span>
            <span class="field-value">{{ verifiedLabel(currentContract.verified) }}</span>
          </div>
          <div v-if="currentContract.description" class="detail-field full">
            <span class="field-label">描述</span>
            <span class="field-value">{{ currentContract.description }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div v-if="availableActions.length > 0" class="actions-section">
          <h4>可用操作</h4>
          <div class="action-buttons">
            <button
              v-for="act in availableActions"
              :key="act.status"
              class="btn-action"
              @click="doTransition(act.status)"
            >
              {{ actionLabel(act.status) }}
            </button>
          </div>
        </div>

        <!-- 时间线 -->
        <div class="timeline-section">
          <h4>时间线</h4>
          <div v-if="timeline.length === 0" class="empty-state">暂无事件记录</div>
          <div v-else class="timeline-list">
            <div v-for="(evt, idx) in timeline" :key="idx" class="timeline-item">
              <div class="timeline-dot"></div>
              <div class="timeline-content">
                <div class="timeline-event">{{ evt.label || evt.event }}</div>
                <div class="timeline-time">{{ formatDate(evt.timestamp) }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button class="btn-secondary" @click="tab = 'list'">返回列表</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useContractMarketStore } from '@/stores/useContractMarketStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const store = useContractMarketStore()
const tab = ref('list')
const filterStatus = ref('')
const currentId = ref<string | null>(null)

// Form state
const form = ref({
  title: '',
  description: '',
  total_amount: undefined as number | undefined,
  contract_type: 'non_exclusive_license',
  billing_cycle: 'one_time',
  scope_usage: 'commercial',
  scope_geography: 'china',
  scope_duration: '',
})

const contracts = computed(() => store.contracts)
const currentContract = computed(() => store.currentContract)
const statusLabels = computed(() => store.transitions?.labels ?? {})

const timeline = ref<Array<{ timestamp?: string; event: string; label?: string }>>([])

// Available actions for current contract status
const availableActions = computed(() => {
  if (!currentContract.value || !store.transitions) return []
  const status = currentContract.value.status
  const nextStatuses = store.transitions.valid_transitions[status] ?? []
  return nextStatuses.map(s => ({
    status: s,
    label: actionLabel(s),
  }))
})

function statusLabel(s: string): string {
  return store.transitions?.labels[s] ?? s
}

function contractTypeLabel(t: string): string {
  return {
    copyright_transfer: '著作权转让',
    product_license: '产品许可',
    exclusive_license: '独占许可',
    non_exclusive_license: '非独占许可',
  }[t] || t
}

function billingCycleLabel(c: string): string {
  return {
    one_time: '一次性',
    monthly: '按月',
    quarterly: '按季度',
    yearly: '按年',
    revenue_share: '分成',
  }[c] || c
}

function verifiedLabel(v: string): string {
  return { pending: '待审核', approved: '已通过', rejected: '已拒绝' }[v] || v
}

function actionLabel(s: string): string {
  const map: Record<string, string> = {
    listed: '挂牌发布',
    active: '生效确认',
    subscribed: '认购',
    escrowed: '发起托管',
    insured: '激活保险',
    executing: '开始履约',
    inspect: '提交验收',
    completed: '完成合约',
    dispute: '发起争议',
    resolved: '解决争议',
    refunded: '退款',
    cancelled: '取消合约',
    released: '释放托管',
  }
  return map[s] ?? s
}

function formatDate(d?: string): string {
  if (!d) return '-'
  return new Date(d).toLocaleDateString('zh-CN')
}

function doFilter() {
  store.loadContracts(filterStatus.value ? { status: filterStatus.value } : undefined)
}

function showDetail(id: string) {
  currentId.value = id
  tab.value = 'detail'
  store.loadContract(id)
  loadTimeline(id)
}

async function loadTimeline(id: string) {
  try {
    const data = await store.transitions
      ? { contract_id: id, timeline: [] }
      : { contract_id: id, timeline: [] }
    // Fetch timeline directly since store doesn't have a dedicated method
    const { getTimeline } = await import('@/api/contractMarket')
    const result = await getTimeline(id)
    timeline.value = result.timeline ?? []
  } catch {
    timeline.value = []
  }
}

async function doCreate() {
  if (!form.value.title || !form.value.total_amount) return
  const result = await store.createContract({
    title: form.value.title,
    description: form.value.description,
    total_amount: form.value.total_amount,
    contract_type: form.value.contract_type,
    billing_cycle: form.value.billing_cycle,
    scope_usage: form.value.scope_usage,
    scope_geography: form.value.scope_geography,
    scope_duration: form.value.scope_duration || undefined,
  })
  currentId.value = result.id
  tab.value = 'detail'
  await store.loadContract(result.id)
  await loadTimeline(result.id)
  // Reset form
  form.value = {
    title: '',
    description: '',
    total_amount: undefined,
    contract_type: 'non_exclusive_license',
    billing_cycle: 'one_time',
    scope_usage: 'commercial',
    scope_geography: 'china',
    scope_duration: '',
  }
}

async function doTransition(action: string) {
  if (!currentId.value) return
  try {
    await store.transition(currentId.value, action, { reason: '' })
    // Reload timeline after transition
    await loadTimeline(currentId.value)
  } catch {
    // Error handled by global axios interceptor
  }
}

// Initial load
store.loadTransitions()
store.loadContracts()
</script>

<style scoped>
.contract-market-view {
  max-width: 960px;
  margin: 0 auto;
}
h2 { font-size: 1.4rem; margin-bottom: 4px; }
.subtitle { color: var(--m-grey-500); font-size: 0.85rem; margin-bottom: 24px; }

.tabs { display: flex; gap: 8px; margin-bottom: 20px; }
.tab {
  padding: 8px 16px;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
}
.tab.active { background: var(--m-primary); color: white; border-color: var(--m-primary); }

.section { background: var(--m-surface); border: 1px solid var(--m-border); border-radius: var(--m-radius-sm); padding: 20px; }

.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.filter-bar select {
  padding: 6px 12px;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  background: var(--m-bg-subtle);
}

/* Table */
.contract-table { overflow-x: auto; }
.contract-table table {
  width: 100%;
  border-collapse: collapse;
}
.contract-table th,
.contract-table td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid var(--m-border);
  font-size: 0.9rem;
}
.contract-table th {
  font-weight: 600;
  color: var(--m-grey-500);
  font-size: 0.8rem;
}
.contract-table tbody tr { cursor: pointer; }
.contract-table tbody tr:hover { background: rgba(var(--m-success-rgb, 86, 202, 0), 0.04); }

/* Status badge */
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}
.status-badge.large { font-size: 0.9rem; padding: 4px 14px; }
.status-draft { background: #e2e8f0; color: #475569; }
.status-listed { background: #dbeafe; color: #1e40af; }
.status-active { background: #dcfce7; color: #166534; }
.status-subscribed { background: #fef3c7; color: #92400e; }
.status-escrowed { background: #e0e7ff; color: #3730a3; }
.status-insured { background: #f3e8ff; color: #7e22ce; }
.status-executing { background: #ccfbf1; color: #115e59; }
.status-inspect { background: #fef9c3; color: #854d0e; }
.status-completed { background: #dcfce7; color: #15803d; }
.status-dispute { background: #fee2e2; color: #991b1b; }
.status-resolved { background: #dbeafe; color: #1e40af; }
.status-refunded { background: #f1f5f9; color: #475569; }
.status-cancelled { background: #f1f5f9; color: #94a3b8; }

/* Form */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group.full-width { grid-column: 1 / -1; }
.form-group label { font-size: 0.85rem; font-weight: 600; }
.form-group input,
.form-group select,
.form-group textarea {
  padding: 8px 12px;
  border: 1px solid var(--m-border);
  border-radius: var(--m-radius-sm);
  background: var(--m-bg-subtle);
  font-size: 0.9rem;
}
.form-group textarea { resize: vertical; }

.form-actions { display: flex; gap: 12px; margin-top: 16px; }
.btn-primary {
  background: var(--m-primary);
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary {
  background: transparent;
  color: var(--m-on-surface);
  border: 1px solid var(--m-border);
  padding: 8px 20px;
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  font-size: 0.9rem;
}

/* Detail */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--m-border);
}
.detail-header h3 { margin: 0; font-size: 1.2rem; }

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 24px;
}
.detail-field { display: flex; flex-direction: column; gap: 2px; }
.detail-field.full { grid-column: 1 / -1; }
.field-label { font-size: 0.75rem; color: var(--m-grey-500); font-weight: 600; text-transform: uppercase; }
.field-value { font-size: 0.95rem; }

/* Actions */
.actions-section { margin-bottom: 24px; }
.actions-section h4 { margin: 0 0 12px; font-size: 0.95rem; }
.action-buttons { display: flex; flex-wrap: wrap; gap: 8px; }
.btn-action {
  padding: 6px 14px;
  border: 1px solid var(--m-primary);
  color: var(--m-primary);
  background: transparent;
  border-radius: var(--m-radius-sm);
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.15s;
}
.btn-action:hover { background: var(--m-primary); color: white; }

/* Timeline */
.timeline-section { margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--m-border); }
.timeline-section h4 { margin: 0 0 12px; font-size: 0.95rem; }
.timeline-list { display: flex; flex-direction: column; gap: 12px; }
.timeline-item { display: flex; gap: 12px; }
.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--m-primary);
  margin-top: 4px;
  flex-shrink: 0;
}
.timeline-content { flex: 1; }
.timeline-event { font-size: 0.9rem; font-weight: 500; }
.timeline-time { font-size: 0.75rem; color: var(--m-grey-500); }

.empty-state { text-align: center; padding: 48px; color: var(--m-grey-500); }
</style>
