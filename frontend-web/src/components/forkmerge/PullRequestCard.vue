<template>
  <div class="pr-panel">
    <div class="panel-header">
      <span>合并请求</span>
      <button class="btn btn-sm btn-secondary" @click="showCreatePR = true">+ 新建 MR</button>
    </div>

    <div v-if="prs.length === 0" class="empty-state">暂无合并请求</div>

    <div v-else class="pr-list">
      <div v-for="pr in prs" :key="pr.id" class="pr-item">
        <div class="pr-title">{{ pr.title }}</div>
        <div class="pr-meta">
          <span class="badge" :class="prBadgeClass(pr.status)">
            {{ prStatusLabel(pr.status) }}
          </span>
          <span v-if="pr.source_branch_id" class="pr-branches">
            → {{ pr.target_branch_id ? `分支 ${pr.source_branch_id} → ${pr.target_branch_id}` : '分支' }}
          </span>
          <span class="pr-time">{{ formatDate(pr.created_at) }}</span>
        </div>
        <div v-if="pr.description" class="pr-desc">{{ pr.description.slice(0, 100) }}</div>
        <div class="pr-actions" v-if="pr.status === 'open'">
          <button class="btn btn-sm btn-secondary" @click="$emit('merge', pr.id)">合并</button>
          <button class="btn btn-sm btn-danger" @click="$emit('reject', pr.id)">拒绝</button>
        </div>
      </div>
    </div>

    <!-- Create PR modal -->
    <div v-if="showCreatePR" class="modal-overlay" @click.self="showCreatePR = false">
      <div class="modal-card modal-card-lg">
        <div class="modal-header"><h3>新建合并请求</h3></div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">标题</label>
            <input class="form-input" v-model="prForm.title" placeholder="MR 标题" />
          </div>
          <div class="form-group">
            <label class="form-label">描述</label>
            <textarea class="form-textarea" v-model="prForm.description" placeholder="简要说明变更内容"></textarea>
          </div>
          <div class="form-group">
            <label class="form-label">源分支</label>
            <select class="form-select" v-model="prForm.source_branch_id">
              <option value="" disabled>请选择</option>
              <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">目标分支</label>
            <select class="form-select" v-model="prForm.target_branch_id">
              <option value="" disabled>请选择</option>
              <option v-for="b in branches" :key="b.id" :value="b.id">{{ b.name }}</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="showCreatePR = false">取消</button>
          <button class="btn btn-primary" @click="handleCreate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
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

function prBadgeClass(status: string): string {
  const map: Record<string, string> = {
    open: 'badge-warning', merged: 'badge-success', closed: 'badge-default', rejected: 'badge-danger',
  }
  return map[status] || 'badge-default'
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
