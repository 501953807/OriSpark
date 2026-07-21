<template>
  <div class="view-page">
    <div class="page-header">
      <div class="header-left">
        <button class="btn btn-link btn-sm" @click="router.back()">&larr; 返回</button>
        <h1>{{ project?.title || '委托详情' }}</h1>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline btn-sm" @click="fetchDashboard">仪表盘</button>
        <button class="btn btn-secondary btn-sm" @click="editing = true; showEditModal = true">编辑</button>
      </div>
    </div>

    <!-- Dashboard bar -->
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

    <div v-if="loading" class="loading-overlay">加载中...</div>

    <template v-if="project">
      <!-- Tabs -->
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

      <!-- Overview tab -->
      <div v-if="activeTab === 'overview'" class="tab-content">
        <div class="detail-grid">
          <div class="detail-item">
            <span class="detail-label">客户</span>
            <span class="detail-value">{{ project.client_name || '-' }}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">状态</span>
            <span class="detail-value">
              <span class="badge-status" :class="'status-' + project.status">{{ statusLabel(project.status) }}</span>
            </span>
          </div>
          <div class="detail-item" v-if="project.description">
            <span class="detail-label">描述</span>
            <span class="detail-value detail-desc">{{ project.description }}</span>
          </div>
        </div>
      </div>

      <!-- Milestones tab -->
      <div v-if="activeTab === 'milestones'" class="tab-content">
        <div class="tab-header">
          <h3>里程碑</h3>
          <button class="btn btn-primary btn-sm" @click="addMilestone">+ 新建里程碑</button>
        </div>
        <div v-if="milestones.length === 0" class="empty-state">暂无里程碑</div>
        <div v-else class="milestone-list">
          <div v-for="m in milestones" :key="m.id" class="milestone-card">
            <div class="milestone-info">
              <div class="milestone-name">{{ m.name }}</div>
              <div class="milestone-meta">
                <span class="milestone-status" :class="'status-' + m.status">{{ statusLabel(m.status) }}</span>
                <span v-if="m.due_date" class="milestone-date">截止: {{ m.due_date }}</span>
              </div>
            </div>
            <div class="milestone-actions">
              <button class="btn btn-link btn-sm" @click="completeMilestone(m)">完成</button>
              <button class="btn btn-link btn-sm" style="color: #ef4444;" @click="removeMilestone(m.id)">删除</button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="activeTab === 'payments'" class="tab-content">
        <div class="tab-header">
          <h3>收款记录</h3>
          <button class="btn btn-primary btn-sm" @click="showPaymentModal = true">+ 新建收款</button>
        </div>
        <div v-if="payments.length === 0" class="empty-state">暂无收款记录</div>
        <div v-else class="payment-list">
          <div v-for="p in payments" :key="p.id" class="payment-card">
            <div class="payment-info-left">
              <div class="payment-amount">¥{{ p.amount }}</div>
              <div class="payment-meta">
                <span class="milestone-status" :class="'status-' + p.status">{{ statusLabel(p.status) }}</span>
                <span class="payment-method">{{ p.method }}</span>
                <span v-if="p.paid_at" class="payment-date">{{ p.paid_at }}</span>
              </div>
            </div>
            <div class="payment-actions">
              <button class="btn btn-link btn-sm" @click="markPaymentReceived(p)">确认收款</button>
              <button class="btn btn-link btn-sm" style="color: #ef4444;" @click="removePayment(p.id)">删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Timeline tab -->
      <div v-if="activeTab === 'timeline'" class="tab-content">
        <h3>时间线</h3>
        <div v-if="!timeline || timeline.length === 0" class="empty-state">暂无时间线</div>
        <div v-else class="timeline-list">
          <div v-for="ev in timeline" :key="ev.id" class="timeline-event">
            <div class="timeline-dot" :class="'dot-' + ev.type"></div>
            <div class="timeline-content">
              <div class="timeline-title">{{ ev.title }}</div>
              <div v-if="ev.description" class="timeline-desc">{{ ev.description }}</div>
              <div class="timeline-date">{{ ev.date }}</div>
            </div>
          </div>
        </div>
      </div>
      <!-- Calendar tab -->
      <div v-if="activeTab === 'calendar'" class="tab-content">
        <CommissionCalendar :events="calendarEvents" :loading="calendarLoading" />
      </div>

      <!-- Revisions tab -->
      <div v-if="activeTab === 'revisions'" class="tab-content">
        <div class="tab-header">
          <h3>修改/反馈记录</h3>
          <button class="btn btn-primary btn-sm" @click="showRevisionModal = true">+ 新建修改</button>
        </div>
        <div v-if="revisions.length === 0" class="empty-state">暂无修改记录</div>
        <div v-else class="revision-list">
          <div v-for="r in revisions" :key="r.id" class="revision-card">
            <div class="revision-info">
              <div class="revision-desc">{{ r.description }}</div>
              <div class="revision-meta">
                <span class="revision-by">{{ r.created_by === 'artist' ? '创作者' : '客户' }}</span>
                <span v-if="r.client_feedback" class="revision-feedback">客户反馈: {{ r.client_feedback }}</span>
                <span class="revision-date">{{ r.created_at }}</span>
              </div>
            </div>
            <div class="revision-actions">
              <button class="btn btn-link btn-sm" style="color: #ef4444;" @click="removeRevision(r.id)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Payment modal -->
    <div v-if="showPaymentModal" class="modal-overlay" @click.self="showPaymentModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>新建收款</h3>
          <button class="modal-close-btn" @click="showPaymentModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>金额</label>
          <input v-model.number="paymentForm.amount" type="number" class="form-input" placeholder="0.00" />
        </div>
        <div class="form-group">
          <label>方式</label>
          <select v-model="paymentForm.method" class="form-select">
            <option>银行转账</option>
            <option>支付宝</option>
            <option>微信</option>
            <option>现金</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showPaymentModal = false">取消</button>
          <button class="btn btn-primary" @click="handleCreatePayment" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Milestone modal -->
    <div v-if="showMilestoneModal" class="modal-overlay" @click.self="resetMilestoneForm">
      <div class="modal-card">
        <div class="modal-header">
          <h3>新建里程碑</h3>
          <button class="modal-close-btn" @click="resetMilestoneForm">&times;</button>
        </div>
        <div class="form-group">
          <label>名称</label>
          <input v-model="milestoneForm.name" class="form-input" placeholder="里程碑名称" />
        </div>
        <div class="form-group">
          <label>截止日期</label>
          <input v-model="milestoneForm.due_date" type="date" class="form-input" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="milestoneForm.description" class="form-textarea" rows="2" placeholder="可选"></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="resetMilestoneForm">取消</button>
          <button class="btn btn-primary" @click="handleCreateMilestone">创建</button>
        </div>
      </div>
    </div>

    <!-- Revision modal -->
    <div v-if="showRevisionModal" class="modal-overlay" @click.self="showRevisionModal = false">
      <div class="modal-card">
        <div class="modal-header">
          <h3>新建修改记录</h3>
          <button class="modal-close-btn" @click="showRevisionModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="revisionForm.description" class="form-textarea" rows="3" placeholder="修改内容"></textarea>
        </div>
        <div class="form-group">
          <label>客户反馈</label>
          <textarea v-model="revisionForm.client_feedback" class="form-textarea" rows="2" placeholder="可选"></textarea>
        </div>
        <div class="form-group">
          <label>创建者</label>
          <select v-model="revisionForm.created_by" class="form-select">
            <option value="artist">创作者</option>
            <option value="client">客户</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showRevisionModal = false">取消</button>
          <button class="btn btn-primary" @click="handleCreateRevision">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCommissionStore } from '@/stores/useCommissionStore'
import { commissionApi } from '@/api/commission'
import CommissionCalendar from '@/components/commission/CommissionCalendar.vue'
import type { CommissionProject, Milestone, Payment, Revision, TimelineEvent, CalendarEvent } from '@/types/commission'

const route = useRoute()
const router = useRouter()
const store = useCommissionStore()

const projectId = route.params.id as string

const project = ref<CommissionProject | null>(null)
const milestones = ref<Milestone[]>([])
const payments = ref<Payment[]>([])
const revisions = ref<Revision[]>([])
const timeline = ref<TimelineEvent[]>([])
const dashboard = ref<Record<string, number> | null>(null)
const calendarEvents = ref<CalendarEvent[]>([])
const calendarLoading = ref(false)
const loading = ref(true)
const saving = ref(false)

const activeTab = ref('overview')
const showEditModal = ref(false)
const showPaymentModal = ref(false)
const showRevisionModal = ref(false)
const editing = ref(false)

const paymentForm = ref({
  amount: 0,
  method: '银行转账',
})

const milestoneForm = ref({
  name: '',
  due_date: '',
  description: '',
})

const showMilestoneModal = ref(false)

const revisionForm = ref({
  description: '',
  client_feedback: '',
  created_by: 'artist',
})

const tabs = [
  { key: 'overview', label: '概览' },
  { key: 'milestones', label: '里程碑' },
  { key: 'payments', label: '收款' },
  { key: 'revisions', label: '修改' },
  { key: 'timeline', label: '时间线' },
  { key: 'calendar', label: '日历' },
]

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '待接单', in_progress: '进行中', review: '待审核',
    completed: '已完成', canceled: '已取消',
  }
  return map[s] || s
}

async function fetchData() {
  loading.value = true
  try {
    const proj = await store.fetchCommissionDetail(projectId)
    project.value = proj

    await store.fetchMilestones(projectId)
    milestones.value = store.milestones

    await store.fetchPayments(projectId)
    payments.value = store.payments

    await store.fetchTimeline(projectId)
    timeline.value = (store.timeline as unknown as TimelineEvent[]) ?? []

    await store.fetchRevisions(projectId)
    revisions.value = store.revisions

    // Load calendar events for current month
    const now = new Date()
    const fromStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`
    const nextMonth = now.getMonth() === 11 ? 0 : now.getMonth() + 1
    const nextYear = now.getMonth() === 11 ? now.getFullYear() + 1 : now.getFullYear()
    const toStr = `${nextYear}-${String(nextMonth + 1).padStart(2, '0')}-01`
    await loadCalendar(fromStr, toStr)
  } catch {
    ;(window as any).$toast?.show('加载失败', 'error')
  } finally {
    loading.value = false
  }
}

async function fetchDashboard() {
  try {
    const data = await store.fetchDashboard()
    if (data) dashboard.value = data
    ;(window as any).$toast?.show('仪表盘数据已加载', 'success')
  } catch {
    ;(window as any).$toast?.show('仪表盘数据加载失败', 'error')
  }
}

async function addMilestone() {
  milestoneForm.value = { name: '', due_date: '', description: '' }
  showMilestoneModal.value = true
}

function resetMilestoneForm() {
  milestoneForm.value = { name: '', due_date: '', description: '' }
  showMilestoneModal.value = false
}

async function handleCreateMilestone() {
  if (!milestoneForm.value.name.trim()) {
    ;(window as any).$toast?.show('请输入里程碑名称', 'error')
    return
  }
  try {
    await store.createMilestone(projectId!, {
      name: milestoneForm.value.name,
      due_date: milestoneForm.value.due_date || undefined,
      description: milestoneForm.value.description || undefined,
    })
    milestones.value = store.milestones
    resetMilestoneForm()
    ;(window as any).$toast?.show('里程碑已创建', 'success')
  } catch {
    ;(window as any).$toast?.show('创建失败', 'error')
  }
}

async function completeMilestone(m: Milestone) {
  try {
    await store.updateMilestone(projectId!, m.id, { status: 'completed' })
    milestones.value = store.milestones
    ;(window as any).$toast?.show('里程碑已完成', 'success')
  } catch {
    ;(window as any).$toast?.show('更新失败', 'error')
  }
}

async function removeMilestone(milestoneId: string) {
  try {
    await store.deleteMilestone(projectId!, milestoneId)
    milestones.value = store.milestones
    ;(window as any).$toast?.show('里程碑已删除', 'success')
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

async function handleCreatePayment() {
  if (!paymentForm.value.amount || paymentForm.value.amount <= 0) {
    ;(window as any).$toast?.show('请输入有效金额', 'error')
    return
  }
  saving.value = true
  try {
    await store.createPayment(projectId!, {
      amount: paymentForm.value.amount,
      method: paymentForm.value.method,
    })
    payments.value = store.payments
    showPaymentModal.value = false
    paymentForm.value = { amount: 0, method: '银行转账' }
    ;(window as any).$toast?.show('收款已记录', 'success')
  } catch {
    ;(window as any).$toast?.show('保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function loadCalendar(from: string, to: string) {
  calendarLoading.value = true
  try {
    await store.fetchCalendar(from, to)
    calendarEvents.value = store.calendarEvents
  } catch {
    calendarEvents.value = []
    ;(window as any).$toast?.show('日历数据加载失败', 'error')
  } finally {
    calendarLoading.value = false
  }
}

async function handleCreateRevision() {
  if (!revisionForm.value.description.trim()) {
    ;(window as any).$toast?.show('请输入修改描述', 'error')
    return
  }
  try {
    await store.createRevision(projectId!, {
      description: revisionForm.value.description,
      client_feedback: revisionForm.value.client_feedback || undefined,
      created_by: revisionForm.value.created_by,
    })
    revisions.value = store.revisions
    showRevisionModal.value = false
    revisionForm.value = { description: '', client_feedback: '', created_by: 'artist' }
    ;(window as any).$toast?.show('修改记录已创建', 'success')
  } catch {
    ;(window as any).$toast?.show('创建失败', 'error')
  }
}

async function removeRevision(revisionId: string) {
  try {
    await commissionApi.deleteRevision(projectId!, revisionId)
    revisions.value = revisions.value.filter((r: Revision) => r.id !== revisionId)
    ;(window as any).$toast?.show('修改记录已删除', 'success')
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

async function markPaymentReceived(payment: Payment) {
  try {
    await store.updatePayment(projectId!, payment.id, { status: 'received' })
    payments.value = store.payments
    ;(window as any).$toast?.show('收款已确认', 'success')
  } catch {
    ;(window as any).$toast?.show('更新失败', 'error')
  }
}

async function removePayment(paymentId: string) {
  try {
    await commissionApi.deletePayment(projectId!, paymentId)
    payments.value = payments.value.filter((p: Payment) => p.id !== paymentId)
    ;(window as any).$toast?.show('收款已删除', 'success')
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

fetchData()
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 16px; }

.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.header-actions { display: flex; align-items: center; gap: 8px; }
.btn-link { background: none; border: none; color: var(--accent); cursor: pointer; font-size: 0.85rem; text-decoration: underline; padding: 0; }
.btn-link:hover { opacity: 0.8; }

/* Dashboard Bar */
.dashboard-bar {
  display: flex; gap: 24px; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px 20px;
}
.dash-stat { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.dash-num { font-size: 1.3rem; font-weight: 700; color: var(--accent); }
.dash-label { font-size: 0.75rem; color: var(--muted); }

/* Tabs */
.tabs { display: flex; gap: 0; border-bottom: 1px solid var(--border); }
.tab {
  padding: 10px 20px; border: none; background: none; cursor: pointer;
  font-size: 0.9rem; font-weight: 600; color: var(--muted);
  border-bottom: 2px solid transparent; transition: all 0.15s;
}
.tab:hover { color: var(--fg); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }

.tab-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.tab-header h3 { margin: 0; }
.tab-content { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; }

/* Detail Grid */
.detail-grid { display: flex; flex-direction: column; gap: 12px; }
.detail-item { display: flex; align-items: center; gap: 12px; }
.detail-label { font-size: 0.82rem; color: var(--muted); font-weight: 600; min-width: 80px; }
.detail-value { font-size: 0.9rem; }
.detail-desc { font-size: 0.88rem; line-height: 1.6; }

.badge-status, .milestone-status {
  font-size: 0.75rem; padding: 3px 10px; border-radius: 10px; font-weight: 600;
}
.status-pending { background: oklch(62% 0.18 55 / 0.12); color: #b45309; }
.status-in_progress { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.status-review { background: oklch(58% 0.16 280 / 0.1); color: var(--purple); }
.status-completed { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.status-canceled { background: var(--border); color: var(--muted); }
.status-partial { background: oklch(62% 0.18 55 / 0.12); color: #b45309; }
.status-received { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }

/* Revisions */
.revision-list { display: flex; flex-direction: column; gap: 10px; }
.revision-card {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 12px 16px;
}
.revision-desc { font-weight: 600; font-size: 0.9rem; }
.revision-meta { display: flex; gap: 8px; align-items: center; margin-top: 4px; }
.revision-by { font-size: 0.75rem; color: var(--purple); font-weight: 600; }
.revision-feedback { font-size: 0.78rem; color: var(--muted); font-style: italic; }
.revision-date { font-size: 0.75rem; color: var(--muted); }

/* Milestones */
.milestone-list { display: flex; flex-direction: column; gap: 10px; }
.milestone-card {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 12px 16px;
}
.milestone-name { font-weight: 700; font-size: 0.95rem; }
.milestone-meta { display: flex; gap: 8px; align-items: center; margin-top: 4px; }
.milestone-date { font-size: 0.78rem; color: var(--muted); }
.milestone-actions { display: flex; gap: 8px; }

/* Payments */
.payment-list { display: flex; flex-direction: column; gap: 10px; }
.payment-card {
  display: flex; align-items: center; justify-content: space-between;
  background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 12px 16px;
}
.payment-amount { font-weight: 700; font-size: 1.1rem; color: var(--accent); }
.payment-info-left { display: flex; align-items: center; gap: 12px; }
.payment-meta { display: flex; gap: 8px; align-items: center; }
.payment-actions { display: flex; gap: 8px; }
.payment-method, .payment-date { font-size: 0.78rem; color: var(--muted); }

/* Timeline */
.timeline-list { display: flex; flex-direction: column; gap: 12px; }
.timeline-event { display: flex; gap: 12px; }
.timeline-dot { width: 10px; height: 10px; border-radius: 50%; margin-top: 5px; flex-shrink: 0; }
.dot-milestone { background: #8b5cf6; }
.dot-payment { background: #16a34a; }
.dot-revision { background: #f59e0b; }
.timeline-content { flex: 1; }
.timeline-title { font-weight: 600; font-size: 0.9rem; }
.timeline-desc { font-size: 0.82rem; color: var(--muted); margin-top: 2px; }
.timeline-date { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }

/* Forms */
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input, .form-select, .form-textarea {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; max-width: 400px;
}
.form-textarea { resize: vertical; width: 100%; max-width: 100%; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:420px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:4px; }

.empty-state { text-align: center; padding: 40px; color: var(--muted); }
.loading-overlay { text-align: center; padding: 40px; color: var(--muted); }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; }
  .form-input, .form-select { max-width: 100%; width: 100%; }
}
</style>
