<template>
  <div class="branch-panel">
    <div class="panel-header">
      <span>分支列表</span>
      <n-button size="small" @click="showCreateBranch = true">+ 新建分支</n-button>
    </div>

    <div v-if="branches.length === 0" class="empty-state">暂无分支</div>

    <div v-else class="branch-list">
      <div v-for="b in branches" :key="b.id" :class="['branch-item', { default: b.is_default }]">
        <span class="branch-icon">{{ b.is_default ? '⭐' : '🌿' }}</span>
        <span class="branch-name">{{ b.name }}</span>
        <span v-if="b.commit_id" class="branch-commit">{{ b.commit_id.slice(0, 7) }}</span>
      </div>
    </div>

    <!-- Create branch modal -->
    <n-modal v-model:show="showCreateBranch" preset="dialog" title="新建分支">
      <n-input v-model:value="newBranchName" placeholder="分支名称，如 feature/add-logo" />
      <template #action>
        <n-button @click="showCreateBranch = false">取消</n-button>
        <n-button type="primary" :disabled="!newBranchName.trim()" @click="handleCreate">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NButton, NModal, NInput } from 'naive-ui'
import { forkMergeApi } from '@/api/forkMerge'
import type { Branch } from '@/types/forkMerge'

const props = defineProps<{ workId: string }>()
const emit = defineEmits<{ branchCreated: [branch: Branch] }>()

const branches = ref<Branch[]>([])
const loading = ref(false)
const showCreateBranch = ref(false)
const newBranchName = ref('')

async function loadBranches() {
  loading.value = true
  try {
    const resp = await forkMergeApi.listBranches(props.workId)
    branches.value = resp.data.data || []
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!newBranchName.value.trim()) return
  try {
    const resp = await forkMergeApi.createBranch(props.workId, { name: newBranchName.value })
    branches.value.push(resp.data.data)
    emit('branchCreated', resp.data.data)
    showCreateBranch.value = false
    newBranchName.value = ''
  } catch {
    // silent error handling
  }
}

onMounted(loadBranches)
</script>

<style scoped>
.branch-panel { display: flex; flex-direction: column; gap: 12px; }

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 0.88rem; font-weight: 600;
}

.branch-list { display: flex; flex-direction: column; gap: 6px; }

.branch-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; background: var(--bg); border-radius: var(--radius-sm);
  font-size: 0.84rem;
}

.branch-item.default { border-left: 3px solid var(--accent); }

.branch-name { flex: 1; color: var(--fg); font-weight: 500; }
.branch-commit { color: var(--muted); font-size: 0.75rem; font-family: monospace; }

.empty-state { padding: 24px; text-align: center; color: var(--muted); font-size: 0.85rem; }
</style>
