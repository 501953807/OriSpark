<template>
  <div class="negotiation-view">
    <!-- Error toast -->
    <div v-if="errorMsg" class="error-toast" @click="errorMsg = ''">{{ errorMsg }}</div>

    <div class="card">
      <div class="split-layout">
        <div class="neg-list-panel">
          <div class="panel-header">
            <h3>协商列表</h3>
            <button class="btn btn-sm btn-secondary" @click="showCreate = true">+ 新建</button>
          </div>
          <select class="form-select" v-model="statusFilter" style="width: 100%; margin-bottom: 12px">
            <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
          </select>
          <div v-if="loading" class="empty-state">加载中...</div>
          <div v-else-if="filteredNegs.length === 0" class="empty-state">暂无议价记录</div>
          <div v-else class="neg-items">
            <div
              v-for="neg in filteredNegs"
              :key="neg.id"
              :class="['neg-item', { selected: neg.id === selectedId }]"
              @click="selectedId = neg.id"
            >
              <div class="neg-title">{{ descPreview(neg) }}</div>
              <div class="neg-meta">
                <span class="badge" :class="negBadgeClass(neg.status)">{{ negStatusLabel(neg.status) }}</span>
                <span v-if="neg.current_offer_yuan" class="neg-price">¥{{ neg.current_offer_yuan }}</span>
                <span class="neg-time">{{ formatDate(neg.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="neg-detail-panel" v-if="selectedNeg">
          <div class="detail-header">
            <div class="detail-status">
              <span class="badge" :class="negBadgeClass(selectedNeg.status)">{{ negStatusLabel(selectedNeg.status) }}</span>
              <span class="detail-id">ID: {{ selectedNeg.id.slice(0,8) }}...</span>
            </div>
            <div class="detail-actions">
              <button v-if="selectedNeg.status === 'pending' || selectedNeg.status === 'negotiating'"
                class="btn btn-sm btn-success" @click.stop="handleAccept(selectedNeg)">接受报价</button>
              <button v-if="selectedNeg.status === 'agreed'"
                class="btn btn-sm btn-primary" @click.stop="handleComplete(selectedNeg)">确认成交</button>
              <button v-if="selectedNeg.status !== 'completed' && selectedNeg.status !== 'cancelled'"
                class="btn btn-sm btn-danger" @click.stop="handleCancel(selectedNeg)">取消</button>
            </div>
          </div>
          <ChatPanel :negotiation="selectedNeg" @reply="handleReply" />
          <OfferTimeline :negotiation="selectedNeg" />
        </div>
        <EmptyState v-else icon="💬" title="选择一条协商" description="从左侧列表中选择或创建新的议价协商。" />
      </div>
    </div>

    <!-- Create modal -->
    <div class="modal-overlay" v-if="showCreate">
      <div class="modal-card">
        <h3 style="margin: 0 0 16px">新建议价协商</h3>
        <div class="form-group">
          <label class="form-label">买方 ID</label>
          <input class="form-input" v-model="createForm.buyer_id" placeholder="买方用户 ID" />
        </div>
        <div class="form-group">
          <label class="form-label">卖方 ID</label>
          <input class="form-input" v-model="createForm.seller_id" placeholder="卖方用户 ID" />
        </div>
        <div class="form-group">
          <label class="form-label">初始报价 (元)</label>
          <input class="form-input" type="number" v-model.number="createForm.initial_price_yuan" placeholder="可选" min="0" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showCreate = false">取消</button>
          <button class="btn btn-primary" @click="handleCreate">创建</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { TradeNegotiation } from '@/types/negotiation'
import { negotiationApi } from '@/api/negotiation'
import ChatPanel from '@/components/negotiation/ChatPanel.vue'
import OfferTimeline from '@/components/negotiation/OfferTimeline.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const negs = ref<TradeNegotiation[]>([])
const loading = ref(false)
const selectedId = ref('')
const statusFilter = ref('')
const showCreate = ref(false)
const errorMsg = ref('')

const createForm = ref({ buyer_id: '', seller_id: '', initial_price_yuan: null as number | null })

const statusOptions = [
  { label: '全部', value: '' },
  { label: '待回复', value: 'pending' },
  { label: '谈判中', value: 'negotiating' },
  { label: '已同意', value: 'agreed' },
  { label: '已完成', value: 'completed' },
  { label: '已取消', value: 'cancelled' },
]

const filteredNegs = computed(() => {
  if (!statusFilter.value) return negs.value
  return negs.value.filter(n => n.status === statusFilter.value)
})

const selectedNeg = computed(() => negs.value.find(n => n.id === selectedId.value) || null)

async function load() {
  loading.value = true
  try {
    const resp = await negotiationApi.list()
    negs.value = (resp.data?.data ?? []) as TradeNegotiation[]
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '加载失败'
  } finally { loading.value = false }
}

async function handleCreate() {
  if (!createForm.value.buyer_id || !createForm.value.seller_id) return
  try {
    const result = await negotiationApi.create({
      ...createForm.value,
      initial_price_yuan: createForm.value.initial_price_yuan ?? undefined,
    })
    const nego = result.data?.data as TradeNegotiation
    negs.value.unshift(nego)
    selectedId.value = nego.id
    showCreate.value = false
    createForm.value = { buyer_id: '', seller_id: '', initial_price_yuan: null }
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '创建失败'
  }
}

async function handleReply(neg: TradeNegotiation, offer: number, msg: string) {
  try {
    const result = await negotiationApi.submitOffer(neg.id, { amount_yuan: offer, message: msg })
    const updated = result.data?.data as TradeNegotiation
    const idx = negs.value.findIndex(n => n.id === neg.id)
    if (idx >= 0) negs.value[idx] = updated
    if (selectedId.value === neg.id) {
      // force re-render of detail panel
      selectedId.value = ''
      setTimeout(() => { selectedId.value = neg.id }, 50)
    }
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '报价发送失败'
  }
}

async function handleAccept(neg: TradeNegotiation) {
  try {
    const result = await negotiationApi.acceptOffer(neg.id)
    const updated = result.data?.data as TradeNegotiation
    const idx = negs.value.findIndex(n => n.id === neg.id)
    if (idx >= 0) negs.value[idx] = updated
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '接受报价失败'
  }
}

async function handleComplete(neg: TradeNegotiation) {
  try {
    const result = await negotiationApi.complete(neg.id)
    const updated = result.data?.data as TradeNegotiation
    const idx = negs.value.findIndex(n => n.id === neg.id)
    if (idx >= 0) negs.value[idx] = updated
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '确认成交失败'
  }
}

async function handleCancel(neg: TradeNegotiation) {
  try {
    const result = await negotiationApi.cancel(neg.id, '用户取消')
    const updated = result.data?.data as TradeNegotiation
    const idx = negs.value.findIndex(n => n.id === neg.id)
    if (idx >= 0) negs.value[idx] = updated
    selectedId.value = ''
  } catch (e: any) {
    errorMsg.value = e.response?.data?.message || '取消失败'
  }
}

function descPreview(n: TradeNegotiation): string {
  return n.description?.slice(0, 40) || `${n.buyer_id.slice(0,6)} ↔ ${n.seller_id.slice(0,6)}`
}

function negBadgeClass(s: string): string {
  const map: Record<string, string> = {
    pending: 'badge-warning', negotiating: 'badge-warning', agreed: 'badge-success', completed: 'badge-success', cancelled: 'badge-danger',
  }
  return map[s] || 'badge-default'
}

function negStatusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '待回复', negotiating: '谈判中', agreed: '已同意', completed: '已完成', cancelled: '已取消',
  }
  return map[s] || s
}

function formatDate(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return `${d.getMonth()+1}/${d.getDate()}`
}

onMounted(load)
</script>

<style scoped>
.negotiation-view { display: flex; flex-direction: column; gap: 16px; }

.split-layout { display: flex; min-height: 400px; }
.neg-list-panel { flex: 0 0 30%; padding: 8px; overflow-y: auto; border-right: 1px solid var(--m-border); max-height: calc(100vh - 200px); }
.neg-detail-panel { flex: 1; padding: 16px; display: flex; flex-direction: column; gap: 16px; }

.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.panel-header h3 { margin: 0; font-size: 0.92rem; font-weight: 600; }

.neg-items { display: flex; flex-direction: column; gap: 6px; }

.neg-item {
  padding: 12px; background: var(--m-bg-subtle); border: 1px solid var(--m-border); border-radius: var(--m-radius-sm);
  cursor: pointer; transition: background 0.15s, border-color 0.15s;
}
.neg-item:hover { background: var(--m-surface); }
.neg-item.selected { border-color: var(--m-primary); background: var(--m-surface); }

.neg-title { font-size: 0.88rem; font-weight: 600; color: var(--m-on-surface); margin-bottom: 4px; }

.neg-meta { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: var(--m-grey-500); }
.neg-price { color: #ea580c; font-weight: 600; }
.neg-time { margin-left: auto; }

.empty-state { padding: 32px; text-align: center; color: var(--m-grey-500); }

.error-toast {
  position: fixed; top: 20px; right: 20px; z-index: 9999;
  padding: 12px 20px; background: var(--red); color: #fff;
  border-radius: var(--m-radius-sm); font-size: 0.85rem; cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,.15); animation: slideIn .2s ease;
}
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

.detail-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 12px; background: var(--m-bg-subtle); border-radius: var(--m-radius-sm);
}
.detail-status { display: flex; align-items: center; gap: 10px; }
.detail-id { font-size: 0.75rem; color: var(--m-grey-500); font-family: monospace; }
.detail-actions { display: flex; gap: 8px; }
</style>
