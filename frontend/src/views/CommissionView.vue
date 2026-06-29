<template>
  <div class="view-page">
    <div class="page-header">
      <h1>委托管理</h1>
      <button class="btn btn-primary btn-sm" @click="showNewModal = true; editingCommission = null; resetCommissionForm()">+ 新建委托</button>
    </div>

    <div class="kanban-board">
      <div
        v-for="col in columns"
        :key="col.key"
        class="kanban-column"
        :class="{ 'drag-over': colDragOver === col.key }"
        @dragover="onDragOver($event, col.key)"
        @dragleave="colDragOver = null"
        @drop="onDrop($event, col.key)"
      >
        <div class="column-header">
          <span class="column-title">{{ col.label }}</span>
          <span class="column-count">{{ getColumnItems(col.key).length }}</span>
        </div>

        <div class="column-items">
          <div
            v-for="item in getColumnItems(col.key)"
            :key="item.id"
            class="kanban-card"
            draggable="true"
            @dragstart="onDragStart($event, item)"
            @click="viewDetail(item)"
          >
            <div class="card-priority" :class="'priority-' + (item.priority || 'normal')"></div>
            <div class="card-title">{{ item.client_name || item.title || '未命名' }}</div>
            <div v-if="item.work_title" class="card-work">{{ item.work_title }}</div>
            <div class="card-meta">
              <span class="card-amount">{{ item.currency === 'CNY' ? '¥' : '$' }}{{ item.amount }}</span>
              <span v-if="item.due_date" class="card-due">截止: {{ item.due_date }}</span>
            </div>
            <div v-if="item.description" class="card-desc">{{ item.description }}</div>
          </div>
        </div>
      </div>
    </div>

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
          <input v-model="commissionForm.work_title" class="form-input" placeholder="相关作品" />
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
          <label>状态</label>
          <select v-model="commissionForm.status" class="form-select">
            <option v-for="c in columns" :key="c.key" :value="c.key">{{ c.label }}</option>
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
            <span class="detail-value">{{ selectedCommission.client_name }}</span>
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
              <span class="badge-status" :class="'status-' + (selectedCommission.status || 'pending')">{{ statusLabel(selectedCommission.status) }}</span>
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
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'

interface Commission {
  id: string
  client_name: string
  title: string
  work_title: string
  amount: number
  currency: string
  status: string
  due_date: string
  priority: string
  description: string
}

const columns = [
  { key: 'pending', label: '待接单' },
  { key: 'in_progress', label: '进行中' },
  { key: 'review', label: '待审核' },
  { key: 'completed', label: '已完成' },
  { key: 'canceled', label: '已取消' },
]

const commissions = ref<Commission[]>([])
const loading = ref(false)
const saving = ref(false)
const colDragOver = ref<string | null>(null)
const draggedItem = ref<Commission | null>(null)

const showNewModal = ref(false)
const editingCommission = ref<Commission | null>(null)
const selectedCommission = ref<Commission | null>(null)

const commissionForm = ref({
  client_name: '', work_title: '', amount: 0, currency: 'CNY',
  status: 'pending', due_date: '', priority: 'normal', description: '',
})

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '待接单', in_progress: '进行中', review: '待审核',
    completed: '已完成', canceled: '已取消',
  }
  return map[s] || s
}

function priorityLabel(p?: string): string {
  const map: Record<string, string> = { high: '高', urgent: '紧急', normal: '普通' }
  return map[p || 'normal'] || '普通'
}

function getColumnItems(status: string): Commission[] {
  return commissions.value.filter((c) => c.status === status)
}

function resetCommissionForm() {
  commissionForm.value = {
    client_name: '', work_title: '', amount: 0, currency: 'CNY',
    status: 'pending', due_date: '', priority: 'normal', description: '',
  }
}

function viewDetail(item: Commission) {
  selectedCommission.value = item
}

function editFromDetail() {
  if (!selectedCommission.value) return
  editingCommission.value = selectedCommission.value
  commissionForm.value = {
    client_name: selectedCommission.value.client_name,
    work_title: selectedCommission.value.work_title,
    amount: selectedCommission.value.amount,
    currency: selectedCommission.value.currency,
    status: selectedCommission.value.status,
    due_date: selectedCommission.value.due_date,
    priority: selectedCommission.value.priority,
    description: selectedCommission.value.description,
  }
  selectedCommission.value = null
  showNewModal.value = true
}

function onDragStart(e: DragEvent, item: Commission) {
  draggedItem.value = item
  e.dataTransfer!.effectAllowed = 'move'
}

function onDragOver(e: DragEvent, status: string) {
  e.preventDefault()
  e.dataTransfer!.dropEffect = 'move'
  colDragOver.value = status
}

async function onDrop(e: DragEvent, targetStatus: string) {
  e.preventDefault()
  colDragOver.value = null
  if (!draggedItem.value) return
  try {
    await systemApi.updateCommission(draggedItem.value.id, { status: targetStatus })
    const idx = commissions.value.findIndex((c) => c.id === draggedItem.value!.id)
    if (idx >= 0) commissions.value[idx].status = targetStatus
    ;(window as any).$toast?.show(`已移至「${statusLabel(targetStatus)}」`, 'success')
  } catch (err: any) {
    const detail = err.response?.data?.detail
    if (detail && typeof detail === 'string' && detail.startsWith('http')) {
      // URL-based error from API -- still show toast
      ;(window as any).$toast?.show(detail.substring(0, 80), 'error')
    } else {
      ;(window as any).$toast?.show('移动失败', 'error')
    }
  }
  draggedItem.value = null
}

async function saveCommission() {
  if (!commissionForm.value.client_name.trim()) {
    ;(window as any).$toast?.show('请输入客户名称', 'error')
    return
  }
  saving.value = true
  try {
    const data = { ...commissionForm.value }
    if (editingCommission.value) {
      await systemApi.updateCommission(editingCommission.value.id, data)
      ;(window as any).$toast?.show('委托已更新', 'success')
    } else {
      const res = await systemApi.createCommission(data)
      const created = res.data.data
      if (created) commissions.value.unshift(created)
      else {
        commissions.value.unshift({
          ...data,
          id: 'new-' + Date.now(),
          title: '',
        } as Commission)
      }
      ;(window as any).$toast?.show('委托已创建', 'success')
    }
    showNewModal.value = false
    editingCommission.value = null
    resetCommissionForm()
  } catch (e: any) {
    const msg = e.response?.data?.detail || '保存失败'
    ;(window as any).$toast?.show(typeof msg === 'string' ? msg : String(msg), 'error')
  } finally {
    saving.value = false
  }
}

function loadMockData() {
  commissions.value = [
    { id: 'c1', client_name: '张三', title: '', work_title: '婚礼摄影', amount: 5000, currency: 'CNY', status: 'pending', due_date: '2026-07-15', priority: 'normal', description: '婚礼全程跟拍，交付精修照片200张' },
    { id: 'c2', client_name: 'XX 科技公司', title: '', work_title: '产品宣传照', amount: 12000, currency: 'CNY', status: 'in_progress', due_date: '2026-06-30', priority: 'high', description: '新产品发布会宣传素材拍摄' },
    { id: 'c3', client_name: '李四', title: '', work_title: '旅行游记', amount: 3000, currency: 'CNY', status: 'review', due_date: '2026-07-01', priority: 'normal', description: '' },
    { id: 'c4', client_name: '王五', title: '', work_title: '人像写真', amount: 2000, currency: 'CNY', status: 'completed', due_date: '2026-06-01', priority: 'normal', description: '' },
    { id: 'c5', client_name: 'A 品牌方', title: '', work_title: '品牌手册', amount: 28000, currency: 'CNY', status: 'in_progress', due_date: '2026-08-01', priority: 'urgent', description: '年度品牌形象手册拍摄及后期' },
    { id: 'c6', client_name: '赵六', title: '', work_title: '家庭合影', amount: 1500, currency: 'CNY', status: 'canceled', due_date: '2026-06-20', priority: 'normal', description: '客户临时取消' },
  ] as Commission[]
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await systemApi.commissions()
    const items = res.data.data || []
    commissions.value = items.map((c: any) => ({
      ...c,
      title: c.title || c.work_title || '',
    }))
  } catch {
    loadMockData()
  }
  loading.value = false
})
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 16px; }

.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }

/* Kanban Board */
.kanban-board { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 12px; min-height: 500px; }
.kanban-column {
  flex: 0 0 240px; min-width: 200px;
  background: oklch(98% 0.003 240);
  border: 1px solid var(--border); border-radius: var(--radius);
  display: flex; flex-direction: column;
  transition: border-color 0.2s, background 0.2s;
}
.kanban-column.drag-over {
  border-color: var(--accent);
  background: oklch(56% 0.12 170 / 0.04);
}
.column-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; border-bottom: 1px solid var(--border);
}
.column-title { font-weight: 700; font-size: 0.9rem; }
.column-count {
  font-size: 0.75rem; background: var(--border); color: var(--muted);
  padding: 1px 8px; border-radius: 10px; font-weight: 600;
}
.column-items {
  flex: 1; padding: 10px; display: flex; flex-direction: column; gap: 10px;
  overflow-y: auto;
}

/* Kanban Cards */
.kanban-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 12px; cursor: grab; transition: all 0.15s;
  border-left: 3px solid transparent;
}
.kanban-card:hover { box-shadow: 0 2px 10px oklch(0 0 0 / 0.06); transform: translateY(-1px); }
.kanban-card:active { cursor: grabbing; }
.card-priority { width: 8px; height: 8px; border-radius: 50%; margin-bottom: 8px; }
.priority-normal { background: var(--border); }
.priority-high { background: #f59e0b; }
.priority-urgent { background: #ef4444; }
.card-title { font-weight: 700; font-size: 0.9rem; margin-bottom: 4px; }
.card-work { font-size: 0.8rem; color: var(--muted); margin-bottom: 8px; }
.card-meta { display: flex; align-items: center; justify-content: space-between; }
.card-amount { font-weight: 700; font-size: 0.95rem; color: var(--accent); }
.card-due { font-size: 0.75rem; color: var(--muted); }
.card-desc { font-size: 0.8rem; color: var(--muted); margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border); }

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
.status-pending { background: oklch(62% 0.18 55 / 0.12); color: #b45309; }
.status-in_progress { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.status-review { background: oklch(58% 0.16 280 / 0.1); color: var(--purple); }
.status-completed { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.status-canceled { background: var(--border); color: var(--muted); }
.priority-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 6px; }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }

@media (max-width: 768px) {
  .kanban-board { flex-direction: column; }
  .kanban-column { flex: none; width: 100%; min-height: 200px; }
  .form-input, .form-textarea, .form-select { max-width: 100%; width: 100%; }
  .form-row-2 { grid-template-columns: 1fr; }
}
</style>
