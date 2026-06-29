<template>
  <div class="view-page">
    <div class="page-header">
      <h1>水印预设</h1>
      <button class="btn btn-primary btn-sm" @click="showCreateModal = true">+ 新建预设</button>
    </div>

    <!-- Loading / Empty -->
    <div v-if="loading" class="empty-hint">加载中...</div>
    <div v-else-if="presets.length === 0" class="empty-hint">暂无水印预设，点击"新建预设"创建</div>

    <!-- Table -->
    <div v-else class="table-wrapper card">
      <table class="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>类型</th>
            <th>默认</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in presets" :key="p.id">
            <td>
              <div class="preset-name">{{ p.name }}</div>
              <div v-if="p.description" class="preset-desc">{{ p.description }}</div>
            </td>
            <td>
              <span class="type-badge" :class="'type-' + (p.watermark_type || 'text')">
                {{ typeLabel(p.watermark_type) }}
              </span>
            </td>
            <td>
              <span v-if="p.is_default" class="default-badge">默认</span>
              <span v-else class="default-badge not-default">-</span>
            </td>
            <td class="time-col">{{ formatDate(p.created_at) }}</td>
            <td class="actions-col">
              <button class="btn btn-ghost btn-xs" @click="previewPreset(p)" title="预览">预览</button>
              <button class="btn btn-ghost btn-xs" @click="editPreset(p)" title="编辑">编辑</button>
              <button class="btn btn-ghost btn-xs btn-danger-sm" @click="confirmDelete(p)" title="删除">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit Modal -->
    <div v-if="showCreateModal || showEditModal" class="modal-overlay" @click.self="closeModals">
      <div class="modal-card animate-scale-in">
        <div class="modal-header">
          <h3>{{ showEditModal ? '编辑预设' : '新建预设' }}</h3>
          <button class="modal-close-btn" @click="closeModals">&times;</button>
        </div>
        <div class="form-group">
          <label>名称</label>
          <input v-model="form.name" class="form-input" placeholder="我的水印" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <input v-model="form.description" class="form-input" placeholder="预设描述" />
        </div>
        <div class="form-group">
          <label>水印类型</label>
          <select v-model="form.watermark_type" class="form-select">
            <option value="text">文字</option>
            <option value="image">图片</option>
            <option value="tiled">平铺</option>
          </select>
        </div>
        <div class="form-group">
          <label>配置 (JSON)</label>
          <textarea v-model="form.config_str" class="form-textarea" rows="4" placeholder='{"opacity": 0.5}'></textarea>
        </div>
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="form.is_default" />
            设为默认
          </label>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModals">取消</button>
          <button class="btn btn-primary" @click="savePreset" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Preview Modal -->
    <div v-if="showPreviewModal" class="modal-overlay" @click.self="showPreviewModal = false">
      <div class="modal-card animate-scale-in" style="max-width:520px">
        <div class="modal-header">
          <h3>水印预览</h3>
          <button class="modal-close-btn" @click="showPreviewModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>选择图片</label>
          <input v-model="previewImagePath" class="form-input" placeholder="/path/to/image.jpg" />
        </div>
        <div class="preview-result" v-if="previewImage">
          <img :src="previewImage" alt="preview" class="preview-img" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showPreviewModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- Apply to Work Modal -->
    <div v-if="showApplyModal" class="modal-overlay" @click.self="showApplyModal = false">
      <div class="modal-card animate-scale-in" style="max-width:420px">
        <div class="modal-header">
          <h3>应用到作品</h3>
          <button class="modal-close-btn" @click="showApplyModal = false">&times;</button>
        </div>
        <div class="form-group">
          <label>选择作品</label>
          <select v-model="applyWorkId" class="form-select">
            <option value="">-- 选择作品 --</option>
            <option v-for="w in works" :key="w.id" :value="w.id">{{ w.title }}</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showApplyModal = false">取消</button>
          <button class="btn btn-primary" @click="applyToWork" :disabled="applying">
            {{ applying ? '处理中...' : '应用水印' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal-card animate-scale-in" style="max-width:400px">
        <div class="modal-header">
          <h3 style="color:#ef4444">确认删除</h3>
          <button class="modal-close-btn" @click="deleteTarget = null">&times;</button>
        </div>
        <p style="color:var(--muted);font-size:0.9rem">确定要删除预设「{{ deleteTarget?.name }}」吗？此操作不可撤销。</p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="deleteTarget = null">取消</button>
          <button class="btn btn-danger" @click="doDelete" :disabled="deleting">
            {{ deleting ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { systemApi } from '@/api/system'
import client from '@/api/client'

interface WatermarkPreset {
  id: string
  name: string
  description: string
  watermark_type: string
  config: Record<string, unknown>
  config_str: string
  is_default: boolean
  created_at: string
}

const presets = ref<WatermarkPreset[]>([])
const loading = ref(false)
const saving = ref(false)
const applying = ref(false)
const deleting = ref(false)

// Modals
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showPreviewModal = ref(false)
const showApplyModal = ref(false)
const deleteTarget = ref<WatermarkPreset | null>(null)
const editingPreset = ref<WatermarkPreset | null>(null)

// Form
const form = ref({
  name: '',
  description: '',
  watermark_type: 'text',
  config_str: '{}',
  is_default: false,
})

// Preview
const previewImagePath = ref('/sample/photo.jpg')
const previewImage = ref('')

// Apply
const applyWorkId = ref('')
const works = ref<Array<{ id: string; title: string }>>([
  { id: '1', title: '示例作品 - 自然风光' },
  { id: '2', title: '示例作品 - 人像摄影' },
  { id: '3', title: '示例作品 - 商业产品' },
])

function typeLabel(t: string): string {
  const map: Record<string, string> = { text: '文字', image: '图片', tiled: '平铺' }
  return map[t] || t
}

function formatDate(d?: string): string {
  if (!d) return '-'
  return d.slice(0, 10)
}

async function loadPresets() {
  loading.value = true
  try {
    const res = await systemApi.watermarkPresets()
    const items = res.data.data || []
    presets.value = items.map((p: any) => ({
      ...p,
      config_str: typeof p.config === 'string' ? p.config : JSON.stringify(p.config || {}, null, 2),
    }))
  } catch {
    presets.value = [
      { id: 'mock-1', name: '默认文字水印', description: '透明度 50% 的文字水印', watermark_type: 'text', config: { text: '© OriStudio' }, config_str: '{"text":"&copy; OriStudio"}', is_default: true, created_at: '2026-01-15T10:00:00Z' },
      { id: 'mock-2', name: 'Logo 角标', description: '右下角半透明 Logo', watermark_type: 'image', config: { position: 'bottom-right' }, config_str: '{"position":"bottom-right"}', is_default: false, created_at: '2026-02-01T14:00:00Z' },
    ]
  } finally {
    loading.value = false
  }
}

function resetForm() {
  form.value = { name: '', description: '', watermark_type: 'text', config_str: '{}', is_default: false }
  editingPreset.value = null
}

function closeModals() {
  showCreateModal.value = false
  showEditModal.value = false
  resetForm()
}

function editPreset(p: WatermarkPreset) {
  editingPreset.value = p
  form.value = {
    name: p.name,
    description: p.description || '',
    watermark_type: p.watermark_type || 'text',
    config_str: p.config_str || '{}',
    is_default: p.is_default,
  }
  showEditModal.value = true
}

async function savePreset() {
  if (!form.value.name.trim()) {
    ;(window as any).$toast?.show('请输入预设名称', 'error')
    return
  }
  saving.value = true
  try {
    const data = {
      name: form.value.name,
      description: form.value.description,
      watermark_type: form.value.watermark_type,
      config: form.value.config_str,
      is_default: form.value.is_default,
    }
    if (showEditModal.value && editingPreset.value) {
      await systemApi.updateWatermarkPreset(editingPreset.value.id, data)
      ;(window as any).$toast?.show('预设已更新', 'success')
    } else {
      await systemApi.createWatermarkPreset(data)
      ;(window as any).$toast?.show('预设已创建', 'success')
    }
    closeModals()
    loadPresets()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

function previewPreset(p: WatermarkPreset) {
  previewImage.value = ''
  showPreviewModal.value = true
  try {
    const config = typeof p.config === 'string' ? JSON.parse(p.config) : p.config
    systemApi.previewWatermark(config || {}, previewImagePath.value).then((res) => {
      if (res.data.data?.preview_url) {
        previewImage.value = res.data.data.preview_url
      }
    }).catch(() => {
      previewImage.value = ''
    })
  } catch {
    previewImage.value = ''
  }
}

function applyPreset(p: WatermarkPreset) {
  applyWorkId.value = ''
  showApplyModal.value = true
}

async function applyToWork() {
  if (!applyWorkId.value) {
    ;(window as any).$toast?.show('请选择作品', 'error')
    return
  }
  applying.value = true
  try {
    await systemApi.applyWatermark(applyWorkId.value, editingPreset.value?.id || '')
    ;(window as any).$toast?.show('水印已应用到作品', 'success')
    showApplyModal.value = false
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '应用失败', 'error')
  } finally {
    applying.value = false
  }
}

function confirmDelete(p: WatermarkPreset) {
  deleteTarget.value = p
}

async function doDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  try {
    await systemApi.deleteWatermarkPreset(deleteTarget.value.id)
    ;(window as any).$toast?.show('预设已删除', 'success')
    deleteTarget.value = null
    loadPresets()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '删除失败', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(loadPresets)
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.table-wrapper { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.data-table th {
  text-align: left; padding: 10px 14px; border-bottom: 2px solid var(--border);
  font-weight: 600; color: var(--muted); font-size: 0.8rem;
}
.data-table td { padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }
.data-table tbody tr:hover { background: oklch(0 0 0 / 0.015); }
.preset-name { font-weight: 600; }
.preset-desc { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }
.type-badge {
  font-size: 0.75rem; padding: 2px 10px; border-radius: 12px; font-weight: 600;
}
.type-text { background: oklch(56% 0.12 170 / 0.1); color: #16a34a; }
.type-image { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.type-tiled { background: oklch(62% 0.16 280 / 0.1); color: var(--purple); }
.default-badge {
  font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; font-weight: 600;
}
.default-badge:not(.not-default) { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.not-default { background: var(--border); color: var(--muted); }
.time-col { color: var(--muted); font-size: 0.82rem; white-space: nowrap; }
.actions-col { display: flex; gap: 4px; white-space: nowrap; }
.btn-xs { padding: 3px 10px; font-size: 0.78rem; }
.btn-danger-sm { color: #ef4444; }
.empty-hint { text-align: center; padding: 48px 24px; color: var(--muted); font-size: 0.9rem; }

/* Form elements (scoped copies from SettingsView) */
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

/* Modal */
.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; max-height:90vh; overflow-y:auto; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:4px; }
.btn-danger { background:#e53e3e; color:#fff; }
.btn-danger:hover { background:#c53030; }

/* Preview */
.preview-result { text-align:center; padding:12px 0; }
.preview-img { max-width:100%; max-height:280px; border-radius:var(--radius-sm); border:1px solid var(--border); }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-ghost { background:transparent; color:var(--muted); }
.btn-ghost:hover { background:oklch(0 0 0 / 0.04); color:var(--fg); }

@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; }
  .form-input, .form-textarea, .form-select { max-width: 100%; width: 100%; }
  .data-table { font-size: 0.8rem; }
  .data-table th, .data-table td { padding: 8px 10px; }
}
</style>
