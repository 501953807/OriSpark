<template>
  <div class="rights-view">
    <!-- Loading state -->
    <div v-if="checking" class="rights-loading" style="text-align:center;padding:60px;color:var(--muted)">加载中...</div>

    <!-- 前置校验: 无作品时拦截 -->
    <EmptyState
      v-else-if="!hasWorks"
      icon="🛡️"
      title="暂无已确权作品"
      description="权利保护需要先上传作品并完成 IP 登记确权"
      :show-action="true"
      :primary-action="{ label: '前往上传作品', onClick: goToWorks }"
      :tips="['上传作品 → 完成 IP 登记 → 开启权利保护']"
    />

    <template v-else>
      <div class="tabs-bar">
        <button :class="['tab-btn', { active: tab === 'notary' }]" @click="tab = 'notary'">🔒 存证确权</button>
        <button :class="['tab-btn', { active: tab === 'monitor' }]" @click="tab = 'monitor'">🛡️ 侵权监测</button>
      </div>
      <!-- 复用已有 NotaryView 和 MonitorView 的内容，简化组合 -->
      <NotaryPanel v-if="tab === 'notary'" />
      <MonitorPanel v-if="tab === 'monitor'" />
    </template>
  </div>
</template>
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/useAppStore'
import EmptyState from '@/components/common/EmptyState.vue'
import NotaryPanel from './rights/NotaryPanel.vue'
import MonitorPanel from './rights/MonitorPanel.vue'
import { worksApi } from '@/api/works'

const router = useRouter()
const appStore = useAppStore()
const tab = ref('notary')
const hasWorks = ref(false)
const checking = ref(true)

const goToWorks = () => router.push('/app/works')

async function checkWorks() {
  try {
    const res = await worksApi.list({ page_size: 1 })
    hasWorks.value = (res.data.data?.items?.length || res.data.data?.length || 0) > 0
  } catch {
    // Fallback to appStore if API fails
    hasWorks.value = appStore.workCount > 0
  } finally {
    checking.value = false
  }
}

onMounted(() => {
  // Use appStore if already populated, otherwise fetch from API
  if (appStore.workCount > 0) {
    hasWorks.value = true
    checking.value = false
  } else {
    checkWorks()
  }
})

watch(() => appStore.workCount, (val) => {
  hasWorks.value = val > 0
})
</script>
<style scoped>
.tabs-bar { display: flex; gap: 4px; border-bottom: 2px solid var(--border); margin-bottom: 20px; padding-bottom: 0; }
.tab-btn { padding: 12px 24px; border: none; background: none; cursor: pointer; font-size: 0.95rem; color: var(--muted); border-bottom: 2px solid transparent; margin-bottom: -2px; transition: all 0.2s; }
.tab-btn:hover { color: var(--fg); }
.tab-btn.active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
</style>
