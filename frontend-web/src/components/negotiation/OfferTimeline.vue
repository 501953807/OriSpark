<template>
  <div class="offer-timeline">
    <h4 class="timeline-title">报价演变</h4>
    <div class="timeline">
      <div v-if="negotiation.initial_price_yuan" class="timeline-item">
        <div class="timeline-dot initial"></div>
        <div class="timeline-content">
          <div class="timeline-label">初始报价</div>
          <div class="timeline-value">¥{{ negotiation.initial_price_yuan }}</div>
          <div class="timeline-time">{{ formatDate(negotiation.created_at) }}</div>
        </div>
      </div>
      <div v-if="negotiation.current_offer_yuan && negotiation.current_offer_yuan !== negotiation.initial_price_yuan" class="timeline-item">
        <div class="timeline-dot current"></div>
        <div class="timeline-content">
          <div class="timeline-label">当前报价</div>
          <div class="timeline-value">¥{{ negotiation.current_offer_yuan }}</div>
          <div class="timeline-time">{{ formatDate(negotiation.updated_at) }}</div>
        </div>
      </div>
      <div v-if="negotiation.final_price_yuan" class="timeline-item agreed">
        <div class="timeline-dot agreed"></div>
        <div class="timeline-content">
          <div class="timeline-label">最终成交价</div>
          <div class="timeline-value">¥{{ negotiation.final_price_yuan }}</div>
          <div class="timeline-time">{{ formatDate(negotiation.updated_at) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TradeNegotiation } from '@/types/negotiation'

defineProps<{ negotiation: TradeNegotiation }>()

function formatDate(iso?: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return `${d.getFullYear()}-${d.getMonth()+1}-${d.getDate()}`
}
</script>

<style scoped>
.offer-timeline { padding: 8px 0; }
.timeline-title { margin: 0 0 12px; font-size: 0.88rem; font-weight: 600; }

.timeline { display: flex; flex-direction: column; gap: 12px; padding-left: 16px; border-left: 2px solid var(--border); }

.timeline-item { position: relative; padding-left: 16px; }

.timeline-dot {
  position: absolute; left: -7px; top: 2px;
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--border);
}
.timeline-dot.initial { background: #2563eb; }
.timeline-dot.current { background: #ea580c; }
.timeline-dot.agreed { background: #16a34a; }

.timeline-label { font-size: 0.78rem; color: var(--muted); }
.timeline-value { font-size: 1.1rem; font-weight: 700; color: var(--fg); }
.timeline-time { font-size: 0.72rem; color: var(--muted); }
</style>
