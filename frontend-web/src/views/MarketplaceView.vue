<template>
  <div class="marketplace-view">
    <div class="m-page-header">
      <h1 class="m-page-title">商业撮合</h1>
      <p class="m-page-subtitle">交易撮合 · 合约认购 · 资金托管 · 履约保障</p>
    </div>

    <div v-if="loading" class="page-loading">
      <LoadingSpinner text="加载中..." />
    </div>
    <div v-else-if="error" class="empty-state">
      {{ error }}
      <button class="btn-primary" style="margin-top:1rem" @click="loadData">重新加载</button>
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
import client from '@/api/client'

const loading = ref(true)
const error = ref<string | null>(null)
const tab = ref('discover')
const subscribeLoading = ref<string | null>(null)
const stats = ref({ available: 0, my_orders: 0, pending: 0, completed: 0 })
const contracts = ref<any[]>([])
const myDeals = ref<any[]>([])
const escrows = ref<any[]>([])

const statusMap: Record<string, string> = {
  listed: '挂牌中', active: '进行中', subscribed: '待签约',
  escrowed: '托管中', executing: '执行中', completed: '已完成',
  dispute: '争议中', cancelled: '已取消',
}
const statusClassMap: Record<string, string> = {
  进行中: 'status-active', 待签约: 'status-pending',
  已完成: 'status-completed', 已取消: 'status-cancelled',
  挂牌中: 'status-active', 托管中: 'status-pending',
  执行中: 'status-active', 争议中: 'status-cancelled',
}
const typeLabelMap: Record<string, string> = {
  exclusive_license: '独占许可', non_exclusive_license: '非独占许可',
  copyright_transfer: '著作权转让', product_license: '产品许可',
  commission: '委托创作',
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

async function loadData() {
  error.value = null
  try {
    // 加载公开合约列表（挂牌中 / 活跃状态）
    const [publicRes, statsRes] = await Promise.all([
      client.get('/public/contracts', { params: { status: 'listed' }, timeout: 10000 }),
      client.get('/public/dashboard-stats', { timeout: 10000 }),
    ])

    // 转换公开合约为 UI 格式
    const publicContracts = (publicRes.data || []) as Array<{
      id: string; title: string; description: string; contract_type: string
      total_amount: number; status: string; created_at?: string
    }>
    contracts.value = publicContracts.map(c => ({
      id: c.id,
      type_label: typeLabelMap[c.contract_type] ?? c.contract_type,
      status: statusMap[c.status] ?? c.status,
      status_class: statusClassMap[statusMap[c.status] ?? c.status] ?? '',
      title: c.title,
      description: c.description,
      amount: c.total_amount?.toLocaleString('zh-CN') ?? '',
      deadline: c.created_at
        ? new Date(c.created_at).toLocaleDateString('zh-CN')
        : '',
    }))

    // 更新统计卡片
    const ds = statsRes.data
    if (ds) {
      stats.value = {
        available: ds.active_contracts ?? 0,
        my_orders: ds.total_contracts_ever ?? 0,
        pending: 0,
        completed: 0,
      }
    }

    // 加载当前用户的合约列表（需认证）
    const authStore = useAuthStore()
    if (authStore.user?.id) {
      try {
        const userRes = await client.get('/contracts', { params: { limit: 20 }, timeout: 10000 })
        const userContracts = (userRes.data || []) as Array<{
          id: string; title: string; status: string; total_amount: number;
          contract_type: string; creator_id?: string
        }>
        // 我的交易记录
        myDeals.value = userContracts
          .filter(c => !['draft', 'cancelled'].includes(c.status))
          .map(c => ({
            id: c.id,
            title: c.title,
            status: statusMap[c.status] ?? c.status,
            amount: c.total_amount?.toLocaleString('zh-CN') ?? '',
          }))
          .slice(0, 10)

        // 资金托管记录（escrowed 状态）
        escrows.value = userContracts
          .filter(c => c.status === 'escrowed')
          .map(c => ({
            id: c.id,
            contract_title: c.title,
            amount: c.total_amount?.toLocaleString('zh-CN') ?? '',
            status: '托管中',
            status_class: 'status-pending',
            updated_at: '',
          }))
      } catch {
        // 用户合约加载失败不影响主流程
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
    console.error('[Marketplace] 数据加载失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
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
