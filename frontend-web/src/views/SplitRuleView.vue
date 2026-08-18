<template>
  <div class="split-rule-view">
    <div v-if="errorMsg" class="error-toast" @click="errorMsg = ''">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success-toast">{{ successMsg }}</div>

    <!-- Contract selector -->
    <div class="card">
      <div class="card-header">
        <h3>合约 ID</h3>
      </div>
      <div class="contract-input-row">
        <input class="form-input" v-model="contractId" placeholder="输入合约 ID" />
        <button class="btn btn-primary" @click="loadRules" :disabled="loading">加载</button>
        <button class="btn btn-secondary" @click="contractId = ''; rules = []; calcResult = null; execResult = null">清空</button>
      </div>
    </div>

    <!-- Platform fee calculator -->
    <div class="card" v-if="contract">
      <div class="card-header">
        <h3>平台费用计算</h3>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label class="form-label">总金额 (CNY)</label>
          <input class="form-input" type="number" v-model.number="platformFeeInput" min="0" />
        </div>
        <button class="btn btn-accent" @click="calcPlatformFee">计算</button>
        <div v-if="platformFeeResult" class="fee-result">
          平台费 (3‰): <strong>¥{{ platformFeeResult.platform_fee.toFixed(2) }}</strong>
        </div>
      </div>
    </div>

    <!-- Current split rules -->
    <div class="card" v-if="rules.length > 0">
      <div class="card-header">
        <h3>当前分润规则</h3>
        <span class="badge badge-default">{{ rules.length }} 条</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th>角色</th>
            <th>参与方 ID</th>
            <th>比例</th>
            <th>报价金额</th>
            <th>报价时间</th>
            <th>锁定时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rules" :key="r.id">
            <td><span class="role-badge" :class="'role-' + r.role">{{ roleLabel(r.role) }}</span></td>
            <td class="id-cell">{{ r.participant_id?.slice(0, 8) }}...</td>
            <td>{{ (r.percentage * 100).toFixed(1) }}%</td>
            <td>{{ r.quote_amount ? '¥' + Number(r.quote_amount).toFixed(2) : '-' }}</td>
            <td>{{ formatDateTime(r.quoted_at) }}</td>
            <td>{{ r.locked_at ? formatDateTime(r.locked_at) : '<em>未锁定</em>' }}</td>
          </tr>
        </tbody>
      </table>
      <div class="card-footer" style="margin-top: 12px">
        <button class="btn btn-primary" @click="showQuoteModal = true" :disabled="!canSubmitQuote">提交报价</button>
        <button class="btn btn-accent" @click="handleLockQuotes" :disabled="!canLockQuotes">锁定最优报价</button>
        <button class="btn btn-secondary" @click="loadRules">刷新</button>
      </div>
    </div>

    <!-- No rules state -->
    <div class="card" v-else-if="contract && !loading">
      <div class="empty-state">
        <div class="empty-icon">📋</div>
        <div class="empty-title">暂无分润规则</div>
        <div class="empty-desc">合约状态为「挂牌」时可提交报价进行分润竞争</div>
        <button class="btn btn-primary" @click="showQuoteModal = true" :disabled="!canSubmitQuote" style="margin-top: 16px">提交第一笔报价</button>
      </div>
    </div>

    <!-- Quote modal -->
    <div class="modal-overlay" v-if="showQuoteModal">
      <div class="modal-card">
        <h3>提交分润报价</h3>
        <div class="form-group">
          <label class="form-label">角色</label>
          <select class="form-select" v-model="quoteForm.role">
            <option v-for="opt in roleOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">参与方 ID</label>
          <input class="form-input" v-model="quoteForm.participant_id" placeholder="你的用户 ID" />
        </div>
        <div class="form-group">
          <label class="form-label">分润比例 (%)</label>
          <input class="form-input" type="number" v-model.number="quoteForm.percentage" min="0.001" max="1" step="0.001" />
        </div>
        <div class="form-group">
          <label class="form-label">报价金额 (CNY)</label>
          <input class="form-input" type="number" v-model.number="quoteForm.quote_amount" min="0" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showQuoteModal = false">取消</button>
          <button class="btn btn-primary" @click="handleSubmitQuote">提交报价</button>
        </div>
      </div>
    </div>

    <!-- Calculate & Execute section -->
    <div class="card" v-if="rules.length > 0 || (contract && contract.split_rules_json && contract.split_rules_json !== '[]')">
      <div class="card-header">
        <h3>分润执行</h3>
      </div>
      <div class="action-row">
        <button class="btn btn-accent" @click="handleCalculate" :disabled="loading">计算分润方案</button>
        <button class="btn btn-primary" @click="showExecuteModal = true" :disabled="!calcResult || loading">执行分润</button>
        <button class="btn btn-danger" @click="showRefundModal = true" :disabled="!hasExecutedRecord || loading">申请退款</button>
      </div>

      <!-- Calculation result -->
      <div v-if="calcResult" class="calc-result">
        <div class="calc-summary">
          <div class="calc-item">
            <span class="calc-label">合约金额</span>
            <span class="calc-value">¥{{ calcResult.total_amount.toFixed(2) }}</span>
          </div>
          <div class="calc-item">
            <span class="calc-label">平台费用 (3‰)</span>
            <span class="calc-value" style="color: var(--orange)">¥{{ calcResult.platform_fee.toFixed(2) }}</span>
          </div>
        </div>
        <table class="data-table" style="margin-top: 12px">
          <thead>
            <tr>
              <th>角色</th>
              <th>比例</th>
              <th>分配金额</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in calcResult.distributions" :key="d.role">
              <td><span class="role-badge" :class="'role-' + d.role">{{ roleLabel(d.role) }}</span></td>
              <td>{{ (d.percentage * 100).toFixed(1) }}%</td>
              <td class="amount">¥{{ d.amount.toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Execution result -->
    <div class="card" v-if="execResult">
      <div class="card-header">
        <h3>执行结果</h3>
        <span class="badge" :class="execResult.status === 'success' ? 'badge-success' : 'badge-danger'">
          {{ execResult.status === 'success' ? '执行成功' : '执行失败' }}
        </span>
      </div>
      <div class="exec-detail">
        <p><strong>批次号:</strong> {{ execResult.batch_id }}</p>
        <p><strong>执行日志ID:</strong> {{ execResult.log_id?.slice(0, 8) }}...</p>
        <p v-if="execResult.error" class="exec-error"><strong>错误:</strong> {{ execResult.error }}</p>
      </div>
    </div>

    <!-- Execute modal -->
    <div class="modal-overlay" v-if="showExecuteModal">
      <div class="modal-card">
        <h3>确认执行分润</h3>
        <p v-if="calcResult" class="exec-preview">
          总金额: ¥{{ calcResult.total_amount.toFixed(2) }} ·
          平台费: ¥{{ calcResult.platform_fee.toFixed(2) }}
        </p>
        <div class="form-group">
          <label class="form-label">自定义总金额 (可选)</label>
          <input class="form-input" type="number" v-model.number="execForm.total_amount" placeholder="留空使用合约金额" min="0" />
        </div>
        <div class="form-group">
          <label class="form-label">批次号 (可选)</label>
          <input class="form-input" v-model="execForm.batch_id" placeholder="留空自动生成" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showExecuteModal = false">取消</button>
          <button class="btn btn-primary" @click="handleExecute" :disabled="loading">确认执行</button>
        </div>
      </div>
    </div>

    <!-- Refund modal -->
    <div class="modal-overlay" v-if="showRefundModal">
      <div class="modal-card">
        <h3>申请退款分润</h3>
        <div class="form-group">
          <label class="form-label">退款原因</label>
          <textarea class="form-textarea" v-model="refundForm.reason" placeholder="请输入退款原因" rows="3" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showRefundModal = false">取消</button>
          <button class="btn btn-danger" @click="handleRefund" :disabled="loading">确认退款</button>
        </div>
      </div>
    </div>

    <!-- Refund result -->
    <div class="card" v-if="refundResult">
      <div class="card-header">
        <h3>退款结果</h3>
        <span class="badge badge-success">已退款</span>
      </div>
      <div class="exec-detail">
        <p><strong>日志ID:</strong> {{ refundResult.log_id?.slice(0, 8) }}...</p>
        <p><strong>退款原因:</strong> {{ refundResult.reason }}</p>
        <p v-if="refundResult.refunded_at"><strong>退款时间:</strong> {{ formatDateTime(refundResult.refunded_at) }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  getContract,
  getSplitRules,
  submitQuote,
  lockSplitQuotes,
  calculateSplit,
  executeSplit,
  refundSplit,
  getPlatformFee,
} from '@/api/contractMarket'

// ── State ──────────────────────────────────────────────
const contractId = ref('')
const loading = ref(false)
const errorMsg = ref('')
const successMsg = ref('')
const contract = ref<any>(null)
const rules = ref<any[]>([])
const calcResult = ref<any>(null)
const execResult = ref<any>(null)
const refundResult = ref<any>(null)

const platformFeeInput = ref(0)
const platformFeeResult = ref<any>(null)

const showQuoteModal = ref(false)
const showExecuteModal = ref(false)
const showRefundModal = ref(false)

const quoteForm = ref({
  participant_id: '',
  role: 'operator',
  percentage: 0.15,
  quote_amount: 0,
})

const execForm = ref({ total_amount: null as number | null, batch_id: '' })
const refundForm = ref({ reason: '' })

// ── Computed ───────────────────────────────────────────
const canSubmitQuote = computed(() => {
  if (!contract.value) return false
  return contract.value.status === 'listed'
})

const canLockQuotes = computed(() => {
  if (!contract.value) return false
  return contract.value.status === 'listed' && rules.value.some(r => !r.locked_at)
})

const hasExecutedRecord = computed(() => !!execResult.value && execResult.value.status === 'success')

const roleOptions = [
  { label: '运营方 (Operator)', value: 'operator' },
  { label: '法务代表 (Legal Rep)', value: 'legal_rep' },
  { label: '税务代理 (Tax Agent)', value: 'tax_agent' },
  { label: '物流方 (Logistics)', value: 'logistics' },
  { label: '保险方 (Insurer)', value: 'insurer' },
]

// ── Actions ────────────────────────────────────────────
async function loadContract() {
  if (!contractId.value) return
  loading.value = true
  try {
    const data = await getContract(contractId.value)
    contract.value = data
    await loadRules()
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '加载失败'
    contract.value = null
    rules.value = []
  } finally {
    loading.value = false
  }
}

async function loadRules() {
  if (!contractId.value) return
  loading.value = true
  try {
    const data = await getSplitRules(contractId.value)
    rules.value = (data?.rules ?? []) as any[]
    calcResult.value = null
    execResult.value = null
    refundResult.value = null
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '加载失败'
    rules.value = []
  } finally {
    loading.value = false
  }
}

async function handleSubmitQuote() {
  if (!quoteForm.value.participant_id || !contractId.value) return
  try {
    await submitQuote({
      contract_id: contractId.value,
      participant_id: quoteForm.value.participant_id,
      role: quoteForm.value.role,
      percentage: quoteForm.value.percentage,
      quote_amount: quoteForm.value.quote_amount,
    })
    showQuoteModal.value = false
    successMsg.value = '报价提交成功'
    setTimeout(() => { successMsg.value = '' }, 3000)
    await loadRules()
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '报价失败'
  }
}

async function handleLockQuotes() {
  if (!contractId.value) return
  loading.value = true
  try {
    const data = await lockSplitQuotes(contractId.value)
    successMsg.value = `已锁定 ${data?.locked_rules?.length ?? 0} 条报价`
    setTimeout(() => { successMsg.value = '' }, 3000)
    await loadRules()
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '锁定失败'
  } finally {
    loading.value = false
  }
}

async function handleCalculate() {
  if (!contractId.value) return
  loading.value = true
  try {
    calcResult.value = await calculateSplit(contractId.value)
    execResult.value = null
    refundResult.value = null
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '计算失败'
  } finally {
    loading.value = false
  }
}

async function handleExecute() {
  if (!contractId.value) return
  loading.value = true
  try {
    execResult.value = await executeSplit(contractId.value, {
      total_amount: execForm.value.total_amount ?? undefined,
      batch_id: execForm.value.batch_id || undefined,
    })
    refundResult.value = null
    showExecuteModal.value = false
    successMsg.value = '分润执行成功'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '执行失败'
  } finally {
    loading.value = false
  }
}

async function handleRefund() {
  if (!contractId.value || !refundForm.value.reason) return
  loading.value = true
  try {
    refundResult.value = await refundSplit(contractId.value, refundForm.value.reason)
    showRefundModal.value = false
    successMsg.value = '退款申请已提交'
    setTimeout(() => { successMsg.value = '' }, 3000)
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '退款失败'
  } finally {
    loading.value = false
  }
}

async function calcPlatformFee() {
  if (!platformFeeInput.value || platformFeeInput.value <= 0) return
  try {
    platformFeeResult.value = await getPlatformFee(platformFeeInput.value)
  } catch (e: unknown) {
    errorMsg.value = (e as Error).message || '计算失败'
  }
}

// ── Utilities ──────────────────────────────────────────
function roleLabel(role: string): string {
  const map: Record<string, string> = {
    creator: '创作者', operator: '运营方', legal_rep: '法务代表',
    tax_agent: '税务代理', logistics: '物流方', insurer: '保险方',
    trader: '采购方', payment_provider: '支付方', platform: '平台',
  }
  return map[role] || role
}

function formatDateTime(iso?: string | null): string {
  if (!iso) return '-'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => {
  const params = new URLSearchParams(window.location.search)
  const cid = params.get('contract_id')
  if (cid) contractId.value = cid
})
</script>

<style scoped>
.split-rule-view { display: flex; flex-direction: column; gap: 16px; }

.contract-input-row {
  display: flex; gap: 10px; align-items: flex-end;
  padding: 12px;
}
.contract-input-row .form-input { flex: 1; }

.form-row { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.form-row .form-group { flex: 1; min-width: 160px; }

.fee-result {
  padding: 8px 14px; background: rgba(2,132,199, 0.06); border-radius: var(--m-radius-sm);
  font-size: 0.88rem; align-self: center;
}

.action-row { display: flex; gap: 10px; flex-wrap: wrap; }

.calc-result { margin-top: 12px; }
.calc-summary {
  display: flex; gap: 24px; padding: 12px;
  background: var(--m-bg-subtle); border-radius: var(--m-radius-sm);
}
.calc-item { display: flex; flex-direction: column; gap: 4px; }
.calc-label { font-size: 0.78rem; color: var(--m-grey-500); }
.calc-value { font-size: 1.2rem; font-weight: 700; }

.exec-detail { padding: 12px; font-size: 0.88rem; line-height: 1.8; }
.exec-error { color: var(--red); }
.exec-preview { color: var(--m-grey-500); font-size: 0.85rem; margin-bottom: 12px; }

.role-badge {
  display: inline-block; padding: 2px 10px; border-radius: 100px;
  font-size: 0.78rem; font-weight: 600;
}
.role-creator { background: rgba(234,88,12, 0.06); color: #fff; }
.role-operator { background: rgba(99,102,241, 0.06); color: #fff; }
.role-legal_rep { background: rgba(79,70,229, 0.06); color: #fff; }
.role-tax_agent { background: rgba(217,119,6, 0.06); color: #fff; }
.role-logistics { background: rgba(22,163,74, 0.06); color: #fff; }
.role-insurer { background: rgba(22,163,74, 0.06); color: #fff; }
.role-platform { background: rgba(79,70,229, 0.06); color: #fff; }

.id-cell { font-family: monospace; font-size: 0.78rem; color: var(--m-grey-500); }
.amount { font-weight: 700; color: #ea580c; }

/* Toasts */
.error-toast {
  position: fixed; top: 20px; right: 20px; z-index: 9999;
  padding: 12px 20px; background: var(--red); color: #fff;
  border-radius: var(--m-radius-sm); font-size: 0.85rem; cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,.15); animation: slideIn .2s ease;
}
.success-toast {
  position: fixed; top: 20px; right: 20px; z-index: 9999;
  padding: 12px 20px; background: rgba(22,163,74, 0.06); color: #fff;
  border-radius: var(--m-radius-sm); font-size: 0.85rem;
  box-shadow: 0 4px 12px rgba(0,0,0,.15); animation: slideIn .2s ease;
}
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

.card-footer { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }

/* Empty state reuse */
.empty-state { padding: 40px; text-align: center; color: var(--m-grey-500); }
.empty-icon { font-size: 3rem; margin-bottom: 12px; }
.empty-title { font-size: 1.1rem; font-weight: 600; color: var(--m-on-surface); margin-bottom: 8px; }
.empty-desc { font-size: 0.88rem; }
</style>
