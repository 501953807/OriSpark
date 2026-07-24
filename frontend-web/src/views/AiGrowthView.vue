<script setup lang="ts">
import { ref, computed } from 'vue'
import { aiSessionV2Api, achievementApi, invoiceApi } from '@/api/module9'

const activeTab = ref('badges')
const loading = ref(false)

// ==================== Badges ====================
const badges = ref<any[]>([])

async function loadBadges() {
  loading.value = true
  try {
    const res = await achievementApi.listBadges()
    badges.value = (res.data ?? res) as any[]
  } catch { /* handled */ } finally { loading.value = false }
}

loadBadges()

// ==================== Invoices ====================
const invoices = ref<any[]>([])
const invoiceLoading = ref(false)

async function loadInvoices() {
  invoiceLoading.value = true
  try {
    const res = await invoiceApi.listMy({ limit: 50 })
    invoices.value = (res.data ?? res) as any[]
  } catch { /* handled */ } finally { invoiceLoading.value = false }
}

loadInvoices()

async function handleMarkPaid(id: string) {
  try {
    await invoiceApi.markPaid(id)
    loadInvoices()
  } catch { /* handled */ }
}

// ==================== Session Comparison ====================
const workId = ref('')
const sessionA = ref('')
const sessionB = ref('')
const comparison = ref<any>(null)
const comparing = ref(false)

async function runComparison() {
  if (!workId.value || !sessionA.value || !sessionB.value) return
  comparing.value = true
  try {
    const res = await aiSessionV2Api.compareSessions(workId.value, sessionA.value, sessionB.value)
    comparison.value = res.data ?? res
  } catch { /* handled */ } finally { comparing.value = false }
}
</script>

<template>
  <div class="ai-growth-view">
    <h2>AI 增长引擎</h2>
    <p class="subtitle">AI 创作会话对比、成就徽章与发票管理</p>

    <div class="tabs">
      <button :class="['tab', { active: activeTab === 'sessions' }]" @click="activeTab = 'sessions'">会话对比</button>
      <button :class="['tab', { active: activeTab === 'badges' }]" @click="activeTab = 'badges'">成就徽章</button>
      <button :class="['tab', { active: activeTab === 'invoices' }]" @click="activeTab = 'invoices'">发票管理</button>
    </div>

    <!-- Session Comparison -->
    <div v-if="activeTab === 'sessions'" class="section">
      <h3>AI 创作会话对比</h3>
      <p class="hint">输入 Work ID 和两个 Session ID 进行参数对比。</p>

      <div class="form-row">
        <input v-model="workId" placeholder="Work ID" class="input" />
        <input v-model="sessionA" placeholder="Session A ID" class="input" />
        <input v-model="sessionB" placeholder="Session B ID" class="input" />
        <button :disabled="comparing || !workId || !sessionA || !sessionB" @click="runComparison" class="btn-primary">
          {{ comparing ? '对比中...' : '对比' }}
        </button>
      </div>

      <div v-if="comparison" class="comparison-result">
        <h4>差异分析</h4>
        <pre>{{ JSON.stringify(comparison, null, 2) }}</pre>
      </div>
    </div>

    <!-- Badges -->
    <div v-else-if="activeTab === 'badges'" class="section">
      <h3>成就徽章</h3>
      <div v-if="loading" class="loading-text">加载中...</div>
      <div v-else-if="badges.length === 0" class="empty-state">暂无徽章数据</div>
      <div v-else class="badge-grid">
        <div v-for="badge in badges" :key="badge.id" class="badge-card">
          <div class="badge-icon" :style="{ background: badge.color_hex || '#667eea' }">
            {{ badge.icon || '🏅' }}
          </div>
          <h4>{{ badge.badge_name }}</h4>
          <p>{{ badge.badge_description }}</p>
          <span class="xp">+{{ badge.xp_reward }} XP</span>
        </div>
      </div>
    </div>

    <!-- Invoices -->
    <div v-else class="section">
      <h3>发票管理</h3>
      <div v-if="invoiceLoading" class="loading-text">加载中...</div>
      <div v-else-if="invoices.length === 0" class="empty-state">暂无发票记录</div>
      <div v-else class="invoice-list">
        <div v-for="inv in invoices" :key="inv.id" class="invoice-card">
          <div class="inv-header">
            <span class="inv-id">{{ inv.id }}</span>
            <span :class="['inv-status', inv.status]">{{ inv.status }}</span>
          </div>
          <div class="inv-details">
            <span>金额: ¥{{ inv.amount ?? '0.00' }}</span>
            <span>日期: {{ inv.created_at }}</span>
          </div>
          <button v-if="inv.status !== 'paid'" @click="handleMarkPaid(inv.id)" class="btn-small">标记已支付</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-growth-view { max-width: 1000px; }
.subtitle { color: var(--muted); margin-bottom: 16px; }
.tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-bottom: 20px; overflow-x: auto; }
.tab { padding: 10px 16px; border: none; background: none; cursor: pointer; font-size: 0.9rem; white-space: nowrap; opacity: 0.6; transition: opacity 0.2s; }
.tab:hover { opacity: 0.8; }
.tab.active { opacity: 1; border-bottom: 2px solid var(--primary); }
.section { margin-top: 16px; }
.hint { color: var(--muted); font-size: 0.85rem; margin-bottom: 16px; }

.form-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.input { flex: 1; min-width: 120px; padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.9rem; }
.btn-primary { padding: 8px 20px; background: var(--primary); color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-small { padding: 4px 12px; background: var(--primary); color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }

.comparison-result { background: var(--surface); padding: 16px; border-radius: 8px; border: 1px solid var(--border); }
.comparison-result pre { white-space: pre-wrap; font-size: 0.85rem; margin: 0; }

.badge-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.badge-card { padding: 16px; text-align: center; border: 1px solid var(--border); border-radius: 8px; }
.badge-icon { width: 48px; height: 48px; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; }
.badge-card h4 { margin: 4px 0; }
.badge-card p { font-size: 0.8rem; color: var(--muted); margin: 4px 0; }
.xp { display: inline-block; font-size: 0.85rem; font-weight: 600; color: #059669; }

.invoice-list { display: flex; flex-direction: column; gap: 8px; }
.invoice-card { padding: 12px 16px; border: 1px solid var(--border); border-radius: 8px; display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.inv-header { display: flex; align-items: center; gap: 8px; flex: 1; min-width: 0; }
.inv-id { font-size: 0.8rem; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.inv-status { font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; }
.inv-status.paid { background: #d1fae5; color: #065f46; }
.inv-status.pending { background: #fef3c7; color: #92400e; }
.inv-details { font-size: 0.8rem; color: var(--muted); }

.loading-text { text-align: center; padding: 40px; color: var(--muted); }
.empty-state { text-align: center; padding: 40px; color: var(--muted); }
</style>
