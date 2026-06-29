<!-- OrderPanel — 订单管理

Shows orders linked to a listing. Displays status, amounts, and actions.
-->
<template>
  <div class="order-panel">
    <div class="panel-header">
      <h4>📋 相关订单</h4>
      <button class="btn-add" @click="showNewOrder = true">+ 创建订单</button>
    </div>

    <div v-if="loading" class="loading-state">加载中...</div>

    <div v-else-if="!orders.length" class="empty-state">
      <span class="empty-icon">📋</span>
      <p>暂无相关订单</p>
    </div>

    <div v-else class="order-list">
      <div v-for="o in orders" :key="o.id" class="order-item">
        <div class="order-info">
          <div class="order-number">{{ o.order_number }}</div>
          <div class="order-product">{{ o.product_name }}</div>
          <div class="order-meta">
            <span class="order-amount">¥{{ o.total_amount }}</span>
            <span :class="['order-status', orderStatusClass(o.status)]">
              {{ statusLabel(o.status) }}
            </span>
          </div>
        </div>
        <div class="order-actions">
          <button class="ext-btn" title="查看详情" @click="viewOrder(o)">👁</button>
        </div>
      </div>
    </div>

    <!-- New order dialog -->
    <div v-if="showNewOrder" class="modal-overlay" @click.self="showNewOrder = false">
      <div class="modal">
        <h4>创建订单</h4>
        <div class="form-group">
          <label>产品名称</label>
          <input v-model="form.product_name" class="form-input" />
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>数量</label>
            <input v-model.number="form.quantity" type="number" class="form-input" />
          </div>
          <div class="form-group">
            <label>单价</label>
            <input v-model.number="form.unit_price" type="number" class="form-input" />
          </div>
        </div>
        <div class="form-group">
          <label>订单类型</label>
          <select v-model="form.order_type" class="form-select">
            <option value="pod">POD 订单</option>
            <option value="crowdfunding">众筹订单</option>
            <option value="custom_mfg">定制制造</option>
          </select>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" @click="showNewOrder = false">取消</button>
          <button class="btn-save" @click="saveOrder" :disabled="saving">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { supplyApi } from '@/api/supply'

interface Props {
  listingId: string
}

const props = defineProps<Props>()

interface Ord {
  id: string
  order_number: string
  product_name: string
  total_amount: number
  status: string
  quantity?: number
  unit_price?: number
}

const orders = ref<Ord[]>([])
const loading = ref(false)
const saving = ref(false)
const showNewOrder = ref(false)

const form = ref({
  product_name: '', quantity: 1, unit_price: 0, order_type: 'pod',
})

function orderStatusClass(s: string): string {
  const map: Record<string, string> = {
    draft: 'status-draft', confirmed: 'status-confirmed',
    shipped: 'status-shipped', delivered: 'status-delivered', cancelled: 'status-cancelled',
  }
  return map[s] || ''
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    draft: '草稿', confirmed: '已确认', shipped: '已发货',
    delivered: '已送达', cancelled: '已取消', producing: '制作中',
  }
  return map[s] || s
}

async function loadOrders() {
  loading.value = true
  try {
    const { data } = await supplyApi.orders()
    orders.value = (data as Ord[]).filter((o: any) => o.listing_id === props.listingId)
  } catch {
    orders.value = []
  } finally {
    loading.value = false
  }
}

function viewOrder(o: Ord) {
  alert(`订单详情: ${o.order_number}`)
}

async function saveOrder() {
  saving.value = true
  try {
    const total = form.value.quantity * form.value.unit_price
    await supplyApi.createOrder({
      ...form.value,
      total_amount: total,
      listing_id: props.listingId,
      status: 'draft',
    })
    showNewOrder.value = false
    await loadOrders()
  } catch {
    // Error toast
  } finally {
    saving.value = false
  }
}

onMounted(loadOrders)
</script>

<style scoped>
.order-panel { padding: 0 4px; }

.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}
.panel-header h4 { margin: 0; font-size: .9rem; }

.btn-add {
  background: var(--accent); color: #fff; border: none;
  padding: 4px 12px; border-radius: var(--radius-sm); font-size: .78rem; cursor: pointer;
}

.loading-state, .empty-state {
  text-align: center; padding: 32px 0; color: var(--muted);
}
.empty-icon { font-size: 2rem; display: block; margin-bottom: 8px; }

.order-list { display: flex; flex-direction: column; gap: 8px; }

.order-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); background: var(--surface);
}

.order-number { font-weight: 700; font-size: .85rem; }
.order-product { font-size: .72rem; color: var(--muted); margin-top: 2px; }

.order-meta { display: flex; gap: 8px; align-items: center; margin-top: 4px; }

.order-amount { font-weight: 800; color: var(--accent); font-size: .92rem; }

.order-status {
  padding: 1px 8px; border-radius: 100px; font-size: .65rem; font-weight: 600;
}

.order-status.status-draft { background: oklch(75% 0.08 80 / .15); color: oklch(65% 0.1 80); }
.order-status.status-confirmed { background: oklch(56% 0.12 140 / .15); color: oklch(56% 0.12 140); }
.order-status.status-shipped { background: oklch(65% 0.1 270 / .15); color: oklch(55% 0.15 270); }
.order-status.status-delivered { background: oklch(56% 0.12 140 / .2); color: oklch(46% 0.14 140); }
.order-status.status-cancelled { background: oklch(56% 0.12 20 / .15); color: oklch(56% 0.12 20); }

.order-actions { display: flex; gap: 4px; }
.ext-btn {
  background: none; border: 1px solid var(--border); border-radius: var(--radius-sm);
  padding: 4px 8px; cursor: pointer; font-size: .82rem;
}

/* Modal */
.modal-overlay {
  position: fixed; inset: 0;
  background: oklch(20% 0.02 180 / .5);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}

.modal {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: 24px;
  width: 420px; max-width: 90vw;
}

.modal h4 { margin: 0 0 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: .78rem; margin-bottom: 4px; color: var(--muted); }

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.form-select, .form-input {
  width: 100%; padding: 6px 10px; border: 1px solid var(--border);
  border-radius: var(--radius-sm); font-size: .85rem; background: var(--surface);
}

.form-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; }
.btn-cancel {
  padding: 6px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  background: none; cursor: pointer; font-size: .82rem;
}
.btn-save {
  padding: 6px 16px; border: none; border-radius: var(--radius-sm);
  background: var(--accent); color: #fff; cursor: pointer; font-size: .82rem;
}
</style>
