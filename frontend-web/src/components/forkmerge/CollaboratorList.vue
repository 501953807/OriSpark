<template>
  <div class="collab-panel">
    <div class="panel-header">
      <span>协作者</span>
      <n-button size="small" @click="showAdd = true">+ 添加</n-button>
    </div>
    <div v-if="collabs.length === 0" class="empty-state">暂无协作者</div>
    <div v-else class="collab-list">
      <div v-for="c in collabs" :key="c.id" class="collab-item">
        <span class="collab-user">用户 {{ c.user_id.slice(0, 8) }}</span>
        <n-tag size="small">{{ roleLabel(c.role) }}</n-tag>
      </div>
    </div>
    <n-modal v-model:show="showAdd" preset="dialog" title="添加协作者">
      <n-input v-model:value="newUserId" placeholder="用户 ID" />
      <template #action>
        <n-button @click="showAdd = false">取消</n-button>
        <n-button type="primary" @click="handleAdd">添加</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { NButton, NModal, NInput, NTag } from 'naive-ui'
import { forkMergeApi } from '@/api/forkMerge'
import type { Collaborator } from '@/types/forkMerge'

const props = defineProps<{ workId: string }>()
const collabs = ref<Collaborator[]>([])
const showAdd = ref(false)
const newUserId = ref('')

async function load() {
  try {
    const resp = await forkMergeApi.listCollaborators(props.workId)
    collabs.value = resp.data.data || []
  } catch { /* silent */ }
}

async function handleAdd() {
  if (!newUserId.value.trim()) return
  try {
    await forkMergeApi.addCollaborator(props.workId, { user_id: newUserId.value })
    showAdd.value = false
    newUserId.value = ''
    await load()
  } catch { /* silent */ }
}

function roleLabel(role: string): string {
  const map: Record<string, string> = {
    owner: '所有者', collaborator: '协作者', contributor: '贡献者', viewer: '查看者',
  }
  return map[role] || role
}

onMounted(load)
</script>

<style scoped>
.collab-panel { display: flex; flex-direction: column; gap: 12px; }
.panel-header { display: flex; align-items: center; justify-content: space-between; font-size: 0.88rem; font-weight: 600; }
.collab-list { display: flex; flex-direction: column; gap: 6px; }
.collab-item { display: flex; align-items: center; gap: 8px; padding: 8px 12px; background: var(--bg); border-radius: var(--radius-sm); font-size: 0.84rem; }
.empty-state { padding: 24px; text-align: center; color: var(--muted); font-size: 0.85rem; }
</style>
