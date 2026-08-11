<template>
  <div class="negotiation-view">
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
          <label class="form-label">买方ID</label>
          <input class="form-input" v-model="createForm.buyer_id" placeholder="买方用户 ID" />
        </div>
        <div class="form-group">
          <label class="form-label">卖方ID</label>
          <input class="form-input" v-model="createForm.seller_id" placeholder="卖方用户 ID" />
        </div>
        <div class="form-group">
          <label class="form-label">初始报价</label>
          <input class="form-input" type="number" v-model.number="createForm.initial_price_yuan" placeholder="金额 (元)" />
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
    negs.value = resp.data.data || []
  } catch { /* silent */ } finally { loading.value = false }
}

async function handleCreate() {
  if (!createForm.value.buyer_id || !createForm.value.seller_id) return
  try {
    const result = await negotiationApi.create({
      ...createForm.value,
      initial_price_yuan: createForm.value.initial_price_yuan ?? undefined,
    })
    negs.value.unshift(result.data.data)
    selectedId.value = result.data.data.id
    showCreate.value = false
  } catch { /* silent */ }
}

async function handleReply(_pr: TradeNegotiation, _offer: number, _msg: string) {
  // Placeholder — actual reply handler wired through ChatPanel events
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
.neg-list-panel { flex: 0 0 30%; padding: 8px; overflow-y: auto; border-right: 1px solid var(--border); max-height: calc(100vh - 200px); }
.neg-detail-panel { flex: 1; padding: 16px; display: flex; flex-direction: column; gap: 16px; }

.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.panel-header h3 { margin: 0; font-size: 0.92rem; font-weight: 600; }

.neg-items { display: flex; flex-direction: column; gap: 6px; }

.neg-item {
  padding: 12px; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius);
  cursor: pointer; transition: background 0.15s, border-color 0.15s;
}
.neg-item:hover { background: var(--surface); }
.neg-item.selected { border-color: var(--accent); background: var(--surface); }

.neg-title { font-size: 0.88rem; font-weight: 600; color: var(--fg); margin-bottom: 4px; }

.neg-meta { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: var(--muted); }
.neg-price { color: #ea580c; font-weight: 600; }
.neg-time { margin-left: auto; }

.empty-state { padding: 32px; text-align: center; color: var(--muted); }
</style>
