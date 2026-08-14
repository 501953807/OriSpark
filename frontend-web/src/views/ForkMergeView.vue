<template>
  <div class="fork-merge-view">
    <!-- Error banner -->
    <div v-if="errorMsg" class="error-banner">
      <span>{{ errorMsg }}</span>
      <button @click="errorMsg = ''">关闭</button>
    </div>

    <div class="card">
      <div class="split-layout">
        <div class="work-list-panel">
          <div class="panel-header">
            <h3>我的仓库</h3>
            <button class="btn btn-sm btn-secondary" @click="showCreateModal = true">+ 新建</button>
          </div>
          <WorkList
            :works="works"
            :loading="loading"
            :selected-id="selectedWork?.id"
            @select="handleWorkSelect"
            @create="showCreateModal = true"
          />
        </div>
        <div v-if="selectedWork" class="work-detail-panel">
          <div class="detail-header">
            <h2>{{ selectedWork.title }}</h2>
            <span class="badge" :class="statusBadgeClass(selectedWork.status)">{{ statusLabel(selectedWork.status) }}</span>
          </div>
          <div class="tabs">
            <div class="tab-row">
              <button class="tab" :class="{ active: detailTab === 'branches' }" @click="detailTab = 'branches'">分支</button>
              <button class="tab" :class="{ active: detailTab === 'prs' }" @click="detailTab = 'prs'">合并请求</button>
              <button class="tab" :class="{ active: detailTab === 'collaborators' }" @click="detailTab = 'collaborators'">协作者</button>
            </div>
            <div class="tab-panel" v-if="detailTab === 'branches'">
              <BranchPanel :work-id="selectedWork.id" />
            </div>
            <div class="tab-panel" v-if="detailTab === 'prs'">
              <PullRequestCard :work-id="selectedWork.id" />
            </div>
            <div class="tab-panel" v-if="detailTab === 'collaborators'">
              <CollaboratorList :work-id="selectedWork.id" />
            </div>
          </div>
        </div>
        <EmptyState
          v-else
          icon="🔀"
          title="选择或创建一个仓库"
          description="Fork-Merge 支持 Git-style 的协同创作工作流。"
        />
      </div>
    </div>

    <!-- Create work modal -->
    <div class="modal-overlay" v-if="showCreateModal">
      <div class="modal-card">
        <h3 style="margin: 0 0 16px">新建协同仓库</h3>
        <div class="form-group">
          <label class="form-label">原始作品ID</label>
          <input class="form-input" v-model="createForm.original_work_id" placeholder="输入原始作品 ID" />
        </div>
        <div class="form-group">
          <label class="form-label">标题</label>
          <input class="form-input" v-model="createForm.title" placeholder="仓库标题" />
        </div>
        <div class="form-group">
          <label class="form-label">可见性</label>
          <select class="form-select" v-model="createForm.visibility">
            <option v-for="opt in visibilityOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
          <button class="btn btn-primary" :disabled="creating" @click="handleCreate">{{ creating ? '创建中...' : '创建' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { ForkMergeWork } from '@/types/forkMerge'
import { forkMergeApi } from '@/api/forkMerge'
import WorkList from '@/components/forkmerge/WorkList.vue'
import BranchPanel from '@/components/forkmerge/BranchPanel.vue'
import PullRequestCard from '@/components/forkmerge/PullRequestCard.vue'
import CollaboratorList from '@/components/forkmerge/CollaboratorList.vue'
import EmptyState from '@/components/common/EmptyState.vue'

// ── State ──────────────────────────────────────────────────────
const works = ref<ForkMergeWork[]>([])
const loading = ref(false)
const selectedWork = ref<ForkMergeWork | null>(null)
const errorMsg = ref('')
const showCreateModal = ref(false)
const creating = ref(false)
const detailTab = ref('branches')

const createForm = reactive({
  original_work_id: '',
  title: '',
  visibility: 'private' as string,
})

const visibilityOptions = [
  { label: '私有', value: 'private' },
  { label: '公开', value: 'public' },
]

// ── Helpers ────────────────────────────────────────────────────
function statusBadgeClass(status: string): string {
  const map: Record<string, string> = {
    active: 'badge-success',
    closed: 'badge-default',
    archived: 'badge-info',
  }
  return map[status] || 'badge-default'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    active: '进行中',
    closed: '已关闭',
    archived: '已归档',
  }
  return map[status] || status
}

// ── Actions ────────────────────────────────────────────────────
async function loadWorks() {
  loading.value = true
  try {
    const resp = await forkMergeApi.listWorks()
    works.value = resp.data.data || []
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : '加载仓库列表失败'
  } finally {
    loading.value = false
  }
}

function handleWorkSelect(work: ForkMergeWork) {
  selectedWork.value = work
}

async function handleCreate() {
  if (!createForm.original_work_id.trim()) {
    alert('请输入原始作品 ID')
    return
  }
  creating.value = true
  try {
    const result = await forkMergeApi.createWork(createForm)
    works.value.unshift(result.data.data)
    selectedWork.value = result.data.data
    showCreateModal.value = false
    Object.assign(createForm, { original_work_id: '', title: '', visibility: 'private' })
    alert('仓库创建成功')
  } catch (e: unknown) {
    alert(e instanceof Error ? e.message : '创建失败')
  } finally {
    creating.value = false
  }
}

// ── Mount ──────────────────────────────────────────────────────
loadWorks()
</script>

<style scoped>
.fork-merge-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--m-grey-500);
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: oklch(65% 0.18 20);
  color: #fff;
  border-radius: var(--m-radius-sm);
  font-size: 0.88rem;
}

.error-banner button {
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 1.1rem;
  opacity: 0.8;
}

.split-layout { display: flex; min-height: 400px; }
.work-list-panel { flex: 0 0 30%; padding: 8px; overflow-y: auto; border-right: 1px solid var(--m-border); max-height: calc(100vh - 200px); }
.work-detail-panel { flex: 1; padding: 16px; }

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.panel-header h3 {
  margin: 0;
  font-size: 0.92rem;
  font-weight: 600;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-header h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

/* Tabs */
.tabs { display: flex; flex-direction: column; }
.tab-row { display: flex; gap: 0; border-bottom: 1px solid var(--m-border); margin-bottom: 12px; }
.tab {
  padding: 8px 16px; border: none; background: none; cursor: pointer;
  font-size: 0.88rem; color: var(--m-grey-500); border-bottom: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
}
.tab:hover { color: var(--m-on-surface); }
.tab.active { color: rgb(140, 87, 255); border-bottom-color: rgb(140, 87, 255); }
.tab-panel { padding: 0; }
</style>
