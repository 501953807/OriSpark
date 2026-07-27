<template>
  <div v-if="activeTab === 'registrations'" class="registrations animate-fade-in">
    <div class="actions-bar">
      <div class="filter-group">
        <select :value="filterType" class="form-input" @change="$emit('update:filterType', ($event.target as HTMLSelectElement).value); $emit('load-records')">
          <option value="">全部类型</option>
          <option value="copyright">著作权</option>
          <option value="trademark">商标</option>
          <option value="design_patent">外观设计</option>
          <option value="utility_patent">专利</option>
        </select>
        <select :value="filterStatus" class="form-input" @change="$emit('update:filterStatus', ($event.target as HTMLSelectElement).value); $emit('load-records')">
          <option value="">全部状态</option>
          <option v-for="(label, key) in statusLabels" :key="key" :value="key">{{ label }}</option>
        </select>
      </div>
      <button class="btn btn-primary" @click="$emit('open-add-modal')">+ 新登记记录</button>
    </div>
    <EmptyState v-if="!records.length" icon="📋" title="暂无登记记录" description="手动添加版权/商标/专利申请记录以追踪进度" />
    <div v-else class="records-list">
      <div v-for="r in records" :key="r.id" class="record-row card">
        <div class="record-header">
          <div class="record-title">
            <span class="record-type">{{ typeLabels[r.ip_type] || r.ip_type }}</span>
            <span class="record-jurisdiction">{{ jurisdictionLabels[r.jurisdiction] || r.jurisdiction }}</span>
            <StatusBadge :status="r.status" :labels="statusLabels" :variants="statusVariants" />
          </div>
        </div>
        <div class="record-body">
          <div class="record-field"><label>申请号</label><span>{{ r.application_no || '—' }}</span></div>
          <div class="record-field"><label>注册号</label><span>{{ r.registration_no || '—' }}</span></div>
          <div class="record-field"><label>申请日期</label><span>{{ r.filing_date || '—' }}</span></div>
          <div class="record-field"><label>到期日</label><span>{{ r.expiration_date || '—' }}</span></div>
          <div class="record-field"><label>官费</label><span>{{ r.total_cost ? '¥' + r.total_cost : (r.official_fee ? '¥' + r.official_fee : '—') }}</span></div>
          <div class="record-field"><label>备注</label><span>{{ r.notes || '—' }}</span></div>
        </div>
        <div class="record-footer">
          <button class="btn btn-secondary btn-sm" @click="$emit('view-record-detail', r)">详情</button>
          <button v-if="canWithdraw(r)" class="btn btn-warning btn-sm" @click="$emit('withdraw-record', r.id)">撤回</button>
          <button v-if="canSupplement(r)" class="btn btn-info btn-sm" @click="$emit('open-supplement', r)">补材料</button>
          <button class="btn btn-secondary btn-sm" @click="$emit('edit-record', r)">编辑</button>
          <button class="btn btn-danger btn-sm" @click="$emit('delete-record', r.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const props = defineProps<{
  activeTab: string
  records: any[]
  showAddModal: boolean
  editingRecord: any
  form: any
  filterType: string
  filterStatus: string
  typeLabels: Record<string, string>
  jurisdictionLabels: Record<string, string>
  statusLabels: Record<string, string>
  statusVariants: Record<string, string>
}>()

defineEmits<{
  'update:showAddModal': [show: boolean]
  'update:editingRecord': [rec: any]
  'update:form': [form: any]
  'update:filterType': [type: string]
  'update:filterStatus': [status: string]
  'load-records': []
  'open-add-modal': []
  'edit-record': [record: any]
  'save-record': []
  'delete-record': [id: string]
  'view-record-detail': [record: any]
  'withdraw-record': [id: string]
  'open-supplement': [record: any]
  'submit-supplement': []
}>()

function canWithdraw(r: any): boolean {
  return ['draft', 'filed', 'under_review'].includes(r.status)
}

function canSupplement(r: any): boolean {
  return ['under_review', 'rejected'].includes(r.status)
}
</script>

<style scoped>
/* ── Registrations ───────────────────────────── */
.registrations { display:flex; flex-direction:column; gap:16px; }
.actions-bar { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.filter-group { display:flex; gap:8px; }
.filter-group .form-input { width:120px; padding:8px 12px; }
.records-list { display:flex; flex-direction:column; gap:12px; }
.record-row { padding:16px 20px; }
.record-header { margin-bottom:12px; }
.record-title { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.record-type { font-weight:700; font-size:.88rem; }
.record-jurisdiction { font-size:.75rem; color:var(--muted); padding:2px 8px; background:var(--surface); border:1px solid var(--border); border-radius:100px; }
.record-body { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }
.record-field label { font-size:.72rem; color:var(--muted); font-weight:600; display:block; }
.record-field span { font-size:.85rem; }
.record-footer { margin-top:12px; display:flex; justify-content:flex-end; gap:8px; }
</style>
