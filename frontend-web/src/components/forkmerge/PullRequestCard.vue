<template>
  <div class="pr-panel">
    <div class="panel-header">
      <span>合并请求</span>
      <n-button size="small" @click="showCreatePR = true">+ 新建 MR</n-button>
    </div>

    <div v-if="prs.length === 0" class="empty-state">暂无合并请求</div>

    <div v-else class="pr-list">
      <div v-for="pr in prs" :key="pr.id" class="pr-item">
        <div class="pr-title">{{ pr.title }}</div>
        <div class="pr-meta">
          <n-tag size="small" :type="prStatusType(pr.status)">
            {{ prStatusLabel(pr.status) }}
          </n-tag>
          <span v-if="pr.source_branch_id" class="pr-branches">
            → {{ pr.target_branch_id ? `分支 ${pr.source_branch_id} → ${pr.target_branch_id}` : '分支' }}
          </span>
          <span class="pr-time">{{ formatDate(pr.created_at) }}</span>
        </div>
        <div v-if="pr.description" class="pr-desc">{{ pr.description.slice(0, 100) }}</div>
        <div class="pr-actions" v-if="pr.status === 'open'">
          <n-button size="tiny" type="success" @click="$emit('merge', pr.id)">合并</n-button>
          <n-button size="tiny" type="error" @click="$emit('reject', pr.id)">拒绝</n-button>
        </div>
      </div>
    </div>

    <!-- Create PR modal -->
    <n-modal v-model:show="showCreatePR" preset="dialog" title="新建合并请求">
      <n-form :model="prForm" label-width="80">
        <n-form-item label="标题">
          <n-input v-model:value="prForm.title" placeholder="MR 标题" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="prForm.description" type="textarea" placeholder="简要说明变更内容" />
        </n-form-item>
        <n-form-item label="源分支">
          <n-select v-model:value="prForm.source_branch_id" :options="branchOptions" />
        </n-form-item>
        <n-form-item label="目标分支">
          <n-select v-model:value="prForm.target_branch_id" :options="branchOptions" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreatePR = false">取消</n-button>
        <n-button type="primary" @click="handleCreate">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NButton, NModal, NForm, NFormItem, NInput, NSelect, NTag } from 'naive-ui'
import { forkMergeApi } from '@/api/forkMerge'
import type { PullRequest, Branch } from '@/types/forkMerge'

const props = defineProps<{ workId: string }>()
const emit = defineEmits<{ merge: [prId: string]; reject: [prId: string] }>()

const prs = ref<PullRequest[]>([])
const branches = ref<Branch[]>([])
const showCreatePR = ref(false)
const prForm = ref({ title: '', description: '', source_branch_id: '', target_branch_id: '' })

const branchOptions = computed(() =>
  branches.value.map(b => ({ label: b.name, value: b.id }))
)

async function loadPRs() {
  try {
    const resp = await forkMergeApi.listPRs(props.workId)
    prs.value = resp.data.data || []
  } catch { /* silent */ }
}

async function loadBranches() {
  try {
    const resp = await forkMergeApi.listBranches(props.workId)
    branches.value = resp.data.data || []
  } catch { /* silent */ }
}

async function handleCreate() {
  if (!prForm.value.source_branch_id || !prForm.value.target_branch_id) return
  try {
    await forkMergeApi.createPR(props.workId, {
      title: prForm.value.title,
      description: prForm.value.description,
      source_branch_id: prForm.value.source_branch_id,
      target_branch_id: prForm.value.target_branch_id,
    })
    showCreatePR.value = false
    Object.assign(prForm.value, { title: '', description: '', source_branch_id: '', target_branch_id: '' })
    await loadPRs()
  } catch { /* silent */ }
}

function prStatusType(status: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  const map: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
    open: 'warning', merged: 'success', closed: 'default', rejected: 'error',
  }
  return map[status] || 'default'
}

function prStatusLabel(status: string): string {
  const map: Record<string, string> = {
    open: '待审核', merged: '已合并', closed: '已关闭', rejected: '已拒绝',
  }
  return map[status] || status
}

function formatDate(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

onMounted(async () => { await Promise.all([loadPRs(), loadBranches()]) })
</script>

<style scoped>
.pr-panel { display: flex; flex-direction: column; gap: 12px; }

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 0.88rem; font-weight: 600;
}

.pr-list { display: flex; flex-direction: column; gap: 8px; }

.pr-item {
  padding: 12px; background: var(--bg); border-radius: var(--radius-sm);
  border-left: 3px solid var(--border);
}

.pr-title { font-size: 0.88rem; font-weight: 600; color: var(--fg); margin-bottom: 4px; }
.pr-desc { font-size: 0.8rem; color: var(--muted); margin: 4px 0; }

.pr-meta { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: var(--muted); }
.pr-branches { font-size: 0.75rem; }
.pr-time { margin-left: auto; }

.pr-actions { display: flex; gap: 6px; margin-top: 8px; }

.empty-state { padding: 24px; text-align: center; color: var(--muted); font-size: 0.85rem; }
</style>
