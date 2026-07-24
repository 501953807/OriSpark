<template>
  <div class="negotiation-view">
    <n-card title="💬 议价协商">
      <n-split direction="horizontal" :default-size="0.35" :min="0.25" :max="0.5">
        <template #1>
          <div class="neg-list-panel">
            <div class="panel-header">
              <h3>协商列表</h3>
              <n-button size="small" @click="showCreate = true">+ 新建</n-button>
            </div>
            <n-select v-model:value="statusFilter" :options="statusOptions" placeholder="按状态筛选" style="width: 100%; margin-bottom: 12px;" />
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
                  <n-tag size="small" :type="negStatusType(neg.status)">
                    {{ negStatusLabel(neg.status) }}
                  </n-tag>
                  <span v-if="neg.current_offer_yuan" class="neg-price">¥{{ neg.current_offer_yuan }}</span>
                  <span class="neg-time">{{ formatDate(neg.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
        <template #2>
          <div v-if="selectedNeg" class="neg-detail-panel">
            <ChatPanel :negotiation="selectedNeg" @reply="handleReply" />
            <OfferTimeline :negotiation="selectedNeg" />
          </div>
          <EmptyState v-else icon="💬" title="选择一条协商" description="从左侧列表中选择或创建新的议价协商。" />
        </template>
      </n-split>
    </n-card>

    <!-- Create modal -->
    <n-modal v-model:show="showCreate" preset="dialog" title="新建议价协商">
      <n-form :model="createForm" label-width="80">
        <n-form-item label="买方ID">
          <n-input v-model:value="createForm.buyer_id" placeholder="买方用户 ID" />
        </n-form-item>
        <n-form-item label="卖方ID">
          <n-input v-model:value="createForm.seller_id" placeholder="卖方用户 ID" />
        </n-form-item>
        <n-form-item label="初始报价">
          <n-input-number v-model:value="createForm.initial_price_yuan" placeholder="金额 (元)" />
        </n-form-item>
      </n-form>
      <template #action>
        <n-button @click="showCreate = false">取消</n-button>
        <n-button type="primary" @click="handleCreate">创建</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { NCard, NSplit, NButton, NModal, NForm, NFormItem, NInput, NInputNumber, NSelect, NTag } from 'naive-ui'
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

const createForm = ref({ buyer_id: '', seller_id: '', initial_price_yuan: undefined as number | null })

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
    const result = await negotiationApi.create(createForm.value)
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

function negStatusType(s: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  const map: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
    pending: 'warning', negotiating: 'warning', agreed: 'success', completed: 'success', cancelled: 'error',
  }
  return map[s] || 'default'
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

.neg-list-panel { padding: 8px; overflow-y: auto; max-height: calc(100vh - 200px); }

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

.neg-detail-panel { padding: 16px; display: flex; flex-direction: column; gap: 16px; }

.empty-state { padding: 32px; text-align: center; color: var(--muted); }
</style>
