<template>
  <div class="versions-view">
    <div class="page-header">
      <router-link to="/app/works" class="btn btn-ghost btn-sm">← 返回作品列表</router-link>
      <h2>{{ work?.title || '版本历史' }}</h2>
    </div>

    <LoadingSpinner v-if="loading" />

    <EmptyState v-else-if="!work" icon="⚠️" title="作品不存在" description="请检查作品ID是否正确" />

    <div v-else class="versions-content">
      <div class="work-info-card">
        <div class="work-info-left">
          <div class="work-title">{{ work.title }}</div>
          <div class="work-meta">
            <span>{{ work.file_type }} / {{ work.file_extension?.toUpperCase() }}</span>
            <span>{{ formatFileSize(work.file_size) }}</span>
            <span v-if="work.sha256" class="mono hash">{{ work.sha256.slice(0, 16) }}…</span>
          </div>
        </div>
        <button class="btn btn-primary" @click="showCreate = true" :disabled="creating">
          {{ creating ? '创建中…' : '+ 创建新版本' }}
        </button>
      </div>

      <!-- Timeline -->
      <div v-if="versions.length === 0" class="empty-state">
        <div class="empty-icon">📸</div>
        <div class="empty-text">暂无版本记录</div>
        <div class="empty-hint">创建新版本以开始追踪作品演进历史</div>
        <button class="btn btn-primary btn-sm" @click="showCreate = true">+ 创建第一个版本</button>
      </div>

      <div v-else class="timeline">
        <div
          v-for="(v, index) in versions"
          :key="v.id"
          class="timeline-item"
          :class="{ 'is-current': v.version_num === latestVersionNum }"
        >
          <div class="timeline-node">
            <div class="node-dot" :class="{ 'is-current': v.version_num === latestVersionNum }"></div>
            <div v-if="index < versions.length - 1" class="node-line"></div>
          </div>
          <div class="timeline-card card">
            <div class="timeline-header">
              <span class="version-badge" :class="{ 'is-current': v.version_num === latestVersionNum }">
                v{{ v.version_num }}
              </span>
              <span class="timeline-date">{{ formatDate(v.created_at) }}</span>
              <div class="timeline-actions">
                <button
                  v-if="v.version_num !== latestVersionNum"
                  class="btn btn-ghost btn-xs"
                  @click="rollbackTo(v.id)"
                >↩ 回滚</button>
                <button
                  v-if="versions.length > 1"
                  class="btn btn-ghost btn-xs btn-danger"
                  @click="deleteVersion(v)"
                >🗑️</button>
              </div>
            </div>
            <div class="timeline-hash">
              <code>{{ v.file_hash?.slice(0, 12) || '—' }}</code>
              <span class="hash-size">{{ formatFileSize(v.file_size) }}</span>
            </div>
            <div v-if="v.notes" class="timeline-notes">{{ v.notes }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Version Modal -->
    <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
      <div class="modal-card" style="max-width:420px">
        <div class="modal-header">
          <h3>创建新版本</h3>
          <button class="modal-close-btn" @click="showCreate = false">×</button>
        </div>
        <div class="form-group">
          <label>备注（可选）</label>
          <textarea
            v-model="versionNotes"
            class="form-textarea"
            rows="3"
            placeholder="描述本次版本的变更内容…"
          ></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="createVersion" :disabled="creating">
            {{ creating ? '创建中…' : '创建' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div v-if="deletingVersion" class="modal-overlay" @click.self="deletingVersion = null">
      <div class="modal-card" style="max-width:380px">
        <div class="modal-header">
          <h3>删除版本</h3>
          <button class="modal-close-btn" @click="confirmDelete = false">×</button>
        </div>
        <p>确定要删除 <strong>v{{ deletingVersion?.version_num }}</strong> 吗？此操作不可撤销。</p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="confirmDelete = false">取消</button>
          <button class="btn btn-danger" @click="confirmDeleteVersion" :disabled="deleting">
            {{ deleting ? '删除中…' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import { worksApi } from '@/api/works'
import type { Work } from '@/types/work'

const route = useRoute()
const workId = route.params.id as string

const work = ref<Work | null>(null)
const versions = ref<any[]>([])
const loading = ref(true)
const showCreate = ref(false)
const versionNotes = ref('')
const creating = ref(false)
const deleting = ref(false)
const deletingVersion = ref<any>(null)
const confirmDelete = ref(false)

const latestVersionNum = computed(() => {
  if (!versions.value.length) return 0
  return Math.max(...versions.value.map((v: any) => v.version_num))
})

async function loadVersions() {
  loading.value = true
  try {
    const [workRes, verRes] = await Promise.all([
      worksApi.get(workId),
      worksApi.listVersions(workId),
    ])
    work.value = workRes.data.data
    versions.value = verRes.data.data || []
  } catch {
    work.value = null
    versions.value = []
  } finally {
    loading.value = false
  }
}

async function createVersion() {
  if (!work.value) return
  creating.value = true
  try {
    await worksApi.createVersion(work.value.id, versionNotes.value || undefined)
    showCreate.value = false
    versionNotes.value = ''
    await loadVersions()
    ;(window as any).$toast?.show('版本已创建', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建版本失败'
    ;(window as any).$toast?.show(msg, 'error')
  } finally {
    creating.value = false
  }
}

function deleteVersion(v: any) {
  deletingVersion.value = v
  confirmDelete.value = false
}

async function confirmDeleteVersion() {
  if (!deletingVersion.value || !work.value) return
  deleting.value = true
  try {
    await worksApi.deleteVersion(work.value.id, deletingVersion.value.id)
    deletingVersion.value = null
    await loadVersions()
    ;(window as any).$toast?.show('版本已删除', 'info')
  } catch (e: unknown) {
    const detail = (e as any)?.response?.data?.detail || '删除失败'
    ;(window as any).$toast?.show(detail, 'error')
    deletingVersion.value = null
  } finally {
    deleting.value = false
  }
}

async function rollbackTo(versionId: string) {
  if (!work.value) return
  if (!confirm('回滚到此版本将更新作品的哈希值，确定继续？')) return
  try {
    await worksApi.rollback(work.value.id, versionId)
    await loadVersions()
    ;(window as any).$toast?.show('已回滚到历史版本', 'success')
  } catch {
    ;(window as any).$toast?.show('回滚失败', 'error')
  }
}

function formatFileSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}

function formatDate(iso: string | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' }) +
    ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

onMounted(() => loadVersions())
</script>

<style scoped>
.versions-view { display: flex; flex-direction: column; gap: 20px; }
.page-header { display: flex; align-items: center; gap: 12px; }
.page-header h2 { margin: 0; font-size: 1.1rem; }
.work-info-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px;
}
.work-info-left { display: flex; flex-direction: column; gap: 4px; }
.work-title { font-weight: 700; font-size: 1rem; }
.work-meta { display: flex; gap: 12px; font-size: .8rem; color: var(--muted); }
.work-meta .mono { font-family: var(--font-mono); font-size: .75rem; color: var(--accent); }
.empty-state { display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 60px 20px; color: var(--muted); }
.empty-icon { font-size: 3rem; }
.empty-text { font-size: 1rem; font-weight: 600; color: var(--fg); }
.empty-hint { font-size: .85rem; }

/* Timeline */
.timeline { position: relative; padding-left: 40px; display: flex; flex-direction: column; gap: 0; }
.timeline-item { position: relative; padding-bottom: 20px; }
.timeline-node {
  position: absolute; left: -40px; top: 0; bottom: 0; width: 40px;
  display: flex; flex-direction: column; align-items: center;
}
.node-dot {
  width: 14px; height: 14px; border-radius: 50%;
  background: var(--border); border: 2px solid var(--surface);
  flex-shrink: 0; z-index: 1;
}
.node-dot.is-current { background: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / .2); }
.node-line { flex: 1; width: 2px; background: var(--border); margin-top: 4px; }
.timeline-card { padding: 14px 16px; }
.timeline-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.version-badge {
  display: inline-flex; align-items: center; padding: 2px 10px;
  border-radius: 20px; font-size: .75rem; font-weight: 700;
  background: oklch(56% 0.12 170 / .1); color: var(--accent);
}
.version-badge.is-current { background: oklch(56% 0.12 170 / .2); color: var(--accent); }
.timeline-date { font-size: .78rem; color: var(--muted); }
.timeline-actions { margin-left: auto; display: flex; gap: 4px; }
.timeline-hash { display: flex; align-items: center; gap: 8px; font-size: .8rem; }
.timeline-hash code { font-family: var(--font-mono); color: var(--accent); }
.hash-size { font-size: .75rem; color: var(--muted); }
.timeline-notes { margin-top: 8px; font-size: .85rem; color: var(--fg); padding: 8px 12px; background: oklch(0 0 0 / .03); border-radius: var(--radius-sm); }
.btn-danger { color: #ef4444; }
.btn-danger:hover { background: oklch(70% 0.2 20) !important; }
.btn-xs { padding: 3px 8px; font-size: .72rem; }
.btn-sm { padding: 6px 14px; font-size: .82rem; }
</style>
