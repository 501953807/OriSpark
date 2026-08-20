<template>
  <div class="marketplace-view">
    <div class="m-page-header">
      <h1 class="m-page-title">商业撮合</h1>
      <p class="m-page-subtitle">交易撮合 · 合约认购 · 资金托管 · 履约保障</p>
    </div>

    <div v-if="loading" class="page-loading">
      <LoadingSpinner text="加载中..." />
    </div>

    <template v-else>
      <!-- Stats row -->
      <div class="stats-row">
        <StatCard icon="📊" label="在售合约" :value="stats.available ?? 0" to="/app/contract-market" color="blue" />
        <StatCard icon="🛒" label="我的采购" :value="stats.my_orders ?? 0" to="/app/contract-market" color="green" />
        <StatCard icon="⏳" label="待处理" :value="stats.pending ?? 0" color="orange" />
        <StatCard icon="✅" label="已完成" :value="stats.completed ?? 0" color="purple" />
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button :class="['tab', { active: tab === 'discover' }]" @click="tab = 'discover'">发现合约</button>
        <button :class="['tab', { active: tab === 'my-deals' }]" @click="tab = 'my-deals'">我的交易</button>
        <button :class="['tab', { active: tab === 'escrow' }]" @click="tab = 'escrow'">资金托管</button>
      </div>

      <!-- Discover contracts -->
      <div v-if="tab === 'discover'" class="section">
        <div v-if="contracts.length === 0" class="empty-state">暂无在售合约</div>
        <div v-else class="contract-grid">
          <div v-for="c in contracts" :key="c.id" class="contract-card">
            <div class="card-header">
              <span class="card-type">{{ c.type_label }}</span>
              <span class="card-status" :class="c.status_class">{{ c.status }}</span>
            </div>
            <h3 class="card-title">{{ c.title }}</h3>
            <p class="card-desc">{{ c.description }}</p>
            <div class="card-meta">
              <span>金额: ¥{{ c.amount }}</span>
              <span>截止: {{ c.deadline }}</span>
            </div>
            <button class="btn-primary full-width" :disabled="subscribeLoading === c.id" @click="handleSubscribe(c)">
              {{ subscribeLoading === c.id ? '认购中...' : '立即认购' }}
            </button>
          </div>
        </div>
      </div>

      <!-- My deals -->
      <div v-if="tab === 'my-deals'" class="section">
        <div v-if="myDeals.length === 0" class="empty-state">暂无交易记录</div>
        <div v-else class="deal-list">
          <div v-for="d in myDeals" :key="d.id" class="deal-item">
            <div class="deal-info">
              <span class="deal-title">{{ d.title }}</span>
              <span class="deal-meta">{{ d.status }} · ¥{{ d.amount }}</span>
            </div>
            <router-link :to="`/app/contract-market`" class="deal-link">详情 →</router-link>
          </div>
        </div>
      </div>

      <!-- Escrow -->
      <div v-if="tab === 'escrow'" class="section">
        <MCard title="资金托管记录">
          <div v-if="escrows.length === 0" class="empty-state">暂无托管记录</div>
          <div v-else class="escrow-table">
            <table>
              <thead>
                <tr>
                  <th>合约</th>
                  <th>金额</th>
                  <th>状态</th>
                  <th>更新时间</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="e in escrows" :key="e.id">
                  <td>{{ e.contract_title }}</td>
                  <td>¥{{ e.amount }}</td>
                  <td><span :class="['status-badge', e.status_class]">{{ e.status }}</span></td>
                  <td>{{ e.updated_at }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </MCard>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/useAuthStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatCard from '@/components/common/StatCard.vue'
import MCard from '@/components/ui/MCard.vue'

const loading = ref(true)
const tab = ref('discover')
const subscribeLoading = ref<string | null>(null)
const stats = ref({ available: 0, my_orders: 0, pending: 0, completed: 0 })
const contracts = ref<any[]>([])
const myDeals = ref<any[]>([])
const escrows = ref<any[]>([])

const statusClassMap: Record<string, string> = {
  进行中: 'status-active',
  待签约: 'status-pending',
  已完成: 'status-completed',
  已取消: 'status-cancelled',
}

async function handleSubscribe(contract: any) {
  if (subscribeLoading.value) return
  const authStore = useAuthStore()
  if (!authStore.user?.id) {
    ;(window as any).$toast?.show('请先登录', 'error')
    return
  }
  subscribeLoading.value = contract.id
  try {
    const { subscribeContract } = await import('@/api/contractMarket')
    await subscribeContract(contract.id, authStore.user.id)
    contracts.value = contracts.value.map(c =>
      c.id === contract.id ? { ...c, status: '待签约', status_class: 'status-pending' } : c
    )
    stats.value = { ...stats.value, available: Math.max(0, (stats.value.available ?? 0) - 1) }
    ;(window as any).$toast?.show('认购成功，等待创作者确认', 'success')
  } catch {
    ;(window as any).$toast?.show('认购失败，请稍后重试', 'error')
  } finally {
    subscribeLoading.value = null
  }
}

onMounted(async () => {
  try {
    // TODO: 对接真实后端 API
    stats.value = { available: 24, my_orders: 5, pending: 2, completed: 18 }
    contracts.value = [
      { id: '1', type_label: '插画授权', status: '进行中', status_class: 'status-active', title: '城市风光系列插画授权', description: '高清城市风光插画，支持多平台授权', amount: '15,000', deadline: '2026-09-15' },
      { id: '2', type_label: '摄影采购', status: '待签约', status_class: 'status-pending', title: '自然风光摄影图库采购', description: '需采购 500+ 张自然风光类摄影作品', amount: '28,000', deadline: '2026-09-01' },
    ]
    myDeals.value = [
      { id: '1', title: '插画授权合约 #003', status: '进行中', amount: '12,000' },
      { id: '2', title: '摄影采购合约 #007', status: '待签约', amount: '28,000' },
    ]
    escrows.value = [
      { id: '1', contract_title: '插画授权合约 #003', amount: '12,000', status: '托管中', status_class: 'status-active', updated_at: '2026-08-10' },
    ]
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.marketplace-view { padding-bottom: 2rem; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0; }
.tab { padding: 0.6rem 1.25rem; border: none; background: transparent; cursor: pointer; font-size: 0.9rem; font-weight: 500; color: #6b7280; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: all 0.2s; }
.tab.active { color: #7c3aed; border-bottom-color: #7c3aed; }
.section { margin-bottom: 1.5rem; }
.contract-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
.contract-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 1.25rem; transition: box-shadow 0.2s; }
.contract-card:hover { box-shadow: 0 4px 16px rgba(124, 58, 237, 0.12); }
.card-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.card-type { font-size: 0.75rem; color: #7c3aed; font-weight: 600; background: #ede9fe; padding: 2px 8px; border-radius: 4px; }
.card-status { font-size: 0.75rem; font-weight: 600; }
.card-title { font-size: 1rem; font-weight: 600; color: #1f2937; margin: 0 0 0.5rem; }
.card-desc { font-size: 0.82rem; color: #6b7280; margin: 0 0 1rem; line-height: 1.5; }
.card-meta { display: flex; gap: 1rem; font-size: 0.78rem; color: #9ca3af; margin-bottom: 1rem; }
.btn-primary { background: linear-gradient(135deg, #7c3aed, #5585ff); color: #fff; border: none; border-radius: 8px; padding: 0.6rem 1.25rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; transition: opacity 0.2s; }
.btn-primary:hover { opacity: 0.9; }
.full-width { width: 100%; }
.deal-list { display: flex; flex-direction: column; gap: 0.75rem; }
.deal-item { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; background: #f8f7fc; border-radius: 8px; }
.deal-title { font-weight: 600; font-size: 0.9rem; color: #1f2937; }
.deal-meta { font-size: 0.78rem; color: #6b7280; margin-top: 2px; }
.deal-link { font-size: 0.82rem; color: #7c3aed; text-decoration: none; font-weight: 500; }
.escrow-table { width: 100%; overflow-x: auto; }
.escrow-table table { width: 100%; border-collapse: collapse; }
.escrow-table th, .escrow-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid #e5e7eb; }
.escrow-table th { font-size: 0.78rem; color: #6b7280; font-weight: 600; }
.status-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.status-active { background: #dcfce7; color: #16a34a; }
.status-pending { background: #fef3c7; color: #d97706; }
.status-completed { background: #dbeafe; color: #2563eb; }
.status-cancelled { background: #fee2e2; color: #dc2626; }
.empty-state { color: #9ca3af; text-align: center; padding: 2rem; }
.page-loading { display: flex; justify-content: center; padding: 3rem; }
</style>
