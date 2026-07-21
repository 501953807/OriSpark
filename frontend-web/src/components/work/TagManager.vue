<template>
  <div class="tag-manager card">
    <div class="card-header-row">
      <h3>🏷️ 标签</h3>
      <button class="btn btn-ghost btn-sm" @click="showGlobal = true">全局管理</button>
    </div>

    <!-- Compact tag pills -->
    <div class="tag-list">
      <div v-if="workTags.length === 0" class="card-empty">暂无标签</div>
      <div v-for="t in workTags" :key="t.id" class="tag-pill-compact">
        <span class="tag-name">{{ t.tag }}</span>
        <button class="tag-remove-xs" @click="removeTag(t)" title="删除">×</button>
      </div>
    </div>

    <!-- Global tag management modal -->
    <div v-if="showGlobal" class="modal-overlay" @click.self="showGlobal = false">
      <div class="modal-card modal-lg">
        <div class="modal-header">
          <h3>全局标签管理</h3>
          <button class="modal-close-btn" @click="showGlobal = false">×</button>
        </div>
        <div v-if="globalTags.length === 0" class="card-empty">暂无标签</div>
        <div v-else class="global-tag-list">
          <div v-for="tg in globalTags" :key="tg.id" class="global-tag-row">
            <span class="gt-name">{{ tg.tag }}</span>
            <span class="gt-count">{{ tg.work_count }} 个作品</span>
            <div class="gt-actions">
              <button @click="renameTag(tg)" title="重命名">✏️</button>
              <button @click="deleteTag(tg)" title="删除">🗑️</button>
              <button @click="viewWorksByTag(tg.tag)" title="查看作品">📄</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Rename modal -->
    <div v-if="showRename" class="modal-overlay" @click.self="showRename = false">
      <div class="modal-card">
        <h3>重命名标签</h3>
        <input v-model="renameValue" class="form-input" placeholder="新标签名" @keydown.enter="confirmRename" />
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showRename = false">取消</button>
          <button class="btn btn-primary" @click="confirmRename">保存</button>
        </div>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
      <div class="modal-card">
        <h3>确认删除标签</h3>
        <p>标签 "{{ pendingTag?.tag }}" 将从所有作品中移除。此操作不可恢复。</p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDeleteConfirm = false">取消</button>
          <button class="btn btn-danger" @click="confirmDelete">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { worksApi } from '@/api/works'
import type { WorkTag } from '@/types/work'

const props = defineProps<{
  workId: string
  workTags: WorkTag[]
}>()

const emit = defineEmits<{
  tagsUpdated: []
}>()

const router = useRouter()
const showGlobal = ref(false)
const showRename = ref(false)
const showDeleteConfirm = ref(false)
const renameValue = ref('')
const renameTarget = ref<{ id: string; tag: string } | null>(null)
const pendingTag = ref<{ id: string; tag: string } | null>(null)
const globalTags = ref<any[]>([])

async function loadGlobalTags() {
  try {
    const res = await worksApi.listTags()
    globalTags.value = res.data.data || []
  } catch {
    globalTags.value = []
  }
}

async function removeTag(tag: WorkTag) {
  try {
    await worksApi.removeTag(props.workId, tag.id)
    emit('tagsUpdated')
  } catch {
    ;(window as any).$toast?.show('删除标签失败', 'error')
  }
}

function renameTag(tg: any) {
  renameTarget.value = { id: tg.id, tag: tg.tag }
  renameValue.value = tg.tag
  showRename.value = true
}

async function confirmRename() {
  if (!renameTarget.value || !renameValue.value.trim()) return
  try {
    await worksApi.renameTag(renameTarget.value.tag, renameValue.value.trim())
    showRename.value = false
    loadGlobalTags()
    emit('tagsUpdated')
    ;(window as any).$toast?.show('标签已重命名', 'success')
  } catch {
    ;(window as any).$toast?.show('重命名失败', 'error')
  }
}

function deleteTag(tg: any) {
  pendingTag.value = { id: tg.id, tag: tg.tag }
  showDeleteConfirm.value = true
}

async function confirmDelete() {
  if (!pendingTag.value) return
  try {
    await worksApi.deleteTag(pendingTag.value.tag)
    showDeleteConfirm.value = false
    loadGlobalTags()
    emit('tagsUpdated')
    ;(window as any).$toast?.show('标签已删除', 'info')
  } catch {
    ;(window as any).$toast?.show('删除失败', 'error')
  }
}

function viewWorksByTag(tagName: string) {
  showGlobal.value = false
  router.push({ path: '/app/works', query: { tag: tagName } })
}

onMounted(() => { loadGlobalTags() })
</script>

<style scoped>
.tag-manager { padding: 16px 20px; }
.tag-manager h3 { margin: 0; font-size: 0.88rem; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-header-row h3 { margin: 0; font-size: 0.88rem; }

/* Compact tag pills — no input, no add button */
.tag-list { display: flex; gap: 6px; flex-wrap: wrap; }
.tag-pill-compact {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 3px 8px;
  border-radius: 100px;
  font-size: 0.75rem;
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--accent);
  font-weight: 600;
}
.tag-name { }
.tag-remove-xs {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  color: var(--muted);
  padding: 0;
  line-height: 1;
  opacity: 0.6;
  transition: opacity 0.15s;
}
.tag-remove-xs:hover { opacity: 1; color: #e53e3e; }

.card-empty { font-size: 0.78rem; color: var(--muted); padding: 8px 0; }

/* Global tag modal */
.global-tag-list { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
.global-tag-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  background: oklch(96% 0.003 240);
}
.gt-name { flex: 1; font-weight: 600; }
.gt-count { color: var(--muted); font-size: 0.72rem; }
.gt-actions { display: flex; gap: 4px; }
.gt-actions button {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 2px 4px;
  opacity: 0.6;
  transition: opacity 0.15s;
}
.gt-actions button:hover { opacity: 1; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 16px; }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-header h3 { margin: 0; }
.modal-close-btn { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: var(--muted); }
.modal-lg { max-width: 480px; }
.form-input {
  padding: 9px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none; width: 100%;
}
</style>
