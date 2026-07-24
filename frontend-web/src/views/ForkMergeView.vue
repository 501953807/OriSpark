<template>
  <div class="fork-merge-view">
    <!-- Error banner -->
    <div v-if="errorMsg" class="error-banner">
      <span>{{ errorMsg }}</span>
      <button @click="errorMsg = ''">关闭</button>
    </div>

    <n-card title="🔀 Fork-Merge 协同创作">
      <n-split direction="horizontal" :default-size="0.3" :min="0.2" :max="0.5">
        <template #1>
          <div class="work-list-panel">
            <div class="panel-header">
              <h3>我的仓库</h3>
              <n-button size="small" @click="showCreateModal = true">+ 新建</n-button>
            </div>
            <WorkList
              :works="works"
              :loading="loading"
              :selected-id="selectedWork?.id"
              @select="handleWorkSelect"
              @create="showCreateModal = true"
            />
          </div>
        </template>
        <template #2>
          <div v-if="selectedWork" class="work-detail-panel">
            <div class="detail-header">
              <h2>{{ selectedWork.title }}</h2>
              <n-tag :type="statusTagType(selectedWork.status)">{{ statusLabel(selectedWork.status) }}</n-tag>
            </div>
            <n-tabs type="segment">
              <n-tab-pane name="branches" tab="分支">
                <BranchPanel :work-id="selectedWork.id" />
              </n-tab-pane>
              <n-tab-pane name="prs" tab="合并请求">
                <PullRequestCard :work-id="selectedWork.id" />
              </n-tab-pane>
              <n-tab-pane name="collaborators" tab="协作者">
                <CollaboratorList :work-id="selectedWork.id" />
              </n-tab-pane>
            </n-tabs>
          </div>
          <EmptyState
            v-else
            icon="🔀"
            title="选择或创建一个仓库"
            description="Fork-Merge 支持 Git-style 的协同创作工作流。"
          />
        </template>
      </n-split>
    </n-card>

    <!-- Create work modal -->
    <n-modal v-model:show="showCreateModal" preset="dialog" title="新建协同仓库">
      <n-form ref="formRef" :model="createForm" label-placement="left" label-width="80">
        <n-form-item label="原始作品ID" path="original_work_id">
          <n-input v-model:value="createForm.original_work_id" placeholder="输入原始作品 ID" />
        </n-form-item>
        <n-form-item label="标题" path="title">
          <n-input v-model:value="createForm.title" placeholder="仓库标题" />
        </n-form-item>
        <n-form-item label="可见性" path="visibility">
          <n-select v-model:value="createForm.visibility" :options="visibilityOptions" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreateModal = false">取消</n-button>
        <n-button type="primary" :loading="creating" @click="handleCreate">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { NButton, NSplit, NTabs, NTabPane, NTag, NModal, NForm, NFormItem, NInput, NSelect, useMessage } from 'naive-ui'
import type { FormInst } from 'naive-ui'
import type { ForkMergeWork } from '@/types/forkMerge'
import { forkMergeApi } from '@/api/forkMerge'
import WorkList from '@/components/forkmerge/WorkList.vue'
import BranchPanel from '@/components/forkmerge/BranchPanel.vue'
import PullRequestCard from '@/components/forkmerge/PullRequestCard.vue'
import CollaboratorList from '@/components/forkmerge/CollaboratorList.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const message = useMessage()

// ── State ──────────────────────────────────────────────────────
const works = ref<ForkMergeWork[]>([])
const loading = ref(false)
const selectedWork = ref<ForkMergeWork | null>(null)
const errorMsg = ref('')
const showCreateModal = ref(false)
const creating = ref(false)
const formRef = ref<FormInst | null>(null)

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
function statusTagType(status: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  const map: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
    active: 'success',
    closed: 'default',
    archived: 'info',
  }
  return map[status] || 'default'
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
    message.error('请输入原始作品 ID')
    return
  }
  creating.value = true
  try {
    const result = await forkMergeApi.createWork(createForm)
    works.value.unshift(result.data.data)
    selectedWork.value = result.data.data
    showCreateModal.value = false
    Object.assign(createForm, { original_work_id: '', title: '', visibility: 'private' })
    message.success('仓库创建成功')
  } catch (e: unknown) {
    message.error(e instanceof Error ? e.message : '创建失败')
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
  color: var(--muted);
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: oklch(65% 0.18 20);
  color: #fff;
  border-radius: var(--radius);
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

.work-list-panel {
  padding: 8px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

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

.work-detail-panel {
  padding: 16px;
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
</style>
