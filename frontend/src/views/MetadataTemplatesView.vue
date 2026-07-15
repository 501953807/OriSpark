<template>
  <div class="view-page">
    <div class="page-header">
      <h1>元数据模板</h1>
      <button class="btn btn-primary btn-sm" @click="showCreateModal = true">+ 新建模板</button>
    </div>

    <div v-if="loading" class="empty-hint">加载中...</div>
    <div v-else-if="templates.length === 0" class="empty-hint">暂无模板，点击"新建模板"创建</div>

    <!-- Template Cards -->
    <div v-else class="template-grid">
      <div
        v-for="t in templates"
        :key="t.id"
        class="template-card"
        :class="{ expanded: expandedId === t.id }"
        @click="toggleExpand(t.id)"
      >
        <div class="card-header">
          <div class="card-title-row">
            <span class="card-title">{{ t.name }}</span>
            <span v-if="t.is_default" class="default-badge">默认</span>
          </div>
          <span class="field-count">{{ t.field_count || 0 }} 个字段</span>
        </div>
        <p v-if="t.description" class="card-desc">{{ t.description }}</p>
        <Transition name="slide-up">
          <div v-if="expandedId === t.id" class="expanded-body">
            <div v-if="fields.length === 0" class="empty-fields">暂无字段</div>
            <div v-else class="fields-list">
              <div v-for="f in fields" :key="f.id" class="field-item">
                <div class="field-drag-handle">&asymp;</div>
                <div class="field-details">
                  <span class="field-key">{{ f.key }}</span>
                  <span class="field-label">{{ f.label }}</span>
                  <span class="field-type">{{ fieldTypeLabel(f.field_type) }}</span>
                  <span v-if="f.required" class="required-star">*</span>
                </div>
                <div class="field-actions">
                  <button class="btn btn-ghost btn-xs" @click.stop="editField(f)">编辑</button>
                  <button class="btn btn-ghost btn-xs btn-danger-sm" @click.stop="removeField(f)">删除</button>
                </div>
              </div>
            </div>
            <div class="expanded-actions">
              <button class="btn btn-primary btn-sm" @click.stop="addFieldInline(t)">+ 添加字段</button>
              <button class="btn btn-secondary btn-sm" @click.stop="applyToWork(t)">应用到作品</button>
            </div>
          </div>
        </Transition>
      </div>
    </div>

    <!-- Create Template Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header"><h3>新建模板</h3><button class="modal-close-btn" @click="showCreateModal = false">&times;</button></div>
        <div class="form-group">
          <label>名称</label>
          <input v-model="createForm.name" class="form-input" placeholder="电商产品元数据" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <input v-model="createForm.description" class="form-input" placeholder="模板用途说明" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn btn-primary" @click="createTemplate" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- Field Editor Modal -->
    <div v-if="showFieldEditor" class="modal-overlay" @click.self="showFieldEditor = false">
      <div class="modal-card animate-scale-in" style="max-width:520px">
        <div class="modal-header">
          <h3>{{ editingField ? '编辑字段' : '添加字段' }}</h3>
          <button class="modal-close-btn" @click="showFieldEditor = false">&times;</button>
        </div>
        <div class="form-group">
          <label>字段键 (key)</label>
          <input v-model="fieldForm.key" class="form-input" placeholder="product_category" />
        </div>
        <div class="form-group">
          <label>标签 (label)</label>
          <input v-model="fieldForm.label" class="form-input" placeholder="产品分类" />
        </div>
        <div class="form-group">
          <label>类型</label>
          <select v-model="fieldForm.field_type" class="form-select">
            <option value="text">文本</option>
            <option value="number">数字</option>
            <option value="date">日期</option>
            <option value="select">单选</option>
            <option value="multiline">多行文本</option>
          </select>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="fieldForm.required" />
            必填
          </label>
        </div>
        <div class="form-group">
          <label>默认值</label>
          <input v-model="fieldForm.default_value" class="form-input" placeholder="可选" />
        </div>
        <div class="form-group">
          <label>选项 (多选时，每行一个选项)</label>
          <textarea v-model="fieldForm.options_str" class="form-textarea" rows="3" placeholder="选项1&#10;选项2&#10;选项3"></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showFieldEditor = false">取消</button>
          <button class="btn btn-primary" @click="saveField" :disabled="saving">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'

interface TemplateField {
  id: string
  template_id: string
  key: string
  label: string
  field_type: string
  required: boolean
  default_value: string | null
  options: string | null
  options_str: string
  sort_order: number
}

interface MetadataTemplate {
  id: string
  name: string
  description: string
  field_count: number
  is_default: boolean
  created_at: string
}

const templates = ref<MetadataTemplate[]>([])
const fields = ref<TemplateField[]>([])
const loading = ref(false)
const saving = ref(false)
const expandedId = ref<string | null>(null)

// Modals
const showCreateModal = ref(false)
const showFieldEditor = ref(false)
let currentTemplateId = ''

const createForm = ref({ name: '', description: '' })
const fieldForm = ref({
  key: '', label: '', field_type: 'text', required: false, default_value: '', options_str: '',
})
const editingField = ref<TemplateField | null>(null)

function fieldTypeLabel(t: string): string {
  const map: Record<string, string> = { text: '文本', number: '数字', date: '日期', select: '单选', multiline: '多行' }
  return map[t] || t
}

function toggleExpand(id: string) {
  if (expandedId.value === id) {
    expandedId.value = null
    fields.value = []
  } else {
    expandedId.value = id
    loadFields(id)
  }
}

async function loadTemplates() {
  loading.value = true
  try {
    const res = await systemApi.metadataTemplates()
    const items = res.data.data || []
    templates.value = items.map((t: any) => ({ ...t, field_count: t.field_count || 0 }))
  } catch {
    templates.value = [
      { id: 'mock-1', name: '电商产品', description: '适用于电商商品展示', field_count: 3, is_default: true, created_at: '2026-01-01T00:00:00Z' } as any,
      { id: 'mock-2', name: '摄影作品', description: '摄影作品元数据', field_count: 2, is_default: false, created_at: '2026-02-01T00:00:00Z' } as any,
    ]
  } finally {
    loading.value = false
  }
}

async function loadFields(templateId: string) {
  try {
    const res = await systemApi.templateFields(templateId)
    const items = res.data.data || []
    fields.value = items.map((f: any) => ({
      ...f,
      options_str: typeof f.options === 'string' ? f.options : Array.isArray(f.options) ? f.options.join('\n') : '',
    }))
  } catch {
    fields.value = templateId === 'mock-1'
      ? [
          { id: 'f1', template_id: templateId, key: 'category', label: '分类', field_type: 'select', required: true, default_value: null, options: '服装,数码', options_str: '服装\n数码', sort_order: 0 } as any,
          { id: 'f2', template_id: templateId, key: 'brand', label: '品牌', field_type: 'text', required: false, default_value: '', options: null, options_str: '', sort_order: 1 } as any,
          { id: 'f3', template_id: templateId, key: 'price', label: '价格', field_type: 'number', required: false, default_value: '0', options: null, options_str: '', sort_order: 2 } as any,
        ]
      : [
          { id: 'f1', template_id: templateId, key: 'camera', label: '相机型号', field_type: 'text', required: false, default_value: '', options: null, options_str: '', sort_order: 0 } as any,
          { id: 'f2', template_id: templateId, key: 'shoot_date', label: '拍摄日期', field_type: 'date', required: true, default_value: null, options: null, options_str: '', sort_order: 1 } as any,
        ]
  }
}

async function createTemplate() {
  if (!createForm.value.name.trim()) {
    ;(window as any).$toast?.show('请输入模板名称', 'error')
    return
  }
  saving.value = true
  try {
    await systemApi.createMetadataTemplate(createForm.value)
    ;(window as any).$toast?.show('模板已创建', 'success')
    createForm.value = { name: '', description: '' }
    showCreateModal.value = false
    loadTemplates()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '创建失败', 'error')
  } finally {
    saving.value = false
  }
}

function addFieldInline(t: MetadataTemplate) {
  currentTemplateId = t.id
  editingField.value = null
  fieldForm.value = { key: '', label: '', field_type: 'text', required: false, default_value: '', options_str: '' }
  showFieldEditor.value = true
}

function editField(f: TemplateField) {
  currentTemplateId = f.template_id
  editingField.value = f
  fieldForm.value = {
    key: f.key,
    label: f.label,
    field_type: f.field_type,
    required: f.required,
    default_value: f.default_value || '',
    options_str: f.options_str,
  }
  showFieldEditor.value = true
}

async function saveField() {
  if (!fieldForm.value.key.trim() || !fieldForm.value.label.trim()) {
    ;(window as any).$toast?.show('请填写字段键和标签', 'error')
    return
  }
  saving.value = true
  try {
    const options = fieldForm.value.field_type === 'select'
      ? fieldForm.value.options_str.split('\n').map((o: string) => o.trim()).filter(Boolean)
      : undefined
    const data = {
      key: fieldForm.value.key,
      label: fieldForm.value.label,
      field_type: fieldForm.value.field_type,
      required: fieldForm.value.required,
      default_value: fieldForm.value.default_value || null,
      ...(options !== undefined ? { options } : {}),
    }
    if (editingField.value) {
      await systemApi.updateTemplateField(currentTemplateId, editingField.value.id, data)
      ;(window as any).$toast?.show('字段已更新', 'success')
    } else {
      await systemApi.addTemplateField(currentTemplateId, data)
      ;(window as any).$toast?.show('字段已添加', 'success')
    }
    showFieldEditor.value = false
    loadFields(currentTemplateId)
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function removeField(f: TemplateField) {
  try {
    await systemApi.deleteTemplateField(currentTemplateId, f.id)
    ;(window as any).$toast?.show('字段已删除', 'success')
    loadFields(currentTemplateId)
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '删除失败', 'error')
  }
}

async function applyToWork(t: MetadataTemplate) {
  const workId = prompt('请输入作品 ID:')
  if (!workId) return
  try {
    await systemApi.applyTemplate(t.id, workId)
    ;(window as any).$toast?.show('模板已应用到作品', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '应用失败', 'error')
  }
}

onMounted(loadTemplates)
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }

.template-grid { display: flex; flex-direction: column; gap: 12px; }
.template-card {
  border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 20px;
  cursor: pointer; transition: all 0.2s;
}
.template-card:hover { box-shadow: 0 4px 16px oklch(0 0 0 / 0.05); border-color: var(--accent); }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.card-title-row { display: flex; align-items: center; gap: 8px; }
.card-title { font-weight: 700; font-size: 1rem; }
.default-badge {
  font-size: 0.72rem; padding: 2px 8px; border-radius: 10px; font-weight: 600;
  background: oklch(56% 0.12 170 / 0.12); color: #16a34a;
}
.field-count { font-size: 0.78rem; color: var(--muted); }
.card-desc { font-size: 0.84rem; color: var(--muted); margin: 6px 0 0; }
.expanded-body { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border); }
.fields-list { display: flex; flex-direction: column; gap: 6px; }
.field-item {
  display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  border: 1px solid var(--border); border-radius: var(--radius-sm); font-size: 0.84rem;
}
.field-drag-handle { color: var(--muted); font-size: 1.1rem; cursor: grab; user-select: none; }
.field-details { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; flex: 1; }
.field-key { font-family: monospace; font-size: 0.78rem; color: var(--accent); background: oklch(56% 0.12 170 / 0.08); padding: 1px 6px; border-radius: 4px; }
.field-label { font-weight: 600; }
.field-type { font-size: 0.75rem; color: var(--muted); }
.required-star { color: #ef4444; font-weight: 700; }
.field-actions { display: flex; gap: 4px; }
.expanded-actions { display: flex; gap: 8px; margin-top: 12px; }
.empty-fields { text-align: center; padding: 16px; color: var(--muted); font-size: 0.85rem; }

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input, .form-textarea, .form-select {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; max-width: 400px;
}
.form-textarea { resize: vertical; width: 100%; max-width: 100%; }
.form-select { width: 100%; max-width: 100%; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-weight: 400; font-size: 0.88rem; cursor: pointer; }
.checkbox-label input[type="checkbox"] { width: 16px; height: 16px; }

.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; max-height:90vh; overflow-y:auto; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:4px; }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-xs { padding: 3px 10px; font-size: 0.78rem; }
.btn-ghost { background:transparent; color:var(--muted); }
.btn-ghost:hover { background:oklch(0 0 0 / 0.04); color:var(--fg); }
.btn-danger-sm { color: #ef4444; }

.empty-hint { text-align: center; padding: 48px 24px; color: var(--muted); font-size: 0.9rem; }

@media (max-width: 768px) {
  .form-input, .form-textarea, .form-select { max-width: 100%; width: 100%; }
  .field-item { flex-wrap: wrap; }
}
</style>
