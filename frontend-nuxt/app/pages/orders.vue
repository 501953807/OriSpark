<!-- OriSpark Orders Page — 我的订单 -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { fetchOrders } from '~/composables/useSupplyApi'

definePageMeta({ layout: 'materio-topnav' })

// SSR-safe; auth middleware redirects non-logged-in users
const loading = ref(false)
const error = ref<string | null>(null)
const activeTab = ref('all')
const statusFilter = ref('')

// API response shape (matches factory_order.py list_orders)
interface ApiOrder {
  id: string
  order_number: string
  contract_id?: string
  work_id?: string
  factory_id?: string
  product_name: string
  product_category?: string
  quantity: number
  unit_price: number
  total_amount: number
  status: string
  expected_date?: string
  notes?: string
  created_at?: string
  updated_at?: string
}

const orders = ref<ApiOrder[]>([])

const filteredOrders = computed(() => {
  let result = orders.value
  if (activeTab.value !== 'all') {
    result = result.filter(o => activeTab.value === 'production' || activeTab.value === 'delivery')
    // All factory orders are production type; delivery is sub-state of shipping
    if (activeTab.value === 'delivery') {
      result = result.filter(o => o.status === 'shipped' || o.status === 'completed')
    }
  }
  if (statusFilter.value) {
    result = result.filter(o => o.status === statusFilter.value)
  }
  return result
})

const stats = computed(() => ({
  total: orders.value.length,
  active: orders.value.filter(o => o.status === 'confirmed' || o.status === 'in_production').length,
  pending: orders.value.filter(o => o.status === 'draft').length,
  completed: orders.value.filter(o => o.status === 'completed').length,
  total_amount: orders.value.reduce((sum, o) => sum + o.total_amount, 0),
}))

const statusMap: Record<string, { label: string; class: string }> = {
  draft:       { label: '待处理',   class: 'status-pending' },
  confirmed:   { label: '进行中',  class: 'status-active' },
  in_production: { label: '生产中', class: 'status-active' },
  quality_check: { label: '质检中', class: 'status-shipping' },
  shipped:     { label: '配送中',  class: 'status-shipping' },
  completed:   { label: '已完成',  class: 'status-completed' },
  cancelled:   { label: '已取消',  class: 'status-cancelled' },
}

async function loadOrders() {
  loading.value = true
  error.value = null
  try {
    orders.value = await fetchOrders()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载订单失败'
  } finally {
    loading.value = false
  }
}

async function confirmOrder(orderId: string) {
  try {
    await import('~/composables/useSupplyApi').then(m => m.confirmOrder(orderId))
    await loadOrders()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function startProduction(orderId: string) {
  try {
    await import('~/composables/useSupplyApi').then(m => m.startProduction(orderId))
    await loadOrders()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function shipOrder(order: ApiOrder) {
  try {
    const tracking = prompt('请输入物流单号（可选）：')
    await import('~/composables/useSupplyApi').then(m => m.shipOrder(order.id, { tracking_number: tracking || undefined }))
    await loadOrders()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function inspectOrder(order: ApiOrder) {
  try {
    const passed = confirm(`确认 ${order.product_name} 质检通过？\n点击"确定"表示通过，"取消"表示不通过。`)
    await import('~/composables/useSupplyApi').then(m => m.inspectOrder(order.id, { passed }))
    await loadOrders()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  }
}

onMounted(loadOrders)
</script>

<template>
  <div class="page-orders">
    <!-- Header -->
    <div class="orders-header">
      <h1 class="page-title">我的订单</h1>
      <div class="header-actions">
        <select v-model="statusFilter" class="filter-select">
          <option value="">全部状态</option>
          <option value="draft">待处理</option>
          <option value="confirmed">确认中</option>
          <option value="in_production">生产中</option>
          <option value="shipped">配送中</option>
          <option value="completed">已完成</option>
          <option value="cancelled">已取消</option>
        </select>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-label">总订单</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #3b82f6">{{ stats.active }}</div>
        <div class="stat-label">进行中</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #f59e0b">{{ stats.pending }}</div>
        <div class="stat-label">待处理</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" style="color: #10b981">{{ stats.completed }}</div>
        <div class="stat-label">已完成</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">¥{{ (stats.total_amount / 10000).toFixed(1) }}万</div>
        <div class="stat-label">总金额</div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'all' }]" @click="activeTab = 'all'">全部</button>
      <button :class="['tab-btn', { active: activeTab === 'production' }]" @click="activeTab = 'production'">生产订单</button>
      <button :class="['tab-btn', { active: activeTab === 'delivery' }]" @click="activeTab = 'delivery'">已完成/配送</button>
    </div>

    <!-- Loading / Error States -->
    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="error" class="error-state">{{ error }}</div>

    <!-- Orders List -->
    <div class="orders-list">
      <div v-if="!loading && !error && filteredOrders.length === 0" class="empty-state">
        暂无订单
      </div>
      <div v-for="order in filteredOrders" :key="order.id" class="order-card">
        <div class="order-header">
          <div class="order-meta">
            <span class="order-type">生产订单</span>
            <span class="order-id">{{ order.order_number }}</span>
          </div>
          <span :class="['status-badge', statusMap[order.status]?.class]">
            {{ statusMap[order.status]?.label }}
          </span>
        </div>

        <div class="order-body">
          <div class="order-info">
            <h3 class="order-title">{{ order.product_name }}</h3>
            <p v-if="order.product_category" class="order-category">{{ order.product_category }}</p>
            <p class="order-amount">¥{{ order.total_amount.toLocaleString() }}</p>
          </div>
          <div class="order-dates">
            <div class="date-item">
              <span class="date-label">创建</span>
              <span class="date-value">{{ order.created_at ? new Date(order.created_at).toLocaleDateString('zh-CN') : '—' }}</span>
            </div>
            <div class="date-item">
              <span class="date-label">预期</span>
              <span class="date-value">{{ order.expected_date ? new Date(order.expected_date).toLocaleDateString('zh-CN') : '—' }}</span>
            </div>
            <div class="date-item">
              <span class="date-label">数量</span>
              <span class="date-value">{{ order.quantity }}</span>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="order-actions">
          <button v-if="order.status === 'draft'" class="btn-primary" @click="confirmOrder(order.id)">确认订单</button>
          <button v-if="order.status === 'confirmed'" class="btn-primary" @click="startProduction(order.id)">开始生产</button>
          <button v-if="order.status === 'in_production' || order.status === 'quality_check'" class="btn-secondary" @click="shipOrder(order)">标记发货</button>
          <button v-if="order.status === 'in_production' || order.status === 'quality_check' || order.status === 'shipped'" class="btn-outline" @click="inspectOrder(order)">质检</button>
          <span v-if="order.status === 'shipped'" class="tracking-text">物流: {{ order.tracking_number || '—' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-orders {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filter-select {
  padding: 0.5rem 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 0.875rem;
  background: #fff;
  cursor: pointer;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 1.25rem;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1f2937;
}

.stat-label {
  font-size: 0.8rem;
  color: #6b7280;
  margin-top: 0.25rem;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1.5rem;
}

.tab-btn {
  padding: 0.6rem 1.25rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  color: #6b7280;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;
}

.tab-btn.active {
  color: #7c3aed;
  border-bottom-color: #7c3aed;
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.order-card {
  background: #fff;
  border-radius: 12px;
  padding: 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s;
}

.order-card:hover {
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.15);
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.order-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.order-type {
  font-size: 0.75rem;
  color: #7c3aed;
  background: #ede9fe;
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.order-id {
  font-size: 0.8rem;
  color: #9ca3af;
}

.order-body {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.order-info h3 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  color: #1f2937;
}

.order-category {
  margin: 0 0 0.25rem;
  font-size: 0.8rem;
  color: #6b7280;
}

.order-amount {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: #7c3aed;
}

.order-dates {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: right;
}

.date-item {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.date-label {
  font-size: 0.75rem;
  color: #9ca3af;
}

.date-value {
  font-size: 0.8rem;
  color: #6b7280;
}

.order-actions {
  display: flex;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.status-badge {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-active {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-pending {
  background: #fef3c7;
  color: #b45309;
}

.status-shipping {
  background: #e0e7ff;
  color: #4338ca;
}

.status-completed {
  background: #d1fae5;
  color: #065f46;
}

.status-cancelled {
  background: #fee2e2;
  color: #991b1b;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #9ca3af;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.error-state {
  color: #dc2626;
}

.tracking-text {
  font-size: 0.8rem;
  color: #3b82f6;
  margin-left: auto;
}
</style>
