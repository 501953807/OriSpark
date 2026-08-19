<!-- OriSpark Orders Page — 我的订单 -->
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

definePageMeta({ layout: 'materio-topnav' })

const loading = ref(false)
const activeTab = ref('all')
const statusFilter = ref('')

const orders = ref([
  {
    id: 'ORD2026001',
    type: 'contract',
    title: '插画授权合约 #001',
    creator: '李画家',
    amount: 12000,
    status: 'active',
    created_at: '2026-08-10',
    deadline: '2026-09-10',
    progress: 60,
  },
  {
    id: 'ORD2026002',
    type: 'contract',
    title: '摄影图库采购 #007',
    creator: '张摄影师',
    amount: 28000,
    status: 'pending',
    created_at: '2026-08-15',
    deadline: '2026-08-30',
    progress: 0,
  },
  {
    id: 'ORD2026003',
    type: 'production',
    title: 'T恤生产订单 #042',
    creator: '王工坊',
    amount: 8500,
    status: 'shipping',
    created_at: '2026-07-20',
    deadline: '2026-08-20',
    progress: 85,
    tracking: 'SF1234567890',
  },
  {
    id: 'ORD2026004',
    type: 'delivery',
    title: '艺术品配送 #108',
    creator: '赵艺术家',
    amount: 5600,
    status: 'completed',
    created_at: '2026-06-15',
    deadline: '2026-07-01',
    progress: 100,
    delivered_at: '2026-07-01',
  },
  {
    id: 'ORD2026005',
    type: 'contract',
    title: '音乐版权授权 #019',
    creator: '刘音乐人',
    amount: 15000,
    status: 'cancelled',
    created_at: '2026-05-20',
    deadline: '2026-06-20',
    progress: 0,
    cancelled_at: '2026-06-18',
  },
])

const filteredOrders = computed(() => {
  let result = orders.value
  if (activeTab.value !== 'all') {
    result = result.filter(o => o.type === activeTab.value)
  }
  if (statusFilter.value) {
    result = result.filter(o => o.status === statusFilter.value)
  }
  return result
})

const stats = computed(() => ({
  total: orders.value.length,
  active: orders.value.filter(o => o.status === 'active').length,
  pending: orders.value.filter(o => o.status === 'pending').length,
  completed: orders.value.filter(o => o.status === 'completed').length,
  total_amount: orders.value.reduce((sum, o) => sum + o.amount, 0),
}))

const statusMap = {
  active: { label: '进行中', class: 'status-active' },
  pending: { label: '待处理', class: 'status-pending' },
  shipping: { label: '配送中', class: 'status-shipping' },
  completed: { label: '已完成', class: 'status-completed' },
  cancelled: { label: '已取消', class: 'status-cancelled' },
}

const typeMap = {
  contract: '合约认购',
  production: '生产订单',
  delivery: '配送记录',
}
</script>

<template>
  <div class="page-orders">
    <!-- Header -->
    <div class="orders-header">
      <h1 class="page-title">我的订单</h1>
      <div class="header-actions">
        <select v-model="statusFilter" class="filter-select">
          <option value="">全部状态</option>
          <option value="active">进行中</option>
          <option value="pending">待处理</option>
          <option value="shipping">配送中</option>
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
      <button :class="['tab-btn', { active: activeTab === 'contract' }]" @click="activeTab = 'contract'">合约认购</button>
      <button :class="['tab-btn', { active: activeTab === 'production' }]" @click="activeTab = 'production'">生产订单</button>
      <button :class="['tab-btn', { active: activeTab === 'delivery' }]" @click="activeTab = 'delivery'">配送记录</button>
    </div>

    <!-- Orders List -->
    <div class="orders-list">
      <div v-if="filteredOrders.length === 0" class="empty-state">
        暂无订单
      </div>
      <div v-for="order in filteredOrders" :key="order.id" class="order-card">
        <div class="order-header">
          <div class="order-meta">
            <span class="order-type">{{ typeMap[order.type] }}</span>
            <span class="order-id">{{ order.id }}</span>
          </div>
          <span :class="['status-badge', statusMap[order.status]?.class]">
            {{ statusMap[order.status]?.label }}
          </span>
        </div>

        <div class="order-body">
          <div class="order-info">
            <h3 class="order-title">{{ order.title }}</h3>
            <p class="order-creator">创作者: {{ order.creator }}</p>
            <p class="order-amount">¥{{ order.amount.toLocaleString() }}</p>
          </div>
          <div class="order-dates">
            <div class="date-item">
              <span class="date-label">创建</span>
              <span class="date-value">{{ order.created_at }}</span>
            </div>
            <div class="date-item">
              <span class="date-label">截止</span>
              <span class="date-value">{{ order.deadline }}</span>
            </div>
          </div>
        </div>

        <!-- Progress Bar (for active/shipping orders) -->
        <div v-if="order.progress > 0" class="progress-section">
          <div class="progress-header">
            <span class="progress-label">进度</span>
            <span class="progress-value">{{ order.progress }}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: order.progress + '%' }"></div>
          </div>
          <div v-if="order.tracking" class="tracking-info">
            <span class="tracking-label">物流单号:</span>
            <span class="tracking-value">{{ order.tracking }}</span>
          </div>
        </div>

        <!-- Actions -->
        <div class="order-actions">
          <button class="btn-secondary" @click="$router.push('/contracts')">查看详情</button>
          <button v-if="order.status === 'pending'" class="btn-primary" @click="$router.push(`/contracts/${order.id}`)">立即认购</button>
          <button v-if="order.status === 'shipping'" class="btn-secondary" @click="$router.push(`/orders/${order.id}/track`)">跟踪物流</button>
          <button v-if="order.status === 'active'" class="btn-outline" @click="$router.push(`/contracts/${order.id}`)">管理合约</button>
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

.order-creator {
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

.progress-section {
  margin-bottom: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.progress-label {
  font-size: 0.8rem;
  color: #6b7280;
}

.progress-value {
  font-size: 0.8rem;
  color: #7c3aed;
  font-weight: 600;
}

.progress-bar {
  height: 6px;
  background: #e5e7eb;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #7c3aed, #3b82f6);
  border-radius: 3px;
  transition: width 0.3s;
}

.tracking-info {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: #6b7280;
}

.tracking-label {
  margin-right: 0.5rem;
}

.tracking-value {
  font-family: monospace;
  color: #3b82f6;
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
</style>
