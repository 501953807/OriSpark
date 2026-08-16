<template>
  <div class="page-supply">
    <h1 class="page-title">供应链管理</h1>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'factories' }]" @click="activeTab = 'factories'">
        工厂管理
      </button>
      <button :class="['tab-btn', { active: activeTab === 'orders' }]" @click="activeTab = 'orders'">
        生产订单
      </button>
      <button :class="['tab-btn', { active: activeTab === 'pod' }]" @click="activeTab = 'pod'">
        POD配置
      </button>
    </div>

    <!-- 工厂管理 -->
    <div v-if="activeTab === 'factories'">
      <div class="filter-bar">
        <select v-model="factoryFilter" class="filter-select">
          <option value="">全部分类</option>
          <option value="clothing">服饰</option>
          <option value="home_decor">家居</option>
          <option value="accessories">配饰</option>
          <option value="stationery">文具</option>
        </select>
        <button class="btn-primary" @click="showFactoryDialog = true">
          + 注册工厂
        </button>
      </div>

      <div v-if="loadingFactories" class="loading-state">加载中...</div>
      <div v-else-if="factoryError" class="error-state">{{ factoryError }}</div>
      <div v-else class="factory-grid">
        <div v-for="factory in factories" :key="factory.id" class="factory-card">
          <div class="factory-header">
            <span class="factory-name">{{ factory.name }}</span>
            <span class="status-badge" :style="{ color: factory.status === 'active' ? 'var(--m-success)' : 'var(--m-grey-500)' }">
              {{ factory.status === 'active' ? '运营中' : '停用' }}
            </span>
          </div>
          <div class="factory-info">
            <div v-if="factory.location" class="info-row">
              <span class="label">📍</span>
              <span>{{ factory.location }}</span>
            </div>
            <div v-if="factory.contact" class="info-row">
              <span class="label">👤</span>
              <span>{{ factory.contact }}</span>
            </div>
            <div v-if="factory.phone" class="info-row">
              <span class="label">📞</span>
              <span>{{ factory.phone }}</span>
            </div>
            <div v-if="factory.rating" class="info-row">
              <span class="label">⭐</span>
              <span>{{ factory.rating }}/5</span>
            </div>
            <div v-if="factory.typical_lead_time_days" class="info-row">
              <span class="label">🕐</span>
              <span>交期 {{ factory.typical_lead_time_days }}天</span>
            </div>
          </div>
          <div class="factory-tags">
            <span v-for="cat in factory.product_categories?.slice(0, 3)" :key="cat" class="tag">
              {{ cat }}
            </span>
          </div>
        </div>
      </div>
      <div v-if="!factories.length && !loadingFactories" class="empty-state">暂无合作工厂</div>
    </div>

    <!-- 生产订单 -->
    <div v-if="activeTab === 'orders'">
      <div class="filter-bar">
        <select v-model="orderFilter" class="filter-select">
          <option value="">全部状态</option>
          <option value="draft">草稿</option>
          <option value="confirmed">已确认</option>
          <option value="in_production">生产中</option>
          <option value="quality_check">质检中</option>
          <option value="shipped">已发货</option>
          <option value="completed">已完成</option>
        </select>
        <button class="btn-primary" @click="showOrderDialog = true">
          + 创建订单
        </button>
      </div>

      <div v-if="loadingOrders" class="loading-state">加载中...</div>
      <div v-else-if="orderError" class="error-state">{{ orderError }}</div>
      <div v-else class="order-list">
        <div v-for="order in filteredOrders" :key="order.id" class="order-card">
          <div class="order-header">
            <div class="order-number">
              <span class="mono">{{ order.order_number }}</span>
              <span class="product-name">{{ order.product_name }}</span>
            </div>
            <span class="status-badge" :style="{ color: ORDER_STATUS_COLOR[order.status] }">
              {{ ORDER_STATUS_LABEL[order.status] }}
            </span>
          </div>
          <div class="order-body">
            <div class="order-meta">
              <span>数量: {{ order.quantity }}</span>
              <span>单价: {{ formatCurrency(order.unit_price) }}</span>
              <span>总额: {{ formatCurrency(order.total_amount) }}</span>
            </div>
            <div v-if="order.expected_date" class="order-date">
              <span>预计交期: {{ formatDate(order.expected_date) }}
                <span v-if="daysUntil(order.expected_date) !== null"
                      :class="['days-remaining', daysUntil(order.expected_date)! <= 3 ? 'urgent' : '']">
                  ({{ daysUntil(order.expected_date) }}天)
                </span>
              </span>
            </div>
            <div v-if="order.shipping_method" class="order-shipping">
              <span>物流: {{ order.shipping_method }}</span>
              <span v-if="order.tracking_number">追踪号: {{ order.tracking_number }}</span>
            </div>
            <div v-if="order.quality_passed !== null" class="order-quality">
              <span :style="{ color: order.quality_passed ? 'var(--m-success)' : 'var(--m-error)' }">
                {{ order.quality_passed ? '✅ 质检通过' : '❌ 质检退回' }}
              </span>
              <span v-if="order.quality_notes">{{ order.quality_notes }}</span>
            </div>
            <div v-if="order.notes" class="order-notes">{{ order.notes }}</div>
          </div>
          <div class="order-actions" v-if="order.status === 'draft'">
            <button class="btn-confirm" @click="handleConfirm(order.id)">确认</button>
          </div>
          <div class="order-actions" v-if="order.status === 'confirmed'">
            <button class="btn-start" @click="handleStart(order.id)">开始生产</button>
          </div>
          <div class="order-actions" v-if="order.status === 'in_production' || order.status === 'quality_check'">
            <button class="btn-ship" @click="showShipDialog(order)">发货</button>
            <button class="btn-inspect-pass" @click="handleInspect(order.id, true)">质检通过</button>
            <button class="btn-inspect-fail" @click="handleInspect(order.id, false)">质检退回</button>
          </div>
          <div class="order-actions" v-if="order.status === 'shipped'">
            <button class="btn-inspect-pass" @click="handleInspect(order.id, true)">确认收货</button>
          </div>
        </div>
      </div>
      <div v-if="!filteredOrders.length && !loadingOrders" class="empty-state">暂无生产订单</div>
    </div>

    <!-- POD配置 -->
    <div v-if="activeTab === 'pod'">
      <div class="filter-bar">
        <button class="btn-primary" @click="showPODDialog = true">
          + 添加平台配置
        </button>
      </div>

      <div v-if="loadingPOD" class="loading-state">加载中...</div>
      <div v-else-if="podError" class="error-state">{{ podError }}</div>
      <div v-else class="pod-list">
        <div v-for="config in podConfigs" :key="config.id" class="pod-card">
          <div class="pod-header">
            <span class="pod-platform">{{ config.platform }}</span>
            <span class="status-badge" :style="{ color: config.is_active ? 'var(--m-success)' : 'var(--m-grey-500)' }">
              {{ config.is_active ? '启用' : '停用' }}
            </span>
          </div>
          <div class="pod-info">
            <span v-if="config.default_store_id" class="info-row">
              店铺ID: {{ config.default_store_id }}
            </span>
            <span class="info-row">
              创建: {{ formatDate(config.created_at) }}
            </span>
          </div>
        </div>
      </div>
      <div v-if="!podConfigs.length && !loadingPOD" class="empty-state">暂无 POD 平台配置</div>
    </div>

    <!-- 注册工厂弹窗 -->
    <FactoryDialog v-if="showFactoryDialog" @close="showFactoryDialog = false" @submitted="onFactorySubmitted" />

    <!-- 创建订单弹窗 -->
    <OrderDialog
      v-if="showOrderDialog"
      :factories="factories"
      @close="showOrderDialog = false"
      @submitted="onOrderSubmitted"
    />

    <!-- 发货弹窗 -->
    <ShipDialog
      v-if="showShipDialogData"
      @close="showShipDialogData = null"
      @submitted="onShipSubmitted"
    />

    <!-- POD配置弹窗 -->
    <PODDialog v-if="showPODDialog" @close="showPODDialog = false" @submitted="onPODSubmitted" />
  </div>
</template>

<script setup lang="ts">
definePageMeta({ layout: 'materio-topnav' })
import { ref, onMounted, computed, watch } from 'vue'
import {
  createFactory, fetchFactories, createOrder, fetchOrders,
  confirmOrder, startProduction, shipOrder, inspectOrder,
  createPODConfig, fetchPODConfigs,
} from '~/composables/useSupplyApi'
import {
  ORDER_STATUS_LABEL, ORDER_STATUS_COLOR, formatDate, formatCurrency, daysUntil,
} from '~/utils/supply'
import FactoryDialog from '~/components/supply/FactoryDialog.vue'
import OrderDialog from '~/components/supply/OrderDialog.vue'
import ShipDialog from '~/components/supply/ShipDialog.vue'
import PODDialog from '~/components/supply/PODDialog.vue'

const auth = useAuthStore()
useHead({ title: '供应链管理 — OriSpark' })

const activeTab = ref('factories')
const factoryFilter = ref('')
const orderFilter = ref('')
const loadingFactories = ref(false)
const loadingOrders = ref(false)
const loadingPOD = ref(false)
const factoryError = ref<string | null>(null)
const orderError = ref<string | null>(null)
const podError = ref<string | null>(null)
const factories = ref<any[]>([])
const orders = ref<any[]>([])
const podConfigs = ref<any[]>([])

const showFactoryDialog = ref(false)
const showOrderDialog = ref(false)
const showShipDialogData = ref<{ id: string } | null>(null)
const showPODDialog = ref(false)

const filteredOrders = computed(() => {
  if (!orderFilter.value) return orders.value
  return orders.value.filter(o => o.status === orderFilter.value)
})

async function loadFactories() {
  loadingFactories.value = true
  factoryError.value = null
  try {
    factories.value = await fetchFactories(factoryFilter.value ? { category: factoryFilter.value } : undefined)
  } catch (e) {
    factoryError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loadingFactories.value = false
  }
}

async function loadOrders() {
  loadingOrders.value = true
  orderError.value = null
  try {
    orders.value = await fetchOrders(orderFilter.value ? { status: orderFilter.value } : undefined)
  } catch (e) {
    orderError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loadingOrders.value = false
  }
}

async function loadPOD() {
  loadingPOD.value = true
  podError.value = null
  try {
    podConfigs.value = await fetchPODConfigs()
  } catch (e) {
    podError.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loadingPOD.value = false
  }
}

async function handleConfirm(orderId: string) {
  try {
    await confirmOrder(orderId)
    await loadOrders()
  } catch (e) {
    orderError.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function handleStart(orderId: string) {
  try {
    await startProduction(orderId)
    await loadOrders()
  } catch (e) {
    orderError.value = e instanceof Error ? e.message : '操作失败'
  }
}

async function handleInspect(orderId: string, passed: boolean) {
  try {
    await inspectOrder(orderId, { passed })
    await loadOrders()
  } catch (e) {
    orderError.value = e instanceof Error ? e.message : '操作失败'
  }
}

function showShipDialog(order: any) {
  showShipDialogData.value = { id: order.id }
}

async function onShipSubmitted() {
  showShipDialogData.value = null
  await loadOrders()
}

async function onFactorySubmitted() {
  showFactoryDialog.value = false
  await loadFactories()
}

async function onOrderSubmitted() {
  showOrderDialog.value = false
  await loadOrders()
}

async function onPODSubmitted() {
  showPODDialog.value = false
  await loadPOD()
}

watch(activeTab, (tab) => {
  if (tab === 'factories') loadFactories()
  else if (tab === 'orders') loadOrders()
  else if (tab === 'pod') loadPOD()
})

watch(factoryFilter, loadFactories)
watch(orderFilter, loadOrders)

onMounted(() => {
  loadFactories()
})
</script>

<style scoped>
.page-supply {
  padding: 0;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--m-on-surface);
  padding: 0 24px;
}

.tabs {
  display: flex;
  gap: 0;
  margin-bottom: 24px;
  padding: 0 24px;
  border-bottom: 1px solid var(--m-border);
}

.tab-btn {
  padding: 12px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  background: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  color: var(--m-grey-500);
  transition: all 0.2s;
  font-family: inherit;
}

.tab-btn.active {
  color: var(--m-primary);
  border-bottom-color: var(--m-primary);
  font-weight: 600;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  align-items: center;
}

.filter-select {
  padding: 8px 14px;
  border: 1px solid var(--m-border);
  border-radius: 6px;
  font-size: 14px;
  background: #FFFFFF;
  color: var(--m-on-surface);
  font-family: inherit;
}

.btn-primary {
  padding: 8px 20px;
  background: var(--m-primary);
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  font-family: inherit;
}

.btn-primary:hover {
  background: rgb(110, 57, 220);
}

/* 工厂网格 */
.factory-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.factory-card {
  background: #FFFFFF;
  border-radius: 6px;
  border: none;
  box-shadow: var(--m-shadow-md);
  padding: 20px;
  transition: box-shadow 0.2s;
}

.factory-card:hover {
  box-shadow: rgba(46, 38, 61, 0.2) 0px 4px 10px 0px;
}

.factory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.factory-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--m-on-surface);
}

.factory-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.info-row {
  font-size: 13px;
  color: rgba(46, 38, 61, 0.6);
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-row .label {
  font-size: 14px;
}

.factory-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(140, 87, 255, 0.1);
  color: var(--m-primary);
  border-radius: 100px;
  font-weight: 500;
}

/* 订单列表 */
.order-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-card {
  background: #FFFFFF;
  border-radius: 6px;
  border: none;
  box-shadow: var(--m-shadow-md);
  padding: 16px 20px;
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.order-number {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.mono {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--m-grey-500);
}

.product-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--m-on-surface);
}

.order-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.order-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: rgba(46, 38, 61, 0.6);
}

.order-date {
  font-size: 13px;
  color: var(--m-grey-500);
}

.order-shipping {
  font-size: 13px;
  color: var(--m-primary);
}

.order-quality {
  font-size: 13px;
  display: flex;
  gap: 12px;
}

.order-notes {
  font-size: 14px;
  color: var(--m-on-surface);
  padding: 8px 12px;
  background: var(--m-grey-100);
  border-radius: 6px;
}

.days-remaining {
  font-size: 12px;
  font-weight: 600;
}

.days-remaining.urgent {
  color: var(--m-error);
}

.order-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(46, 38, 61, 0.1);
}

.btn-confirm, .btn-start, .btn-ship, .btn-inspect-pass, .btn-inspect-fail {
  padding: 6px 16px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
}

.btn-confirm {
  background: var(--m-success);
  color: #fff;
}

.btn-confirm:hover {
  background: var(--m-success);
}

.btn-start {
  background: var(--m-primary);
  color: #fff;
}

.btn-start:hover {
  background: var(--m-primary-dark);
}

.btn-ship {
  background: var(--m-primary);
  color: #fff;
}

.btn-ship:hover {
  background: rgb(110, 57, 220);
}

.btn-inspect-pass {
  background: var(--m-success);
  color: #fff;
}

.btn-inspect-pass:hover {
  background: var(--m-success);
}

.btn-inspect-fail {
  background: transparent;
  color: var(--m-error);
  border: 1px solid var(--m-error);
}

.btn-inspect-fail:hover {
  background: rgba(255, 76, 81, 0.08);
}

/* POD 列表 */
.pod-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pod-card {
  background: #FFFFFF;
  border-radius: 6px;
  border: none;
  box-shadow: var(--m-shadow-md);
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pod-platform {
  font-size: 16px;
  font-weight: 600;
  color: var(--m-primary);
  text-transform: uppercase;
}

.pod-info {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: var(--m-grey-500);
}

/* 通用状态 */
.loading-state,
.error-state,
.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--m-grey-500);
}

.error-state {
  color: var(--m-error);
}

.status-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 100px;
  background: rgba(46, 38, 61, 0.06);
  color: var(--m-grey-700);
}
</style>
