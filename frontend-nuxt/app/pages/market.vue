<template>
  <div class="page-market">
    <!-- 顶部筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <span class="filter-label">合约行情</span>
        <span class="filter-count">{{ filteredContracts.length }} 条</span>
      </div>
      <div class="filter-right">
        <select v-model="filterCategory" class="filter-select">
          <option value="">全部分类</option>
          <option value="illustration">插画</option>
          <option value="photo">摄影</option>
          <option value="3d">3D/手办</option>
          <option value="music">音乐</option>
          <option value="writing">写作</option>
        </select>
        <select v-model="filterAmount" class="filter-select">
          <option value="">金额范围</option>
          <option value="0-500">¥0 - ¥500</option>
          <option value="500-2000">¥500 - ¥2,000</option>
          <option value="2000-10000">¥2,000 - ¥10,000</option>
          <option value="10000+">¥10,000+</option>
        </select>
        <select v-model="filterStatus" class="filter-select">
          <option value="">全部状态</option>
          <option value="listed">挂牌中</option>
          <option value="active">活跃</option>
          <option value="executing">执行中</option>
          <option value="completed">已完成</option>
        </select>
      </div>
    </div>

    <!-- 行情概览条 -->
    <div class="market-ticker">
      <div class="ticker-item">
        <span class="ticker-label">挂牌总量</span>
        <span class="ticker-value data-mono">{{ stats?.total_works ?? 0 }}</span>
      </div>
      <div class="ticker-divider"></div>
      <div class="ticker-item">
        <span class="ticker-label">活跃合约</span>
        <span class="ticker-value data-mono" style="color:var(--spark-blue);">{{ stats?.active_contracts ?? 0 }}</span>
      </div>
      <div class="ticker-divider"></div>
      <div class="ticker-item">
        <span class="ticker-label">月交易额</span>
        <span class="ticker-value data-mono" style="color:var(--spark-green);">{{ formatCurrency(stats?.monthly_transaction_volume) }}</span>
      </div>
      <div class="ticker-divider"></div>
      <div class="ticker-item">
        <span class="ticker-label">成交率</span>
        <span class="ticker-value data-mono" style="color:var(--spark-gold);">67.3%</span>
      </div>
      <div class="ticker-divider"></div>
      <div class="ticker-item">
        <span class="ticker-label">平均分润</span>
        <span class="ticker-value data-mono">70%</span>
      </div>
    </div>

    <!-- 三栏布局 -->
    <div class="market-layout" v-loading="loading">
      <!-- 左侧：合约行情表 -->
      <div class="column column-table">
        <div class="column-header">
          <span class="column-title">合约列表</span>
        </div>
        <div class="contract-table">
          <div class="table-header">
            <span class="col-title">作品/创作者</span>
            <span class="col-price">挂牌价</span>
            <span class="col-change">认购</span>
            <span class="col-status">状态</span>
          </div>
          <div v-if="filteredContracts.length === 0 && !loading" class="table-empty">暂无符合条件的合约</div>
          <div
            v-for="contract in filteredContracts"
            :key="contract.id"
            class="table-row"
            :class="{ 'row-active': selectedId === contract.id }"
            @click="selectContract(contract)"
          >
            <div class="row-title">
              <div class="row-thumb" v-if="contract.thumbnail">
                <img :src="contract.thumbnail" :alt="contract.title" />
              </div>
              <div class="row-info">
                <div class="row-name">{{ contract.title }}</div>
                <div class="row-creator">{{ contract.creator_name }}</div>
              </div>
            </div>
            <div class="row-price data-mono">{{ contract.currency }} {{ (contract.total_amount ?? 0).toLocaleString() }}</div>
            <div class="row-change data-mono">
              <span class="change-val">{{ getChange(contract) }}</span>
              <span class="change-pct" :class="getChangeClass(contract)">{{ getChangePct(contract) }}</span>
            </div>
            <div class="row-status">
              <span class="status-badge" :class="'status-' + contract.status">{{ statusLabel(contract.status) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间：合约详情面板 -->
      <div class="column column-detail" v-if="selectedContract">
        <div class="column-header">
          <span class="column-title">合约详情</span>
          <span class="status-badge" :class="'status-' + selectedContract.status">{{ statusLabel(selectedContract.status) }}</span>
        </div>

        <!-- 合约状态进度条 -->
        <div class="contract-progress">
          <div class="progress-label">合约状态推进</div>
          <div class="progress-track">
            <div
              v-for="(step, idx) in contractStatusSteps"
              :key="step.key"
              class="progress-step"
              :class="{ 'step-done': getContractProgressIndex(selectedContract.status) >= idx, 'step-current': getContractProgressIndex(selectedContract.status) === idx }"
            >
              <div class="step-dot">{{ idx + 1 }}</div>
              <div class="step-label">{{ step.label }}</div>
            </div>
          </div>
          <div
            class="progress-connected"
            :style="{ width: `${(getContractProgressIndex(selectedContract.status) / (contractStatusSteps.length - 1)) * 100}%` }"
          ></div>
        </div>

        <!-- 分润占比条 -->
        <div class="profit-bar-section">
          <div class="profit-bar-label">分润结构</div>
          <div class="profit-bar-track">
            <div class="profit-bar-seg creator"
              :style="{ width: `${parseFloat(selectedContract.split_ratio || '70').split('/')[0].trim()}%` }">
              <span class="seg-label">创作者</span>
            </div>
            <div class="profit-bar-seg platform">
              <span class="seg-label">平台</span>
            </div>
          </div>
          <div class="profit-bar-legend">
            <span class="legend-dot creator"></span>
            <span class="legend-text">创作者 {{ parseFloat(selectedContract.split_ratio || '70').split('/')[0].trim() }}%</span>
            <span class="legend-dot platform"></span>
            <span class="legend-text">平台 {{ parseFloat(selectedContract.split_ratio || '70').split('/')[1]?.trim() || '3%' }}</span>
          </div>
        </div>

        <!-- 作品预览 -->
        <div class="detail-preview">
          <div class="preview-img" v-if="selectedContract.thumbnail">
            <img :src="selectedContract.thumbnail" :alt="selectedContract.title" />
          </div>
          <div class="preview-img preview-placeholder" v-else>
            <span>🖼️ 作品预览</span>
          </div>
          <div class="preview-meta">
            <div class="meta-row"><span class="meta-key">创作者</span><span class="meta-val">{{ selectedContract.creator_name }}</span></div>
            <div class="meta-row"><span class="meta-key">合约类型</span><span class="meta-val">{{ contractTypeLabel(selectedContract.contract_type) }}</span></div>
            <div class="meta-row"><span class="meta-key">存证状态</span><span class="meta-val" style="color:var(--spark-green);">✓ 已存证</span></div>
            <div class="meta-row"><span class="meta-key">风险等级</span><span class="meta-val" style="color:var(--spark-blue);">低风险</span></div>
          </div>
        </div>

        <!-- 合约信息卡 -->
        <div class="detail-card">
          <div class="card-row"><span class="card-label">挂牌金额</span><span class="card-value data-mono">{{ selectedContract.currency }} {{ (selectedContract.total_amount ?? 0).toLocaleString() }}</span></div>
          <div class="card-row"><span class="card-label">分润比例</span><span class="card-value data-mono">{{ selectedContract.split_ratio ?? '创作者 70% / 平台 3%' }}</span></div>
          <div class="card-row"><span class="card-label">使用范围</span><span class="meta-val">{{ selectedContract.scope_usage }}</span></div>
          <div class="card-row"><span class="card-label">地域范围</span><span class="meta-val">{{ selectedContract.scope_geography }}</span></div>
          <div class="card-row"><span class="card-label">距到期</span><span class="card-value data-mono" style="color:var(--spark-gold);">{{ daysUntilExpiry(selectedContract) }} 天</span></div>
          <div class="card-row"><span class="card-label">保险方案</span><span class="meta-val"><span class="badge-insurance">版权保险 included</span></span></div>
        </div>

        <!-- 操作按钮 -->
        <div class="detail-actions">
          <NuxtLink :to="`/contracts/${selectedContract.id}`" class="btn-subscribe">立即认购 →</NuxtLink>
          <button class="btn-fav" @click="isFavorited = !isFavorited">{{ isFavorited ? '★ 已收藏' : '☆ 收藏' }}</button>
        </div>

        <!-- 合约时间线 -->
        <div class="detail-timeline">
          <div class="timeline-title">交易时间线</div>
          <div class="timeline-items">
            <div class="tl-item tl-active"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">挂牌发布</div><div class="tl-time">{{ formatDate(selectedContract.created_at) }}</div></div></div>
            <div class="tl-item"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">认购锁定</div><div class="tl-time">—</div></div></div>
            <div class="tl-item"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">支付托管</div><div class="tl-time">—</div></div></div>
            <div class="tl-item"><div class="tl-dot"></div><div class="tl-content"><div class="tl-title">分润执行</div><div class="tl-time">—</div></div></div>
          </div>
        </div>
      </div>

      <!-- 中间空状态 -->
      <div class="column column-detail column-empty" v-else>
        <div class="empty-detail">
          <div class="empty-icon">📊</div>
          <div class="empty-title">选择合约查看详情</div>
          <div class="empty-desc">点击左侧合约列表中的任意合约，此处将展示详细信息与认购操作面板</div>
        </div>
      </div>

      <!-- 右侧：买卖盘口 -->
      <div class="column column-orderbook">
        <div class="column-header"><span class="column-title">买卖盘口</span></div>

        <!-- 当前价格 -->
        <div class="orderbook-price">
          <div class="op-main">
            <span class="op-price data-mono">{{ selectedContract ? formatCurrency(selectedContract.total_amount) : '—' }}</span>
            <span class="op-change" :class="getChangeClass(selectedContract)">{{ getChangePct(selectedContract) }}</span>
          </div>
          <div class="op-sub">
            <span>昨收: ¥{{ (selectedContract?.total_amount ?? 0) * 0.95 | precision(0) }}</span>
            <span>今开: ¥{{ selectedContract?.total_amount ?? '—' }}</span>
          </div>
        </div>

        <!-- 卖盘 -->
        <div class="orderbook-section">
          <div class="ob-label">卖出挂单 (Ask)</div>
          <div class="ob-row"><span class="ob-price data-mono">{{ askPrice(5) }}</span><span class="ob-qty data-mono">1</span></div>
          <div class="ob-row"><span class="ob-price data-mono">{{ askPrice(4) }}</span><span class="ob-qty data-mono">3</span></div>
          <div class="ob-row"><span class="ob-price data-mono">{{ askPrice(3) }}</span><span class="ob-qty data-mono">2</span></div>
          <div class="ob-row"><span class="ob-price data-mono">{{ askPrice(2) }}</span><span class="ob-qty data-mono">5</span></div>
          <div class="ob-row"><span class="ob-price data-mono">{{ askPrice(1) }}</span><span class="ob-qty data-mono">12</span></div>
        </div>

        <!-- 买盘 -->
        <div class="orderbook-section">
          <div class="ob-label">买入挂单 (Bid)</div>
          <div class="ob-row"><span class="ob-price data-mono" style="color:var(--spark-blue);">{{ bidPrice(1) }}</span><span class="ob-qty data-mono">8</span></div>
          <div class="ob-row"><span class="ob-price data-mono" style="color:var(--spark-blue);">{{ bidPrice(2) }}</span><span class="ob-qty data-mono">4</span></div>
          <div class="ob-row"><span class="ob-price data-mono" style="color:var(--spark-blue);">{{ bidPrice(3) }}</span><span class="ob-qty data-mono">6</span></div>
          <div class="ob-row"><span class="ob-price data-mono" style="color:var(--spark-blue);">{{ bidPrice(4) }}</span><span class="ob-qty data-mono">2</span></div>
          <div class="ob-row"><span class="ob-price data-mono" style="color:var(--spark-blue);">{{ bidPrice(5) }}</span><span class="ob-qty data-mono">1</span></div>
        </div>

        <!-- 快速认购 -->
        <div class="orderbook-actions">
          <div class="ob-action-title">快速认购</div>
          <div class="ob-input-group">
            <label>认购数量</label>
            <input v-model.number="subscribeQty" type="number" min="1" max="100" class="ob-input data-mono" />
          </div>
          <div class="ob-total">
            <span>合计金额</span>
            <span class="ob-total-val data-mono">{{ formatCurrency(subscribeQty * (selectedContract?.total_amount ?? 0)) }}</span>
          </div>
          <NuxtLink
            :to="selectedContract ? `/contracts/${selectedContract.id}` : '#'"
            class="btn-order"
            :class="{ 'btn-order-disabled': !selectedContract }"
          >确认认购</NuxtLink>
        </div>
      </div>
    </div>

    <!-- 底部：合约时间线 + 操作记录 -->
    <div class="market-footer">
      <div class="footer-section">
        <div class="footer-title">最近成交记录</div>
        <div class="trade-history">
          <div class="th-row">
            <span>时间</span><span>合约</span><span>认购方</span><span>金额</span><span>状态</span>
          </div>
          <div class="th-row th-data">
            <span class="data-mono">2026-08-10 14:32</span>
            <span>「晨曦插画集 Vol.3」</span>
            <span>某文化传媒公司</span>
            <span class="data-mono">¥12,800</span>
            <span class="status-badge status-executing">执行中</span>
          </div>
          <div class="th-row th-data">
            <span class="data-mono">2026-08-09 09:15</span>
            <span>「城市光影·摄影系列」</span>
            <span>独立设计师王某</span>
            <span class="data-mono">¥8,500</span>
            <span class="status-badge status-completed">已完成</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Contract, Work, DashboardStats } from '~/types/public'
import { fetchPublicContracts, fetchDashboardStats } from '~/composables/usePublicApi'
import { useAuthStore } from '~/stores/auth'

useHead({ title: '合约行情 — OriSpark' })

const auth = useAuthStore()
const contracts = ref<Contract[]>([])
const works = ref<Work[]>([])
const stats = ref<DashboardStats | null>(null)
const loading = ref(false)
const selectedId = ref<string | null>(null)
const filterCategory = ref('')
const filterAmount = ref('')
const filterStatus = ref('')
const subscribeQty = ref(1)
const isFavorited = ref(false)
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 合约状态机进度条配置
const contractStatusSteps = [
  { key: 'draft', label: '草稿', color: '#94a3b8' },
  { key: 'listed', label: '挂牌', color: '#f59e0b' },
  { key: 'active', label: '活跃', color: '#3b82f6' },
  { key: 'subscribed', label: '认购', color: '#6366f1' },
  { key: 'escrowed', label: '托管', color: '#8b5cf6' },
  { key: 'insured', label: '投保', color: '#ec4899' },
  { key: 'executing', label: '执行', color: '#10b981' },
  { key: 'completed', label: '完成', color: '#059669' },
] as const

function getContractProgressIndex(status: string): number {
  const idx = contractStatusSteps.findIndex(s => s.key === status)
  return idx >= 0 ? idx : 0
}

const selectedContract = computed(() => {
  if (!selectedId.value) return null
  return contracts.value.find(c => c.id === selectedId.value) ?? null
})

// 模拟涨跌幅数据（实际应来自 WebSocket）
const changeCache = new Map<string, { value: number; pct: number }>()

function getChange(contract: Contract): number {
  if (!changeCache.has(contract.id)) {
    const base = contract.total_amount ?? 0
    changeCache.set(contract.id, {
      value: Math.round(base * (Math.random() * 0.06 - 0.03)),
      pct: parseFloat(((Math.random() * 6 - 3)).toFixed(2)),
    })
  }
  return changeCache.get(contract.id)!.value
}

function getChangePct(contract: Contract | null): string {
  if (!contract) return '—'
  const c = changeCache.get(contract.id) ?? { pct: 0 }
  return `${c.pct >= 0 ? '+' : ''}${c.pct}%`
}

function getChangeClass(contract: Contract | null): string {
  if (!contract) return ''
  const c = changeCache.get(contract.id) ?? { pct: 0 }
  return c.pct >= 0 ? 'change-up' : 'change-down'
}

function askPrice(level: number): string {
  const base = selectedContract.value?.total_amount ?? 1000
  return `¥${Math.round(base * (1 + level * 0.005)).toLocaleString()}`
}

function bidPrice(level: number): string {
  const base = selectedContract.value?.total_amount ?? 1000
  return `¥${Math.round(base * (1 - level * 0.005)).toLocaleString()}`
}

const filteredContracts = computed(() => {
  let result = contracts.value
  if (filterStatus.value) {
    result = result.filter(c => c.status === filterStatus.value)
  }
  if (filterAmount.value) {
    const [min, max] = filterAmount.value.split('-').map(v => v.replace('+', ''))
    result = result.filter(c => {
      const amt = c.total_amount ?? 0
      if (max === '+') return amt >= Number(min)
      return amt >= Number(min) && amt <= Number(max)
    })
  }
  return result
})

function selectContract(contract: Contract) {
  selectedId.value = contract.id
  isFavorited.value = false
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: '草稿', listed: '挂牌中', active: '活跃',
    escrowed: '托管中', insured: '已投保', executing: '执行中',
    completed: '已完成', dispute: '争议中', resolved: '已解决',
    refunded: '已退款', cancelled: '已取消',
  }
  return labels[status] ?? status
}

function contractTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    exclusive_license: '独占许可', non_exclusive_license: '非独占许可',
    transfer: '转让', commission: '委托创作',
  }
  return labels[type] ?? type
}

function formatCurrency(value?: number): string {
  if (value == null) return '¥0'
  return `¥${value.toLocaleString('zh-CN')}`
}

function daysUntilExpiry(contract: Contract): number {
  if (!contract.created_at) return 90
  const created = new Date(contract.created_at)
  const expires = new Date(created.getTime() + 90 * 24 * 60 * 60 * 1000)
  const diff = Math.ceil((expires.getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return Math.max(0, diff)
}

function formatDate(dateStr?: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

async function loadData() {
  loading.value = true
  try {
    const [contractsRes, statsRes] = await Promise.all([
      fetchPublicContracts(),
      fetchDashboardStats(),
    ])
    contracts.value = (contractsRes ?? []) as Contract[]
    stats.value = (statsRes ?? null) as DashboardStats | null
  } catch (e) {
    console.error('Failed to load market data:', e)
  } finally {
    loading.value = false
  }
}

function startPolling() {
  refreshTimer = setInterval(async () => {
    try {
      const [c, s] = await Promise.all([fetchPublicContracts(), fetchDashboardStats()])
      contracts.value = (c ?? []) as Contract[]
      stats.value = (s ?? null) as DashboardStats | null
    } catch { /* ignore polling errors */ }
  }, 30000)
}

function stopPolling() {
  if (refreshTimer) { clearInterval(refreshTimer); refreshTimer = null }
}

onMounted(() => {
  loadData()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.page-market {
  min-height: 100vh;
  background: #f8fafc;
  padding: 0;
}

/* --- FILTER BAR --- */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 10;
}
.filter-left { display: flex; align-items: center; gap: 12px; }
.filter-label { font-size: 14px; font-weight: 700; color: #1e293b; }
.filter-count { font-size: 12px; color: #64748b; background: #f1f5f9; padding: 2px 8px; border-radius: 100px; }
.filter-right { display: flex; gap: 10px; flex-wrap: wrap; }
.filter-select {
  padding: 6px 12px; border: 1px solid #e2e8f0; border-radius: 6px;
  font-size: 13px; background: #fff; color: #374151; cursor: pointer;
}
.filter-select:focus { outline: none; border-color: #3b82f6; }

/* --- TICKER --- */
.market-ticker {
  display: flex; align-items: center;
  padding: 10px 24px; background: #fff; border-bottom: 1px solid #e2e8f0;
  gap: 0; overflow-x: auto;
}
.ticker-item { display: flex; flex-direction: column; gap: 2px; min-width: 100px; }
.ticker-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
.ticker-value { font-size: 16px; font-weight: 700; color: #1e293b; }
.ticker-divider { width: 1px; height: 32px; background: #e2e8f0; margin: 0 8px; }

/* --- THREE-COLUMN LAYOUT --- */
.market-layout {
  display: grid;
  grid-template-columns: 1fr 1.4fr 0.85fr;
  gap: 0;
  min-height: calc(100vh - 120px);
}
.column { border-right: 1px solid #e2e8f0; min-height: 100%; }
.column:last-child { border-right: none; }
.column-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; background: #f8fafc; border-bottom: 1px solid #e2e8f0;
}
.column-title { font-size: 13px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.05em; }

/* --- CONTRACT TABLE --- */
.contract-table { display: flex; flex-direction: column; }
.table-header {
  display: grid; grid-template-columns: 2fr 1fr 0.8fr 0.8fr;
  padding: 8px 16px; background: #f1f5f9; border-bottom: 1px solid #e2e8f0;
  font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em;
}
.table-row {
  display: grid; grid-template-columns: 2fr 1fr 0.8fr 0.8fr;
  padding: 10px 16px; border-bottom: 1px solid #f1f5f9;
  cursor: pointer; transition: background 0.15s; align-items: center;
}
.table-row:hover { background: #f8fafc; }
.row-active { background: #eff6ff; border-left: 3px solid #3b82f6; }
.row-title { display: flex; align-items: center; gap: 10px; min-width: 0; }
.row-thumb { width: 36px; height: 36px; border-radius: 4px; overflow: hidden; flex-shrink: 0; background: #e2e8f0; }
.row-thumb img { width: 100%; height: 100%; object-fit: cover; }
.row-info { min-width: 0; }
.row-name { font-size: 13px; font-weight: 600; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row-creator { font-size: 11px; color: #94a3b8; }
.row-price { font-size: 13px; font-weight: 600; color: #1e293b; }
.row-change { display: flex; flex-direction: column; align-items: flex-end; gap: 1px; }
.change-val { font-size: 12px; font-weight: 600; }
.change-pct { font-size: 11px; }
.change-up { color: #10b981; }
.change-down { color: #ef4444; }
.row-status { font-size: 11px; }

/* --- DETAIL PANEL --- */
.detail-preview {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px;
  padding: 16px; border-bottom: 1px solid #e2e8f0;
}
.preview-img { border-radius: 8px; overflow: hidden; aspect-ratio: 4/3; background: #f1f5f9; }
.preview-img img { width: 100%; height: 100%; object-fit: cover; }
.preview-placeholder { display: flex; align-items: center; justify-content: center; color: #94a3b8; font-size: 14px; }
.preview-meta { display: flex; flex-direction: column; gap: 10px; }
.meta-row { display: flex; justify-content: space-between; align-items: center; }
.meta-key { font-size: 12px; color: #94a3b8; }
.meta-val { font-size: 12px; font-weight: 600; color: #1e293b; }

.detail-card {
  margin: 16px; padding: 16px; background: #fff; border: 1px solid #e2e8f0;
  border-radius: 8px; display: flex; flex-direction: column; gap: 10px;
}
.card-row { display: flex; justify-content: space-between; align-items: center; }
.card-label { font-size: 12px; color: #94a3b8; }
.card-value { font-size: 13px; font-weight: 600; color: #1e293b; }
.badge-insurance { display: inline-block; padding: 2px 8px; background: #fef3c7; color: #92400e; border-radius: 4px; font-size: 11px; font-weight: 600; }

.detail-actions { display: flex; gap: 10px; padding: 0 16px 16px; }
.btn-subscribe {
  flex: 1; padding: 10px 16px; background: #1e293b; color: #fff; border: none; border-radius: 6px;
  font-size: 14px; font-weight: 600; cursor: pointer; text-decoration: none; text-align: center; transition: background 0.15s;
}
.btn-subscribe:hover { background: #334155; }
.btn-fav { padding: 10px 16px; background: #fff; color: #94a3b8; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; cursor: pointer; transition: all 0.15s; }
.btn-fav:hover { border-color: #f59e0b; color: #f59e0b; }
.btn-fav[style*="color"] { color: #f59e0b; }

.detail-timeline { margin: 0 16px 16px; padding: 16px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
.timeline-title { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
.timeline-items { display: flex; flex-direction: column; gap: 0; }
.tl-item { display: flex; gap: 12px; position: relative; }
.tl-dot { width: 10px; height: 10px; border-radius: 50%; background: #cbd5e1; margin-top: 4px; flex-shrink: 0; }
.tl-active .tl-dot { background: #3b82f6; box-shadow: 0 0 0 3px rgba(59,130,246,0.2); }
.tl-content { flex: 1; padding-bottom: 12px; border-left: 1px solid #e2e8f0; margin-left: 4px; }
.tl-title { font-size: 13px; font-weight: 600; color: #374151; }
.tl-time { font-size: 11px; color: #94a3b8; }

.column-empty { display: flex; align-items: center; justify-content: center; }
.empty-detail { text-align: center; padding: 40px 24px; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
.empty-title { font-size: 16px; font-weight: 600; color: #374151; margin-bottom: 8px; }
.empty-desc { font-size: 13px; color: #94a3b8; max-width: 280px; }

/* --- ORDERBOOK --- */
.orderbook-price { padding: 16px; border-bottom: 1px solid #e2e8f0; background: #fff; }
.op-main { display: flex; align-items: baseline; gap: 8px; }
.op-price { font-size: 24px; font-weight: 700; color: #1e293b; }
.op-change { font-size: 13px; font-weight: 600; }
.op-sub { display: flex; gap: 16px; margin-top: 6px; font-size: 11px; color: #94a3b8; }
.orderbook-section { padding: 12px 16px; border-bottom: 1px solid #e2e8f0; }
.ob-label { font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.ob-row { display: flex; justify-content: space-between; font-size: 12px; padding: 3px 0; }
.ob-price { color: #ef4444; }
.ob-qty { color: #64748b; }

.orderbook-actions { padding: 16px; }
.ob-action-title { font-size: 12px; font-weight: 700; color: #475569; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.05em; }
.ob-input-group { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.ob-input-group label { font-size: 12px; color: #94a3b8; }
.ob-input { padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; font-family: var(--font-mono, monospace); }
.ob-input:focus { outline: none; border-color: #3b82f6; }
.ob-total { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 12px; color: #374151; }
.ob-total-val { font-weight: 700; color: #1e293b; }
.btn-order {
  display: block; width: 100%; padding: 12px; background: #10b981; color: #fff; border: none; border-radius: 6px;
  font-size: 14px; font-weight: 700; cursor: pointer; text-align: center; text-decoration: none; transition: background 0.15s;
}
.btn-order:hover { background: #059669; }
.btn-order-disabled { background: #cbd5e1; cursor: not-allowed; }

/* --- FOOTER --- */
.market-footer { padding: 24px; background: #fff; border-top: 1px solid #e2e8f0; }
.footer-section { max-width: 1200px; margin: 0 auto; }
.footer-title { font-size: 14px; font-weight: 700; color: #374151; margin-bottom: 12px; }
.trade-history { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.th-row { display: grid; grid-template-columns: 1fr 2fr 1.5fr 1fr 1fr; padding: 8px 16px; font-size: 12px; background: #f8fafc; color: #94a3b8; border-bottom: 1px solid #e2e8f0; }
.th-data { color: #374151; font-size: 13px; }

/* --- STATUS BADGES --- */
.status-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;
}
.status-listed { background: #fef3c7; color: #92400e; }
.status-active { background: #d1fae5; color: #065f46; }
.status-executing { background: #dbeafe; color: #1e40af; }
.status-completed { background: #e5e7eb; color: #374151; }
.status-dispute { background: #fee2e2; color: #991b1b; }

/* --- RESPONSIVE --- */
@media (max-width: 1024px) {
  .market-layout { grid-template-columns: 1fr 1fr; }
  .column-orderbook { grid-column: span 2; }
}
@media (max-width: 768px) {
  .market-layout { grid-template-columns: 1fr; }
  .column-orderbook { grid-column: span 1; }
  .filter-bar { flex-direction: column; align-items: flex-start; gap: 12px; }
  .filter-right { flex-wrap: wrap; }
  .table-header, .table-row { grid-template-columns: 2fr 1fr 0.8fr; }
  .col-status { display: none; }
}

/* --- CONTRACT PROGRESS BAR --- */
.contract-progress {
  margin: 0 16px 12px; padding: 14px 16px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
}
.progress-label {
  font-size: 11px; font-weight: 700; color: #475569;
  text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;
}
.progress-track {
  display: flex; align-items: flex-start; gap: 0; position: relative;
}
.progress-step {
  display: flex; flex-direction: column; align-items: center; flex: 1; position: relative; z-index: 1;
}
.step-dot {
  width: 22px; height: 22px; border-radius: 50%;
  background: #e2e8f0; color: #94a3b8; font-size: 10px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  transition: background 0.2s, color 0.2s, box-shadow 0.2s;
}
.step-label {
  font-size: 10px; color: #94a3b8; margin-top: 4px; white-space: nowrap;
  transition: color 0.2s;
}
.step-done .step-dot {
  background: #10b981; color: #fff; box-shadow: 0 0 0 3px rgba(16,185,129,0.15);
}
.step-done .step-label { color: #065f46; }
.step-current .step-dot {
  background: #3b82f6; color: #fff; box-shadow: 0 0 0 3px rgba(59,130,246,0.25);
  animation: progress-pulse 1.5s ease-in-out infinite;
}
.step-current .step-label { color: #1e40af; font-weight: 600; }
@keyframes progress-pulse {
  0%, 100% { box-shadow: 0 0 0 3px rgba(59,130,246,0.25); }
  50% { box-shadow: 0 0 0 6px rgba(59,130,246,0.12); }
}
.progress-connected {
  position: absolute; top: 11px; left: 6.25%; right: 6.25%; height: 2px;
  background: #e2e8f0; z-index: 0; pointer-events: none;
}

/* --- PROFIT BAR --- */
.profit-bar-section {
  margin: 0 16px 12px; padding: 14px 16px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
}
.profit-bar-label {
  font-size: 11px; font-weight: 700; color: #475569;
  text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;
}
.profit-bar-track {
  display: flex; height: 24px; border-radius: 6px; overflow: hidden; margin-bottom: 8px;
}
.profit-bar-seg {
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: #fff; transition: width 0.4s ease;
}
.profit-bar-seg.creator {
  background: linear-gradient(135deg, #3b82f6 0%, #6366f1 100%);
}
.profit-bar-seg.platform {
  background: linear-gradient(135deg, #94a3b8 0%, #cbd5e1 100%);
  flex: 1;
}
.profit-bar-seg .seg-label { text-shadow: 0 1px 2px rgba(0,0,0,0.2); }
.profit-bar-legend {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-dot.creator { background: #3b82f6; }
.legend-dot.platform { background: #94a3b8; }
.legend-text { font-size: 12px; color: #475569; }
.data-mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; font-variant-numeric: tabular-nums; }
</style>
