<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-card animate-scale-in">
        <div class="panel-header">
          <h3>批量编辑 ({{ workIds.length }} 个作品)</h3>
          <button class="close-btn" @click="$emit('close')">&times;</button>
        </div>

        <div class="panel-body">
          <!-- Tags -->
          <div class="section-label">标签</div>
          <div class="form-group">
            <label>添加标签（逗号分隔，追加到现有标签）</label>
            <input
              v-model="tagAdd"
              class="form-input"
              placeholder="风景, 数字艺术"
            />
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="tagReplace" />
              替换为所选标签（不清除现有标签）
            </label>
          </div>
          <div class="form-group">
            <label>从已有标签中选择（追加到新增标签）</label>
            <TagInput v-model="tagSelectedItems" />
          </div>

          <!-- Status -->
          <div class="section-label">状态</div>
          <div class="form-group">
            <label>作品状态</label>
            <select v-model="formStatus" class="form-input">
              <option :value="''">保持原样</option>
              <option value="active">active（活跃）</option>
              <option value="trashed">trashed（回收站）</option>
              <option value="archived">archived（归档）</option>
            </select>
          </div>

          <!-- Category / Creator Type -->
          <div class="section-label">分类</div>
          <div class="form-group">
            <label>创作者类型（creator_type）</label>
            <select v-model="formCreatorType" class="form-input">
              <option :value="''">保持原样</option>
              <option value="illustrator">插画师</option>
              <option value="photographer">摄影师</option>
              <option value="video">视频创作者</option>
              <option value="craftsman">手工艺人</option>
              <option value="musician">音乐人</option>
              <option value="writer">作家</option>
            </select>
          </div>
          <div class="form-group">
            <label>体裁（genre，写入 custom_metadata）</label>
            <input
              v-model="formGenre"
              class="form-input"
              placeholder="小说 / 散文 / 诗歌…"
            />
          </div>

          <!-- Title Prefix -->
          <div class="section-label">批量重命名</div>
          <div class="form-group">
            <label>标题前缀</label>
            <input
              v-model="titlePrefix"
              class="form-input"
              placeholder="可选：在标题最前面加上这段文字"
            />
          </div>
          <div class="form-group">
            <label>标题后缀</label>
            <input
              v-model="titleSuffix"
              class="form-input"
              placeholder="可选：在标题最后面加上这段文字"
            />
          </div>
        </div>

        <div class="panel-footer">
          <button class="btn btn-secondary" @click="$emit('close')">取消</button>
          <button
            class="btn btn-primary"
            :disabled="executing"
            @click="handleBatchEdit"
          >
            {{ executing ? '处理中…' : '执行批量编辑' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, defineModel } from 'vue'
import TagInput from './TagInput.vue'
import type { WorkTag } from '@/types/work'

const props = defineProps<{
  visible: boolean
  workIds: string[]
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const tagSelectedItems = ref<WorkTag[]>([])

const tagAdd = ref('')
const tagReplace = ref(true)

const formStatus = ref('')
const formCreatorType = ref('')
const formGenre = ref('')

const titlePrefix = ref('')
const titleSuffix = ref('')

const executing = ref(false)

watch(() => props.visible, (v) => {
  if (v) {
    tagSelectedItems.value = []
    tagAdd.value = ''
    tagReplace.value = true
    formStatus.value = ''
    formCreatorType.value = ''
    formGenre.value = ''
    titlePrefix.value = ''
    titleSuffix.value = ''
    executing.value = false
  }
})

function buildUpdates(): Record<string, unknown> {
  const updates: Record<string, unknown> = {}

  // Status
  if (formStatus.value) {
    updates.status = formStatus.value
  }

  // Creator type
  if (formCreatorType.value) {
    updates.creator_type = formCreatorType.value
  }

  // Genre (into custom_metadata)
  if (formGenre.value) {
    updates._genre = formGenre.value
  }

  // Title prefix / suffix
  if (titlePrefix.value || titleSuffix.value) {
    updates._title_prefix = titlePrefix.value
    updates._title_suffix = titleSuffix.value
  }

  // Tags: merge into a single comma-delimited string
  if (tagAdd.value || tagSelectedItems.value.length > 0) {
    const addTags = tagAdd.value.split(',').map(s => s.trim()).filter(Boolean)
    const selectedLabels = tagSelectedItems.value.map(t => t.tag)
    const merged = tagReplace.value
      ? addTags.concat(selectedLabels)
      : addTags.concat(selectedLabels)
    updates._tags_add = merged.join(',')
    updates._tags_replace = tagReplace.value
  }

  return updates
}

async function handleBatchEdit() {
  const updates = buildUpdates()
  if (Object.keys(updates).length === 0) {
    ;(window as any).$toast?.show('请至少选择一个编辑选项', 'warning')
    return
  }

  executing.value = true
  try {
    // Send via the same worksApi.batchEdit but with our computed payload shape
    const api = (await import('@/api/works')).worksApi
    await api.batchEdit(props.workIds, updates)
    ;(window as any).$toast?.show(
      `已将 ${props.workIds.length} 个作品批量编辑完成`,
      'success',
    )
    emit('saved')
    emit('close')
  } catch (e) {
    console.error('Batch edit failed:', e)
    ;(window as any).$toast?.show('批量编辑失败', 'error')
  } finally {
    executing.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0; background: oklch(0 0 0 / 0.4);
  backdrop-filter: blur(4px); z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.modal-card {
  background: var(--surface); border-radius: var(--radius-xl);
  padding: 0; width: 480px; max-width: 90vw; max-height: 85vh;
  box-shadow: 0 16px 64px oklch(0 0 0 / 0.16);
  display: flex; flex-direction: column; overflow: hidden;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.panel-header h3 { margin: 0; font-size: 1.1rem; }
.close-btn { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: var(--muted); }
.panel-body {
  flex: 1; padding: 20px; overflow-y: auto;
  display: flex; flex-direction: column; gap: 14px;
}
.panel-footer {
  padding: 14px 20px; border-top: 1px solid var(--border);
  display: flex; justify-content: flex-end; gap: 10px; flex-shrink: 0;
}
.section-label {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--accent);
  padding-top: 4px; border-top: 1px solid var(--border);
}
.section-label:first-child { border-top: none; padding-top: 0; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 0.8rem; font-weight: 600; color: var(--muted); }
.form-input {
  padding: 9px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none;
}
.form-input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1); }
.btn { padding: 9px 18px; border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; font-family: var(--font-body); }
.btn-primary { background: var(--accent); color: #fff; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background: var(--surface); color: var(--fg); border: 1px solid var(--border); }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; cursor: pointer; font-weight: 400; color: var(--fg); }
@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.animate-scale-in { animation: scaleIn 0.15s ease; }
</style>
