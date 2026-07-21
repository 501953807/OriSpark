<template>
  <div class="view-page">
    <div class="page-header">
      <h1>委托管理</h1>
      <div class="header-actions">
        <button class="btn btn-outline btn-sm" @click="fetchDashboard">仪表盘</button>
        <button class="btn btn-primary btn-sm" @click="showNewModal = true; editingCommission = null; resetCommissionForm()">+ 新建委托</button>
      </div>
    </div>

    <div v-if="dashboard" class="dashboard-bar">
      <div class="dash-stat">
        <span class="dash-num">{{ dashboard.active_count }}</span>
        <span class="dash-label">活跃项目</span>
      </div>
      <div class="dash-stat">
        <span class="dash-num">{{ dashboard.pending_payment }}</span>
        <span class="dash-label">待收款</span>
      </div>
      <div class="dash-stat">
        <span class="dash-num">¥{{ dashboard.monthly_revenue }}</span>
        <span class="dash-label">本月收入</span>
      </div>
      <div class="dash-stat">
        <span class="dash-num">¥{{ dashboard.avg_ticket }}</span>
        <span class="dash-label">平均客单价</span>
      </div>
    </div>

    <!-- Kanban board via extracted component -->
    <CommissionKanban
      :commissions="store.commissions"
      :loading="loading"
      @select="viewDetail"
      @status-update="handleStatusUpdate"
    />

    <!-- New / Edit Commission Modal -->
    <div v-if="showNewModal" class="modal-overlay" @click.self="showNewModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header">
          <h3>{{ editingCommission ? '编辑委托' : '新建委托' }}</h3>
          <button class="modal-close-btn" @click="showNewModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>客户名称</label>
          <input v-model="commissionForm.client_name" class="form-input" placeholder="客户姓名或公司名" />
        </div>
        <div class="form-group">
          <label>作品标题</label>
          <input v-model="commissionForm.title" class="form-input" placeholder="相关作品" />
        </div>
        <div class="form-row-2">
          <div class="form-group">
            <label>金额</label>
            <input v-model.number="commissionForm.amount" type="number" class="form-input" placeholder="0.00" />
          </div>
          <div class="form-group">
            <label>货币</label>
            <select v-model="commissionForm.currency" class="form-select">
              <option>CNY</option>
              <option>USD</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label>截止日期</label>
          <input v-model="commissionForm.due_date" type="date" class="form-input" />
        </div>
        <div class="form-group">
          <label>优先级</label>
          <select v-model="commissionForm.priority" class="form-select">
            <option value="normal">普通</option>
            <option value="high">高</option>
            <option value="urgent">紧急</option>
          </select>
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="commissionForm.description" class="form-textarea" rows="3" placeholder="备注信息"></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showNewModal = false">取消</button>
          <button class="btn btn-primary" @click="saveCommission" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedCommission" class="modal-overlay" @click.self="selectedCommission = null">
      <div class="modal-card animate-scale-in" style="max-width:520px">
        <div class="modal-header">
          <h3>委托详情</h3>
          <button class="modal-close-btn" @click="selectedCommission = null">&times;</button>
        </div>
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">客户</span>
            <span class="detail-value">{{ selectedCommission.client_name || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">作品</span>
            <span class="detail-value">{{ selectedCommission.work_title || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">金额</span>
            <span class="detail-value detail-amount">{{ selectedCommission.currency === 'CNY' ? '¥' : '$' }}{{ selectedCommission.amount }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">状态</span>
            <span class="detail-value">
              <span class="badge-status" :class="'status-' + selectedCommission.status">{{ statusLabel(selectedCommission.status) }}</span>
            </span>
          </div>
          <div class="detail-item">
            <span class="detail-label">截止日期</span>
            <span class="detail-value">{{ selectedCommission.due_date || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">优先级</span>
            <span class="detail-value">
              <span class="priority-dot" :class="'priority-' + (selectedCommission.priority || 'normal')"></span>
              {{ priorityLabel(selectedCommission.priority) }}
            </span>
          </div>
          <div v-if="selectedCommission.description" class="detail-item full-width">
            <span class="detail-label">描述</span>
            <span class="detail-value detail-desc">{{ selectedCommission.description }}</span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="selectedCommission = null">关闭</button>
          <button class="btn btn-primary" @click="editFromDetail">编辑</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { systemApi } from '@/api/system'
import { useCommissionStore } from '@/stores/useCommissionStore'
import CommissionKanban from '@/components/commission/CommissionKanban.vue'
import type { CommissionProject } from '@/types/commission'

const router = useRouter()
const store = useCommissionStore()

const loading = ref(false)
const saving = ref(false)

const showNewModal = ref(false)
const editingCommission = ref<CommissionProject | null>(null)
const selectedCommission = ref<CommissionProject | null>(null)

const commissionForm = ref({
  client_name: '',
  title: '',
  amount: 0,
  currency: 'CNY',
  status: 'brief',
  due_date: '',
  priority: 'normal',
  description: '',
})

const dashboard = computed(() => store.dashboard)

const STATUS_LABELS: Record<string, string> = {
  brief: '需求',
  proposal: '提案',
  production: '制作中',
  delivery: '交付',
  settlement: '已结款',
}

function statusLabel(s: string): string {
  return STATUS_LABELS[s] || s
}

function priorityLabel(p?: string): string {
  const map: Record<string, string> = { high: '高', urgent: '紧急', normal: '普通' }
  return map[p || 'normal'] || '普通'
}

function resetCommissionForm() {
  commissionForm.value = {
    client_name: '',
    title: '',
    amount: 0,
    currency: 'CNY',
    status: 'brief',
    due_date: '',
    priority: 'normal',
    description: '',
  }
}

async function fetchDashboard() {
  try {
    await store.fetchDashboard()
    ;(window as any).$toast?.show('仪表盘数据已加载', 'success')
  } catch {
    ;(window as any).$toast?.show('仪表盘数据加载失败', 'error')
  }
}

function viewDetail(item: CommissionProject) {
  selectedCommission.value = item
}

function editFromDetail() {
  if (!selectedCommission.value) return
  editingCommission.value = selectedCommission.value
  commissionForm.value = {
    client_name: selectedCommission.value.client_name || '',
    title: selectedCommission.value.title || '',
    amount: 0,
    currency: 'CNY',
    status: selectedCommission.value.status || 'brief',
    due_date: selectedCommission.value.created_at || '',
    priority: 'normal',
    description: selectedCommission.value.description || '',
  }
  selectedCommission.value = null
  showNewModal.value = true
}

async function handleStatusUpdate(payload: {
  commissionId: string
  fromStatus: string
  toStatus: string
  commission: CommissionProject
}) {
  try {
    await store.updateCommissionStatus(payload.commissionId, payload.toStatus)
    const toLabel = STATUS_LABELS[payload.toStatus] || payload.toStatus
    const fromLabel = STATUS_LABELS[payload.fromStatus] || payload.fromStatus
    ;(window as any).$toast?.show(
      `已从「${fromLabel}」移至「${toLabel}」`,
      'success'
    )
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '状态更新失败'
    ;(window as any).$toast?.show(msg, 'error')
    // Roll back: re-fetch to restore correct state
    await store.fetchCommissions()
  }
}

async function saveCommission() {
  if (!commissionForm.value.client_name.trim()) {
    ;(window as any).$toast?.show('请输入客户名称', 'error')
    return
  }
  if (!commissionForm.value.title.trim()) {
    ;(window as any).$toast?.show('请输入相关作品', 'error')
    return
  }
  saving.value = true
  try {
    const data = {
      client_name: commissionForm.value.client_name,
      title: commissionForm.value.title,
      description: commissionForm.value.description,
      status: commissionForm.value.status,
    }
    if (editingCommission.value) {
      await systemApi.updateCommission(editingCommission.value.id, data)
      await store.fetchCommissions()
      ;(window as any).$toast?.show('委托已更新', 'success')
    } else {
      const res = await systemApi.createCommission(data)
      const created = res.data.data
      if (created) {
        await store.fetchCommissions()
      }
      ;(window as any).$toast?.show('委托已创建', 'success')
    }
    showNewModal.value = false
    editingCommission.value = null
    resetCommissionForm()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    ;(window as any).$toast?.show(typeof msg === 'string' ? msg : String(msg), 'error')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await store.fetchCommissions()
  } catch {
    store.commissions = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 16px; }

.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.header-actions { display: flex; align-items: center; gap: 8px; }

/* Dashboard Bar */
.dashboard-bar {
  display: flex; gap: 24px; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px 20px;
}
.dash-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.dash-num { font-size: 1.3rem; font-weight: 700; color: var(--accent); }
.dash-label { font-size: 0.75rem; color: var(--muted); }

/* Forms */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input, .form-textarea, .form-select {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; max-width: 400px;
}
.form-textarea { resize: vertical; width: 100%; max-width: 100%; }
.form-select { width: 100%; max-width: 100%; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; max-height:90vh; overflow-y:auto; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:4px; }

/* Detail modal */
.detail-grid { display: flex; flex-direction: column; gap: 12px; }
.detail-item { display: flex; align-items: center; gap: 12px; }
.detail-item.full-width { flex-direction: column; align-items: flex-start; }
.detail-label { font-size: 0.82rem; color: var(--muted); font-weight: 600; min-width: 80px; }
.detail-value { font-size: 0.9rem; }
.detail-amount { font-weight: 700; font-size: 1.1rem; color: var(--accent); }
.detail-desc { font-size: 0.88rem; line-height: 1.6; }
.badge-status {
  font-size: 0.75rem; padding: 3px 10px; border-radius: 10px; font-weight: 600;
}
.status-inquiry { background: oklch(62% 0.18 55 / 0.12); color: #b45309; }
.status-confirmed { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.status-production { background: oklch(58% 0.16 280 / 0.1); color: var(--purple); }
.status-delivery { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.status-settlement { background: var(--border); color: var(--muted); }
.priority-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }

@media (max-width: 768px) {
  .kanban-board { flex-direction: column; }
  .kanban-column { flex: none; width: 100%; min-height: 200px; }
  .form-input, .form-textarea, .form-select { max-width: 100%; width: 100%; }
  .form-row-2 { grid-template-columns: 1fr; }
}
</style>
