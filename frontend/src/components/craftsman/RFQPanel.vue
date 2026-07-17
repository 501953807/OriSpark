<template>
  <div class="rfq-panel">
    <!-- ── Header ──────────────────────────────────────────────── -->
    <div class="panel-header">
      <span class="panel-title">询价管理</span>
      <button class="btn btn-sm btn-primary" @click="toggleForm">
        <span>+</span> 新建询价
      </button>
    </div>

    <!-- ── Create Form ─────────────────────────────────────────── -->
    <div v-if="showForm" class="create-form">
      <div class="form-group">
        <label class="form-label" for="rfq-title">标题</label>
        <input
          id="rfq-title"
          v-model="form.title"
          class="form-input"
          placeholder="请输入询价标题"
          maxlength="120"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label class="form-label" for="rfq-quantity">需求数量</label>
          <input
            id="rfq-quantity"
            v-model.number="form.quantity_needed"
            type="number"
            class="form-input"
            placeholder="≥ 1"
            min="1"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="rfq-price">目标单价 (¥)</label>
          <input
            id="rfq-price"
            v-model.number="form.target_price"
            type="number"
            class="form-input"
            placeholder="可选"
            min="0"
            step="0.01"
          />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label" for="rfq-material">材质要求</label>
        <textarea
          id="rfq-material"
          v-model="form.material_note"
          class="form-textarea"
          rows="2"
          placeholder="描述材质、工艺等具体要求（可选）"
        ></textarea>
      </div>

      <div class="form-group" v-if="props.factories.length > 0">
        <label class="form-label" for="rfq-factory">关联工厂</label>
        <select
          id="rfq-factory"
          v-model="form.factory_id"
          class="form-select"
        >
          <option value="">-- 选择工厂（可选）--</option>
          <option
            v-for="f in props.factories"
            :key="f.id"
            :value="f.id"
          >
            {{ f.name }}
          </option>
        </select>
      </div>

      <div class="form-actions">
        <button class="btn btn-sm" @click="resetForm">取消</button>
        <button
          class="btn btn-sm btn-primary"
          :disabled="!formValid"
          @click="handleCreate"
        >
          提交询价
        </button>
      </div>
    </div>

    <!-- ── RFQ List ────────────────────────────────────────────── -->
    <div class="rfq-list">
      <div
        v-for="rfq in listItems"
        :key="rfq.id"
        class="rfq-item"
      >
        <div class="rfq-info">
          <div class="rfq-title">{{ rfq.title }}</div>
          <div class="rfq-meta">
            <span v-if="rfq.quantity_needed != null">需求: {{ rfq.quantity_needed }} 件</span>
            <span v-if="rfq.target_price != null" class="price-tag">
              ¥{{ rfq.target_price!.toFixed(2) }}/件
            </span>
            <span class="time-ago">{{ formatDate(rfq.created_at) }}</span>
          </div>
        </div>
        <div class="rfq-status">
          <span class="status-badge" :class="'status-' + rfq.status">
            {{ STATUS_MAP[rfq.status]?.label ?? rfq.status }}
          </span>
          <button
            class="btn btn-xs btn-ghost"
            @click="$emit('delete', rfq)"
            title="关闭询价"
          >&times;</button>
        </div>
      </div>

      <div v-if="listItems.length === 0" class="empty-state">
        <p>暂无询价单</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'
import type { RFQ, Factory } from '@/types/craftsman'

const STATUS_MAP: Record<string, { label: string }> = {
  open: { label: '开放中' },
  quoted: { label: '已报价' },
  awarded: { label: '已授标' },
  closed: { label: '已结束' },
}

const STATUS_ORDER: Array<keyof typeof STATUS_MAP> = ['open', 'quoted', 'awarded', 'closed']

const SORT_ORDER: Record<keyof typeof STATUS_MAP, number> = {
  open: 0,
  quoted: 1,
  awarded: 2,
  closed: 3,
}

interface Props {
  rfqs: RFQ[]
  factories?: Factory[]
}

const props = withDefaults(defineProps<Props>(), {
  factories: () => [],
})

const emit = defineEmits<{
  'rfq-created': [rfq: RFQ]
  delete: [rfq: RFQ]
}>()

const showForm = ref(false)

const defaultForm = (): {
  title: string
  quantity_needed: number | undefined
  target_price: number | undefined
  material_note: string
  factory_id: string
} => ({
  title: '',
  quantity_needed: undefined,
  target_price: undefined,
  material_note: '',
  factory_id: '',
})

const form = reactive(defaultForm())

function toggleForm() {
  showForm.value = !showForm.value
  if (showForm.value) resetForm()
}

function resetForm() {
  Object.assign(form, defaultForm())
  showForm.value = false
}

const formValid = computed(
  () => form.title.trim().length > 0 && (form.quantity_needed ?? 0) >= 1,
)

// ── Sorting: open first, then by date descending ──────────────────
const listItems = computed(() => {
  const items = [...props.rfqs]
  items.sort((a, b) => {
    const sa = SORT_ORDER[a.status] ?? 99
    const sb = SORT_ORDER[b.status] ?? 99
    if (sa !== sb) return sa - sb
    return (new Date(b.created_at ?? '').getTime() - new Date(a.created_at ?? '').getTime())
  })
  return items
})

async function handleCreate() {
  if (!formValid.value) return
  try {
    const created: RFQ = {
      id: crypto.randomUUID(),
      title: form.title.trim(),
      quantity_needed: form.quantity_needed,
      target_price: form.target_price,
      status: 'open',
      craft_product_id: '',
      created_at: new Date().toISOString(),
    }
    emit('rfq-created', created)
    ;(window as any).$toast?.show('询价单创建成功', 'success')
    resetForm()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建询价单失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

function formatDate(isoStr?: string): string {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return '今天'
    if (diffDays === 1) return '昨天'
    if (diffDays < 7) return `${diffDays} 天前`
    return d.toLocaleDateString('zh-CN')
  } catch {
    return isoStr.slice(0, 10)
  }
}
</script>

<style scoped>
/* ── Panel ──────────────────────────────────────────────────── */
.rfq-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--fg);
}

/* ── Create form ────────────────────────────────────────────── */
.create-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: fade-in 0.2s ease;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-input,
.form-textarea,
.form-select {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  background: var(--bg);
  color: var(--fg);
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--accent);
}

.form-textarea {
  resize: vertical;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* ── RFQ list ───────────────────────────────────────────────── */
.rfq-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rfq-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: border-color 0.2s;
}

.rfq-item:hover {
  border-color: var(--muted);
}

.rfq-info {
  flex: 1;
  min-width: 0;
}

.rfq-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rfq-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.76rem;
  color: var(--muted);
  margin-top: 4px;
}

.price-tag {
  color: var(--accent);
  font-weight: 600;
}

/* ── Status badges ──────────────────────────────────────────── */
.rfq-status {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  margin-left: 12px;
}

.status-badge {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 100px;
}

.status-open {
  background: oklch(56% 0.12 170 / 0.12);
  color: #059669;
}

.status-quoted {
  background: oklch(62% 0.16 260 / 0.1);
  color: var(--accent2);
}

.status-awarded {
  background: oklch(58% 0.14 245 / 0.12);
  color: var(--blue);
}

.status-closed {
  background: var(--border);
  color: var(--muted);
}

.btn-xs {
  padding: 2px 6px;
  font-size: 1rem;
  line-height: 1;
  background: transparent;
  border: none;
  color: var(--muted);
  cursor: pointer;
}

.btn-xs:hover {
  color: #ef4444;
}

/* ── Empty ──────────────────────────────────────────────────── */
.empty-state {
  text-align: center;
  padding: 32px;
  color: var(--muted);
  font-size: 0.88rem;
  background: var(--surface);
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border);
}

/* ── Buttons ────────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: background 0.2s;
  gap: 4px;
}

.btn:hover { background: var(--bg); }
.btn-sm { padding: 6px 12px; font-size: 0.8rem; }
.btn-ghost { border: none; background: transparent; color: var(--muted); }
.btn-ghost:hover { background: oklch(0 0 0 / 0.04); color: var(--fg); }

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover {
  background: oklch(50% 0.1 170);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
