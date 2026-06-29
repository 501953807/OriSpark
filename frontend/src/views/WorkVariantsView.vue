<template>
  <div class="view-page">
    <div class="page-header">
      <div>
        <h1>作品变体分组</h1>
        <p class="page-sub">作品: {{ workId || '-' }}</p>
      </div>
      <button class="btn btn-primary btn-sm" @click="showCreateGroup = true">+ 新建分组</button>
    </div>

    <div v-if="loading" class="empty-hint">加载中...</div>
    <div v-else-if="groups.length === 0" class="empty-hint">暂无变体分组，点击"新建分组"创建</div>

    <div v-else class="groups-container">
      <div v-for="g in groups" :key="g.id" class="group-card">
        <div class="group-header">
          <div>
            <div class="group-name">{{ g.name }}</div>
            <div class="group-meta">{{ (g.variants || []).length }} 个变体 &middot; {{ formatDate(g.created_at) }}</div>
          </div>
          <div class="group-actions">
            <button class="btn btn-ghost btn-xs" @click="addGroupVariants(g)">+ 添加变体</button>
            <button class="btn btn-ghost btn-xs" @click="generateStandardVariants(g)">一键生成</button>
            <button class="btn btn-ghost btn-xs btn-danger-sm" @click="confirmDeleteGroup(g)">删除分组</button>
          </div>
        </div>

        <div class="variants-grid">
          <div v-for="v in g.variants" :key="v.id" class="variant-card">
            <div class="variant-name">{{ v.name || v.variant_name || '未命名' }}</div>
            <div class="variant-specs">
              <span v-if="v.aspect_ratio" class="spec-item">
                {{ v.aspect_ratio }}
              </span>
              <span v-if="v.width && v.height" class="spec-item">
                {{ v.width }} &times; {{ v.height }}
              </span>
              <span v-if="v.sort_order !== undefined" class="spec-item sort">
                #{{ v.sort_order }}
              </span>
            </div>
            <div class="variant-actions">
              <button class="btn btn-ghost btn-xs" @click="editVariant(g, v)">编辑</button>
              <button class="btn btn-ghost btn-xs btn-danger-sm" @click="removeVariant(g, v)">删除</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Group Modal -->
    <div v-if="showCreateGroup" class="modal-overlay" @click.self="showCreateGroup = false">
      <div class="modal-card animate-scale-in" style="max-width:420px">
        <div class="modal-header"><h3>新建分组</h3><button class="modal-close-btn" @click="showCreateGroup = false">&times;</button></div>
        <div class="form-group">
          <label>分组名称</label>
          <input v-model="groupForm.name" class="form-input" placeholder="社交媒体专用" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateGroup = false">取消</button>
          <button class="btn btn-primary" @click="createGroup" :disabled="saving">创建</button>
        </div>
      </div>
    </div>

    <!-- Variant Editor Modal -->
    <div v-if="showVariantEditor" class="modal-overlay" @click.self="showVariantEditor = false">
      <div class="modal-card animate-scale-in" style="max-width:440px">
        <div class="modal-header">
          <h3>{{ editingVariant ? '编辑变体' : '添加变体' }}</h3>
          <button class="modal-close-btn" @click="showVariantEditor = false">&times;</button>
        </div>
        <div class="form-group">
          <label>名称</label>
          <input v-model="variantForm.name" class="form-input" placeholder="正方形封面" />
        </div>
        <div class="form-group">
          <label>宽高比</label>
          <input v-model="variantForm.aspect_ratio" class="form-input" placeholder="1:1" />
        </div>
        <div class="form-row-2">
          <div class="form-group">
            <label>宽度</label>
            <input v-model.number="variantForm.width" type="number" class="form-input" placeholder="1080" />
          </div>
          <div class="form-group">
            <label>高度</label>
            <input v-model.number="variantForm.height" type="number" class="form-input" placeholder="1080" />
          </div>
        </div>
        <div class="form-group">
          <label>排序</label>
          <input v-model.number="variantForm.sort_order" type="number" class="form-input" placeholder="0" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showVariantEditor = false">取消</button>
          <button class="btn btn-primary" @click="saveVariant" :disabled="saving">保存</button>
        </div>
      </div>
    </div>

    <!-- Delete Group Confirmation -->
    <div v-if="deleteGroupTarget" class="modal-overlay" @click.self="deleteGroupTarget = null">
      <div class="modal-card animate-scale-in" style="max-width:400px">
        <div class="modal-header">
          <h3 style="color:#ef4444">确认删除</h3>
          <button class="modal-close-btn" @click="deleteGroupTarget = null">&times;</button>
        </div>
        <p style="color:var(--muted);font-size:0.9rem">确定要删除分组「{{ deleteGroupTarget?.name }}」吗？此操作不可撤销。</p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="deleteGroupTarget = null">取消</button>
          <button class="btn btn-danger" @click="doDeleteGroup" :disabled="deleting">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { systemApi } from '@/api/system'

interface WorkVariant {
  id: string
  name: string
  variant_name: string
  aspect_ratio: string
  width: number | null
  height: number | null
  sort_order: number
}

interface VariantGroup {
  id: string
  name: string
  work_id: string
  variants?: WorkVariant[]
  created_at: string
}

const route = useRoute()
const workId = ref(route.params.id as string || '')

const groups = ref<VariantGroup[]>([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)

const showCreateGroup = ref(false)
const showVariantEditor = ref(false)
const deleteGroupTarget = ref<VariantGroup | null>(null)

let currentGroupId = ''
let editingVariant: WorkVariant | null = null

const groupForm = ref({ name: '' })
const variantForm = ref({
  name: '', aspect_ratio: '', width: 0, height: 0, sort_order: 0,
})

function formatDate(d?: string): string {
  if (!d) return '-'
  return d.slice(0, 10)
}

async function loadGroups() {
  loading.value = true
  try {
    const res = await systemApi.variantGroups(workId.value)
    const items = res.data.data || []
    // Group variants by group
    const grouped: Record<string, VariantGroup> = {}
    for (const v of items) {
      const gid = v.group_id || v.id
      if (!grouped[gid]) {
        grouped[gid] = { id: gid, name: v.group_name || v.name || '未命名分组', work_id: v.work_id || workId.value, created_at: v.created_at || '', variants: [] }
      }
      if (v.variants) {
        grouped[gid].variants = v.variants
      } else if (v.id) {
        // Single variant
        grouped[gid].variants = grouped[gid].variants || []
        grouped[gid].variants.push({
          id: v.id, name: v.name || v.variant_name || '', variant_name: v.variant_name,
          aspect_ratio: v.aspect_ratio || '', width: v.width || null, height: v.height || null, sort_order: v.sort_order ?? 0,
        })
      }
    }
    groups.value = Object.values(grouped)
  } catch {
    // Mock data fallback
    groups.value = [
      {
        id: 'mock-g1', name: '标准比例', work_id: workId.value, created_at: '2026-05-01T00:00:00Z',
        variants: [
          { id: 'v1', name: '正方形', variant_name: '', aspect_ratio: '1:1', width: 1080, height: 1080, sort_order: 0 },
          { id: 'v2', name: '竖屏', variant_name: '', aspect_ratio: '9:16', width: 1080, height: 1920, sort_order: 1 },
          { id: 'v3', name: '横屏', variant_name: '', aspect_ratio: '16:9', width: 1920, height: 1080, sort_order: 2 },
        ],
      },
      {
        id: 'mock-g2', name: '社交媒体', work_id: workId.value, created_at: '2026-05-15T00:00:00Z',
        variants: [
          { id: 'v4', name: 'Instagram Feed', variant_name: '', aspect_ratio: '4:5', width: 1080, height: 1350, sort_order: 0 },
          { id: 'v5', name: 'Story', variant_name: '', aspect_ratio: '9:16', width: 1080, height: 1920, sort_order: 1 },
        ],
      },
    ]
  } finally {
    loading.value = false
  }
}

async function createGroup() {
  if (!groupForm.value.name.trim()) {
    ;(window as any).$toast?.show('请输入分组名称', 'error')
    return
  }
  saving.value = true
  try {
    const res = await systemApi.createVariantGroup({ name: groupForm.value.name, work_id: workId.value })
    const data = res.data.data
    if (data) groups.value.push(data)
    ;(window as any).$toast?.show('分组已创建', 'success')
    showCreateGroup.value = false
    groupForm.value = { name: '' }
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '创建失败', 'error')
  } finally {
    saving.value = false
  }
}

function addGroupVariants(g: VariantGroup) {
  currentGroupId = g.id
  editingVariant = null
  variantForm.value = { name: '', aspect_ratio: '', width: 0, height: 0, sort_order: 0 }
  showVariantEditor.value = true
}

function editVariant(g: VariantGroup, v: WorkVariant) {
  currentGroupId = g.id
  editingVariant = v
  variantForm.value = {
    name: v.name || '',
    aspect_ratio: v.aspect_ratio || '',
    width: v.width || 0,
    height: v.height || 0,
    sort_order: v.sort_order ?? 0,
  }
  showVariantEditor.value = true
}

async function saveVariant() {
  saving.value = true
  try {
    const data = {
      name: variantForm.value.name,
      aspect_ratio: variantForm.value.aspect_ratio || undefined,
      width: variantForm.value.width || undefined,
      height: variantForm.value.height || undefined,
      sort_order: variantForm.value.sort_order ?? 0,
    }
    if (editingVariant) {
      await systemApi.updateVariant(currentGroupId, editingVariant.id, data)
      ;(window as any).$toast?.show('变体已更新', 'success')
    } else {
      await systemApi.addVariant(currentGroupId, data)
      ;(window as any).$toast?.show('变体已添加', 'success')
    }
    showVariantEditor.value = false
    loadGroups()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '保存失败', 'error')
  } finally {
    saving.value = false
  }
}

async function removeVariant(g: VariantGroup, v: WorkVariant) {
  try {
    await systemApi.deleteVariant(g.id, v.id)
    ;(window as any).$toast?.show('变体已删除', 'success')
    loadGroups()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '删除失败', 'error')
  }
}

async function generateStandardVariants(g: VariantGroup) {
  try {
    await systemApi.generateVariants(workId.value, g.id)
    ;(window as any).$toast?.show('已生成 7 种标准比例的变体', 'success')
    loadGroups()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '生成失败', 'error')
  }
}

function confirmDeleteGroup(g: VariantGroup) {
  deleteGroupTarget.value = g
}

async function doDeleteGroup() {
  if (!deleteGroupTarget.value) return
  deleting.value = true
  try {
    await systemApi.deleteVariantGroup(deleteGroupTarget.value.id)
    ;(window as any).$toast?.show('分组已删除', 'success')
    deleteGroupTarget.value = null
    loadGroups()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '删除失败', 'error')
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  workId.value = (route.params.id as string) || workId.value
  loadGroups()
})
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.page-sub { color: var(--muted); font-size: 0.85rem; margin: 4px 0 0; }

.groups-container { display: flex; flex-direction: column; gap: 20px; }
.group-card {
  border: 1px solid var(--border); border-radius: var(--radius); padding: 20px;
}
.group-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.group-name { font-weight: 700; font-size: 1.05rem; }
.group-meta { font-size: 0.82rem; color: var(--muted); margin-top: 2px; }
.group-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.variants-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; margin-top: 16px; }
.variant-card {
  border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 12px;
  display: flex; flex-direction: column; gap: 6px;
}
.variant-name { font-weight: 600; font-size: 0.9rem; }
.variant-specs { display: flex; flex-wrap: wrap; gap: 6px; }
.spec-item { font-size: 0.75rem; color: var(--muted); background: var(--border); padding: 2px 8px; border-radius: 10px; }
.spec-item.sort { color: var(--accent); background: oklch(56% 0.12 170 / 0.08); }
.variant-actions { display: flex; gap: 4px; margin-top: 4px; }

.empty-hint { text-align: center; padding: 48px 24px; color: var(--muted); font-size: 0.9rem; }

.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.82rem; font-weight: 600; color: var(--muted); }
.form-input {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; max-width: 400px;
}
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.modal-overlay { position:fixed; inset:0; background:oklch(0 0 0 / .4); backdrop-filter:blur(4px); z-index:9998; display:flex; align-items:center; justify-content:center; }
.modal-card { background:var(--surface); border-radius:var(--radius-xl); padding:28px; max-width:560px; width:90%; box-shadow:0 16px 64px oklch(0 0 0 / .16); display:flex; flex-direction:column; gap:14px; max-height:90vh; overflow-y:auto; }
.modal-header { display:flex; align-items:center; justify-content:space-between; }
.modal-header h3 { margin:0; }
.modal-close-btn { background:none; border:none; cursor:pointer; font-size:1.4rem; color:var(--muted); }
.modal-footer { display:flex; justify-content:flex-end; gap:10px; margin-top:4px; }
.btn-danger { background:#e53e3e; color:#fff; }
.btn-danger:hover { background:#c53030; }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-xs { padding: 3px 10px; font-size: 0.78rem; }
.btn-ghost { background:transparent; color:var(--muted); }
.btn-ghost:hover { background:oklch(0 0 0 / 0.04); color:var(--fg); }
.btn-danger-sm { color: #ef4444; }

@media (max-width: 768px) {
  .form-input { max-width: 100%; width: 100%; }
  .form-row-2 { grid-template-columns: 1fr; }
  .variants-grid { grid-template-columns: 1fr 1fr; }
}
</style>
