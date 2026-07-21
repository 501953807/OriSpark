<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { negotiationApi } from '@/api/marketplace'
import type { NegotiationItem } from '@/api/marketplace'

const props = defineProps<{ negotiationId: string }>()
const emit = defineEmits<{ updated: [] }>()

const negotiation = ref<NegotiationItem | null>(null)
const loading = ref(true)
const sending = ref(false)
const offerAmount = ref('')
const messageText = ref('')
const error = ref('')

const messages = computed(() => {
  if (!negotiation.value?.message_log) return []
  try {
    return JSON.parse(negotiation.value.message_log)
  } catch { return [] }
})

async function load() {
  try {
    const res = await negotiationApi.getById(props.negotiationId)
    negotiation.value = res.data
  } catch { error.value = '加载议价失败' } finally { loading.value = false }
}

async function sendOffer() {
  const amount = parseFloat(offerAmount.value)
  if (!amount || amount <= 0) { error.value = '请输入有效金额'; return }
  error.value = ''
  sending.value = true
  try {
    await negotiationApi.submitOffer(props.negotiationId, {
      amount_yuan: amount,
      message: messageText.value || undefined,
    })
    offerAmount.value = ''
    messageText.value = ''
    await load()
    emit('updated')
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : '发送报价失败'
  } finally { sending.value = false }
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    pending: '待议价', negotiating: '议价中', agreed: '已同意',
    completed: '已完成', cancelled: '已取消',
  }
  return map[s] || s
}

function statusClass(s: string): string {
  return `status-${s}`
}

load()
</script>

<template>
  <div class="negotiation-chat card">
    <div v-if="loading" class="loading">加载中...</div>
    <template v-else-if="negotiation">
      <div class="chat-header">
        <h3>议价 #{{ negotiation.id.slice(0, 8) }}</h3>
        <span :class="['status-badge', statusClass(negotiation.status)]">{{ statusLabel(negotiation.status) }}</span>
      </div>

      <div class="chat-info">
        <div>初始报价: ¥{{ negotiation.initial_ask_yuan }}</div>
        <div v-if="negotiation.last_offer_yuan">最新报价: ¥{{ negotiation.last_offer_yuan }}</div>
        <div v-if="negotiation.agreed_price_yuan">成交价: ¥{{ negotiation.agreed_price_yuan }}</div>
      </div>

      <!-- Message log -->
      <div class="chat-messages">
        <div v-for="(msg, i) in messages" :key="i" class="message" :class="msg.role">
          <div class="msg-content">{{ msg.content }}</div>
          <div class="msg-time">{{ new Date(msg.created_at).toLocaleString('zh-CN') }}</div>
        </div>
      </div>

      <!-- Offer form -->
      <div v-if="negotiation.status === 'negotiating'" class="offer-form">
        <div class="form-row">
          <label>
            报价（元）
            <input type="number" v-model="offerAmount" placeholder="输入你的报价" />
          </label>
        </div>
        <div class="form-row">
          <label>
            留言
            <textarea v-model="messageText" rows="2" placeholder="可选留言..." />
          </label>
        </div>
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="btn btn-primary" @click="sendOffer" :disabled="sending">
          {{ sending ? '发送中...' : '提交报价' }}
        </button>
      </div>

      <!-- Actions -->
      <div v-if="negotiation.status === 'negotiating'" class="chat-actions">
        <button class="btn btn-success" @click="async () => { await negotiationApi.acceptOffer(props.negotiationId); await load(); emit('updated'); }">
          接受报价
        </button>
        <button class="btn btn-danger" @click="async () => { await negotiationApi.cancel(props.negotiationId); await load(); emit('updated'); }">
          取消议价
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.chat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.chat-info { display: flex; gap: 16px; font-size: 0.85rem; color: var(--muted); margin-bottom: 12px; }
.chat-messages { max-height: 300px; overflow-y: auto; margin-bottom: 16px; }
.message { padding: 8px 12px; margin-bottom: 8px; border-radius: 8px; font-size: 0.9rem; }
.message.seller { background: #fef3c7; margin-right: 20%; }
.message.buyer { background: #dbeafe; margin-left: 20%; }
.msg-time { font-size: 0.75rem; color: var(--muted); margin-top: 4px; }
.offer-form { display: flex; flex-direction: column; gap: 8px; }
.form-row input, .form-row textarea { width: 100%; padding: 8px; border: 1px solid var(--border); border-radius: 6px; }
.error-msg { color: #ef4444; font-size: 0.85rem; }
.chat-actions { display: flex; gap: 8px; margin-top: 12px; }
.status-badge { padding: 4px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 500; }
.status-negotiating { background: #fef3c7; color: #92400e; }
.status-agreed { background: #d1fae5; color: #065f46; }
.status-completed { background: #dbeafe; color: #1e40af; }
.status-cancelled { background: #fee2e2; color: #991b1b; }
.status-pending { background: #f3f4f6; color: #374151; }
</style>
