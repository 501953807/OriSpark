<template>
  <div class="operator-dashboard">
    <div class="m-page-header">
      <h1 class="m-page-title">运营工作台</h1>
      <p class="m-page-subtitle">作品运营 · 授权管理 · 分润体系 · 多市场扩展</p>
    </div>

    <div v-if="loading" class="page-loading">
      <LoadingSpinner text="加载中..." />
    </div>

    <template v-else>
      <!-- Stats row -->
      <div class="stats-row">
        <StatCard icon="🎨" label="关联合约" :value="stats.total_contracts ?? 0" to="/app/contract-market" color="blue" />
        <StatCard icon="🤝" label="进行中交易" :value="stats.active_deals ?? 0" to="/app/multimarket" color="green" />
        <StatCard icon="⚠️" label="风险预警" :value="stats.risk_alerts ?? 0" to="/app/risk-center" color="orange" />
        <StatCard icon="💰" label="本月收益" :value="`¥${fmtMoney(stats.monthly_revenue ?? 0)}`" color="purple" />
      </div>

      <!-- Quick actions -->
      <MCard title="快捷操作">
        <div class="quick-actions">
          <div class="action-card" @click="$router.push('/app/contract-market')">
            <span class="action-icon">📝</span>
            <span class="action-label">合约市场</span>
          </div>
          <div class="action-card" @click="$router.push('/app/multimarket')">
            <span class="action-icon">🌍</span>
            <span class="action-label">多市场扩展</span>
          </div>
          <div class="action-card" @click="$router.push('/app/negotiation')">
            <span class="action-icon">🤝</span>
            <span class="action-label">交易谈判</span>
          </div>
          <div class="action-card" @click="$router.push('/app/capability')">
            <span class="action-icon">🧠</span>
            <span class="action-label">能力评估</span>
          </div>
          <div class="action-card" @click="$router.push('/app/credit-improvement')">
            <span class="action-icon">💳</span>
            <span class="action-label">信用提升</span>
          </div>
        </div>
      </MCard>

      <!-- Recent contracts -->
      <MCard title="最近合约动态">
        <div class="contract-list">
          <div v-if="recentContracts.length === 0" class="empty-state">暂无合约动态</div>
          <div v-for="c in recentContracts" :key="c.id" class="contract-item">
            <div class="contract-info">
              <span class="contract-title">{{ c.title }}</span>
              <span class="contract-meta">{{ c.status }} · ¥{{ c.amount }}</span>
            </div>
            <router-link :to="`/app/contract-market`" class="contract-link">查看 →</router-link>
          </div>
        </div>
      </MCard>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatCard from '@/components/common/StatCard.vue'
import MCard from '@/components/ui/MCard.vue'

const loading = ref(true)
const stats = ref({ total_contracts: 0, active_deals: 0, risk_alerts: 0, monthly_revenue: 0 })
const recentContracts = ref<any[]>([])

function fmtMoney(n: number): string {
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

onMounted(async () => {
  try {
    // TODO: 对接真实后端 API
    stats.value = { total_contracts: 12, active_deals: 5, risk_alerts: 2, monthly_revenue: 85600 }
    recentContracts.value = [
      { id: '1', title: '插画授权合约 #001', status: '进行中', amount: '12,000' },
      { id: '2', title: '摄影图库采购', status: '待签约', amount: '8,500' },
    ]
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.operator-dashboard { padding-bottom: 2rem; }
.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
.quick-actions { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1rem; }
.action-card { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; padding: 1.25rem; border-radius: 12px; background: #f8f7fc; cursor: pointer; transition: all 0.2s; }
.action-card:hover { background: #ede9fe; transform: translateY(-2px); }
.action-icon { font-size: 1.75rem; }
.action-label { font-size: 0.82rem; font-weight: 600; color: #374151; }
.contract-list { display: flex; flex-direction: column; gap: 0.75rem; }
.contract-item { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; background: #f8f7fc; border-radius: 8px; }
.contract-title { font-weight: 600; font-size: 0.9rem; color: #1f2937; }
.contract-meta { font-size: 0.78rem; color: #6b7280; margin-top: 2px; }
.contract-link { font-size: 0.82rem; color: #7c3aed; text-decoration: none; font-weight: 500; }
.contract-link:hover { text-decoration: underline; }
.empty-state { color: #9ca3af; text-align: center; padding: 2rem; }
.page-loading { display: flex; justify-content: center; padding: 3rem; }
</style>
