<template>
  <div class="chat-panel">
    <div class="chat-messages">
      <div v-for="(msg, i) in messages" :key="i" :class="['msg', msg.direction]">
        <div class="msg-bubble">
          <div class="msg-sender">{{ msg.sender }}</div>
          <div class="msg-text">{{ msg.text }}</div>
          <div class="msg-price" v-if="msg.price">¥{{ msg.price }}</div>
          <div class="msg-time">{{ msg.time }}</div>
        </div>
      </div>
    </div>
    <div class="chat-input">
      <n-input v-model:value="replyText" placeholder="输入回复..." />
      <n-input-number v-model:value="replyOffer" placeholder="报价 (元)" style="width: 140px;" />
      <n-button type="primary" @click="handleSend">发送</n-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { NInput, NInputNumber, NButton } from 'naive-ui'
import type { TradeNegotiation } from '@/types/negotiation'

const props = defineProps<{ negotiation: TradeNegotiation }>()
const emit = defineEmits<{ reply: [neg: TradeNegotiation, offer: number, message: string] }>()

const replyText = ref('')
const replyOffer = ref<number | null>(null)

const messages = computed(() => {
  const msgs: Array<{ sender: string; text: string; price?: number; time: string; direction: 'incoming' | 'outgoing' }> = []
  if (props.negotiation.initial_price_yuan) {
    msgs.push({ sender: '系统', text: `初始报价`, price: props.negotiation.initial_price_yuan, time: formatDate(props.negotiation.created_at), direction: 'incoming' })
  }
  if (props.negotiation.current_offer_yuan && props.negotiation.current_offer_yuan !== props.negotiation.initial_price_yuan) {
    msgs.push({ sender: '当前报价', text: '', price: props.negotiation.current_offer_yuan, time: formatDate(props.negotiation.updated_at), direction: 'incoming' })
  }
  return msgs
})

function formatDate(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

function handleSend() {
  if (!replyOffer.value || replyOffer.value <= 0) return
  emit('reply', props.negotiation, replyOffer.value, replyText.value)
  replyText.value = ''
  replyOffer.value = null
}
</script>

<style scoped>
.chat-panel { display: flex; flex-direction: column; gap: 12px; }

.chat-messages {
  max-height: 300px; overflow-y: auto;
  padding: 12px; background: var(--bg); border-radius: var(--radius);
  display: flex; flex-direction: column; gap: 8px;
}

.msg { display: flex; }
.msg.outgoing { justify-content: flex-end; }

.msg-bubble {
  max-width: 80%; padding: 8px 12px;
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
}

.msg.outgoing .msg-bubble { background: var(--accent); color: #fff; border-color: var(--accent); }

.msg-sender { font-size: 0.75rem; font-weight: 600; margin-bottom: 2px; }
.msg-text { font-size: 0.85rem; }
.msg-price { font-size: 1rem; font-weight: 700; color: #ea580c; }
.msg-time { font-size: 0.7rem; opacity: 0.6; margin-top: 4px; }

.chat-input { display: flex; gap: 8px; align-items: center; }
</style>
